"""Estimate the commissioning year of ships that have no date, and flag every estimate.

Never overwrites `commissioned`; writes ship.service_year (+ service_year_estimated = 1, a basis and a confidence).
Methods, in order of reliability:
  interpolated   (high)   between the two nearest dated sisters in hull-number/table order
  extrapolated   (medium) beyond the dated range, using the class's typical gap between sisters (capped)
  class-start    (low)    no dated sisters: class first-in-service year (+ typical spacing by order)
  built-range    (low)    no dated sisters and no class year: start of the infobox build range
"""
import re, statistics

TODAY_YEAR = 2026


def _order_key(row):
    sid, pen = row["id"], row["pennant"] or ""
    nums = re.findall(r"\d+", pen)
    return (int(nums[-1]) if nums else 10 ** 9, sid)


def run(con):
    con.row_factory = None
    cols = ["id", "class_id", "pennant", "commissioned", "status"]
    classes = con.execute("select id, service_start, service_raw from ship_class").fetchall()
    n_est = {"high": 0, "medium": 0, "low": 0, "none": 0}
    for cid, svc_start, svc_raw in classes:
        rows = [dict(zip(cols, r)) for r in con.execute(
            "select id,class_id,pennant,commissioned,status from ship where class_id=?", (cid,))]
        if not rows:
            continue
        # order: by hull number when most ships have one, else by table order (usually chronological)
        with_num = sum(1 for r in rows if re.search(r"\d", r["pennant"] or ""))
        rows.sort(key=_order_key if with_num >= 0.7 * len(rows) else (lambda r: r["id"]))
        for r in rows:
            m = re.match(r"(\d{4})", r["commissioned"] or "")
            r["year"] = int(m.group(1)) if m and 1900 <= int(m.group(1)) <= 2040 else None
        known = [(i, r["year"]) for i, r in enumerate(rows) if r["year"]]
        # typical gap between consecutive dated sisters (capped to keep extrapolation conservative)
        gaps = [(b[1] - a[1]) / (b[0] - a[0]) for a, b in zip(known, known[1:]) if b[0] > a[0] and b[1] >= a[1]]
        step = min(max(statistics.median(gaps), 0.0), 2.5) if gaps else None
        first_year = int(svc_start) if svc_start and str(svc_start).isdigit() else None
        yrs = [int(y) for y in re.findall(r"\b(19[4-9]\d|20[0-3]\d)\b", svc_raw or "")]
        for i, r in enumerate(rows):
            if r["year"]:
                con.execute("UPDATE ship SET service_year=?, service_year_estimated=0 WHERE id=?", (r["year"], r["id"]))
                continue
            est = basis = conf = None
            before = [k for k in known if k[0] < i]
            after = [k for k in known if k[0] > i]
            if before and after:
                (i0, y0), (i1, y1) = before[-1], after[0]
                est = round(y0 + (y1 - y0) * (i - i0) / (i1 - i0))
                basis, conf = f"interpolated between sisters {y0} and {y1}", "high"
            elif before:
                i0, y0 = before[-1]
                est = round(y0 + (step if step is not None else 1.0) * (i - i0))
                basis, conf = f"extrapolated after sister {y0} (gap {step if step is not None else 1.0:.1f}y/ship)", "medium"
            elif after:
                i1, y1 = after[0]
                est = round(y1 - (step if step is not None else 1.0) * (i1 - i))
                basis, conf = f"extrapolated before sister {y1} (gap {step if step is not None else 1.0:.1f}y/ship)", "medium"
            elif first_year:
                est = first_year + round(i * 1.0) if len(rows) > 1 else first_year
                basis, conf = f"class first in service {first_year}, +1y per ship in order", "low"
            elif yrs:
                est = yrs[0] + i
                basis, conf = f"start of class service range {yrs[0]}, +1y per ship in order", "low"
            if est is None:
                n_est["none"] += 1
                continue
            planned = r["status"] == "planned"
            if not planned:
                est = min(est, TODAY_YEAR)
            if first_year and est < first_year and not before:
                est = first_year
            con.execute("UPDATE ship SET service_year=?, service_year_estimated=1, service_year_est_basis=?, service_year_est_confidence=? WHERE id=?",
                        (est, basis + (" [planned/not yet in service]" if planned else ""), conf, r["id"]))
            n_est[conf] += 1
    con.commit()
    print("estimated service years:", n_est)
