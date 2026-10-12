"""Step 4: build data/navy.db from data/classes_raw.json + data/ships_raw.json (+ US list page)."""
import json, pathlib, re, sys
from . import db, wiki, ships as shipmod, classparse as cp
from .countries import LIST_PAGES

ROOT = pathlib.Path(__file__).resolve().parent.parent
COUNTRY_WORDS = {"CN": r"china|chinese|plan\b|people.s liberation", "RU": r"russia|soviet|russian",
                 "IN": r"india|indian", "TR": r"turk", "KR": r"korea", "JP": r"japan",
                 "GB": r"british|united kingdom|royal navy", "FR": r"france|french", "US": r"united states|u\.?s\.? navy"}
NAVY = {"US": "United States Navy", "CN": "PLA Navy", "RU": "Russian Navy", "JP": "JMSDF", "GB": "Royal Navy",
        "FR": "French Navy", "KR": "ROK Navy", "IN": "Indian Navy", "TR": "Turkish Naval Forces"}


def field(ib, key):
    v = cp.first(ib, key)
    if v and re.fullmatch(r"\{\{[^{}|]+\}\}", v.strip()):
        try:
            v = wiki.expand(v.strip())
        except Exception:
            pass
    return v


def int_or_none(v):
    m = re.search(r"\d+", cp.plain(v or ""))
    return int(m.group()) if m else None


def main():
    classes = json.load(open(ROOT / "data" / "classes_raw.json"))
    rows = json.load(open(ROOT / "data" / "ships_raw.json"))
    pagecount = {}
    revgroup = {}
    for c in classes:
        pagecount.setdefault(c["page"], set()).add(c["country"])
        revgroup.setdefault((c["country"], c["revid"]), []).append(c["page"])
    shared_rev = {pg for pages in revgroup.values() if len(pages) > 1 for pg in pages}

    def stem(page):
        return re.sub(r"[-\s]class.*$", "", page, flags=re.I).strip().lower()
    path = ROOT / "data" / "navy.db"
    if path.exists():
        path.unlink()
    con = db.connect(path)
    cid = {}
    for c in classes:
        ib = c["infobox"]
        disp, basis, disp_txt = cp.displacement(field(ib, "displacement"))
        ships_here = [r for r in rows if r["class_page"] == c["page"] and r["country"] == c["country"]]
        yrs = [int(r["commissioned"][:4]) for r in ships_here if r["commissioned"]]
        iy = cp.years(cp.first(ib, "in_service_range") or cp.first(ib, "in_commission_range") or cp.first(ib, "service") or "")
        start = min(yrs) if yrs else (iy[0] if iy else None)
        note = []
        if len(pagecount[c["page"]]) > 1:
            note.append("page shared by multiple countries; specs describe the page's main variant")
        if not ib:
            note.append("no infobox")
        cur = con.execute(
            "INSERT INTO ship_class(country,navy,name,type,page,revid,displacement_full_t,displacement_raw,displacement_basis,"
            "service_start,service_raw,active_count,note) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (c["country"], NAVY[c["country"]], re.sub(r"^.*? (?=\w)", "", c["page"]) if False else c["page"], c["type"], c["page"], c["revid"],
             disp, disp_txt[:500], basis, str(start) if start else None,
             (cp.first(ib, "in_service_range") or cp.first(ib, "in_commission_range") or "")[:200],
             int_or_none(cp.first(ib, "total_ships_active")), "; ".join(note) or None))
        k = cur.lastrowid
        cid[(c["country"], c["page"])] = k
        for r in cp.radars(field(ib, "sensors")):
            con.execute("INSERT INTO radar VALUES (?,?,?,?)", (k, r["model"], r["role"], r["raw"][:300]))
        arm = field(ib, "armament")
        for v in cp.vls(arm):
            con.execute("INSERT INTO vls VALUES (?,?,?,?)", (k, v["model"], v["cells"], v["raw"][:300]))
        for w in cp.weapons(arm):
            con.execute("INSERT INTO weapon VALUES (?,?,?,?,?)", (k, w["name"], w["qty"], w["category"], w["raw"][:300]))

    # ---- ships from class pages
    seen = set()
    for r in rows:
        k = cid.get((r["country"], r["class_page"]))
        if not k:
            continue
        if len(pagecount[r["class_page"]]) > 1 and not re.search(COUNTRY_WORDS[r["country"]], r["section"], re.I) \
                and not re.search(COUNTRY_WORDS[r["country"]], r.get("class_raw") or "", re.I):
            continue
        if r["class_page"] in shared_rev:
            if stem(r["class_page"]) not in (r.get("class_raw") or "").lower():
                continue
        key = (k, r["name"], r["pennant"])
        if key in seen:
            continue
        seen.add(key)
        con.execute("INSERT INTO ship(class_id,country,name,pennant,commissioned,commissioned_raw,status,status_basis,source_page,source_rev) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (k, r["country"], r["name"], r["pennant"], r["commissioned"], r["commissioned_raw"],
                     r["status"], "table" if r["status"] != "unknown" else None, r["source_page"], r["source_rev"]))

    # ---- US: the active-ships list is authoritative for who is commissioned today
    h, rev = wiki.html(LIST_PAGES["US"][0])
    us = {p: k for (c, p), k in cid.items() if c == "US"}
    n_us = 0
    for head, trs in shipmod.tables(h):
        if head.strip() != "Commissioned":
            continue
        for r in trs:
            cl = (r.get("class_raw") or "").strip()
            page = next((p for p in us if cl and p.lower().startswith(cl.lower())), None)
            if not page:
                continue
            k = us[page]
            con.execute("DELETE FROM ship WHERE class_id=? AND source_page!=?", (k, LIST_PAGES["US"][0]))
            n_us += 1
            con.execute("INSERT INTO ship(class_id,country,name,pennant,commissioned,commissioned_raw,status,status_basis,source_page,source_rev) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?)", (k, "US", re.sub(r"^USS\s+", "", r["name"]), r["pennant"], r["commissioned"],
                                                        r["commissioned_raw"], "active", "us-list", LIST_PAGES["US"][0], rev))
    # ---- confirm 'unknown' rows that appear on the country's own active-ships list (name or pennant)
    def norm(x):
        return re.sub(r"[^a-z0-9]", "", re.sub(r"^(uss|hms|jds|js|tcg|ins|rokS|roks|fs|ran|plan)\s+", "", (x or "").lower().strip()))
    for cc, pages in LIST_PAGES.items():
        if cc == "US":
            continue
        names = set()
        for pg in pages:
            hh, _ = wiki.html(pg)
            for head, trs in shipmod.tables(hh):
                for r in trs:
                    names.add(norm(r["name"].split("/")[-1])); names.add(norm(r["pennant"]))
        names.discard("")
        for sid, nm, pn in con.execute("select id,name,pennant from ship where country=? and status='unknown'", (cc,)).fetchall():
            if norm(nm.split("/")[-1]) in names or (pn and norm(pn) in names):
                con.execute("update ship set status='active', status_basis='country-list' where id=?", (sid,))

    # ---- infer status for unknown rows when the class count says they must all be active
    for k, ac, sh in con.execute("select id, active_count, note like '%shared%' from ship_class").fetchall():
        if ac is None or sh or k in {v for (_, _), v in []}:
            continue
        act = con.execute("select count(*) from ship where class_id=? and status='active'", (k,)).fetchone()[0]
        unk = con.execute("select count(*) from ship where class_id=? and status='unknown'", (k,)).fetchone()[0]
        if unk and act + unk <= ac:
            con.execute("update ship set status='active', status_basis='inferred' where class_id=? and status='unknown'", (k,))
    con.commit()
    for t in ("ship_class", "radar", "vls", "weapon", "ship"):
        print(t, con.execute(f"select count(*) from {t}").fetchone()[0])
    print("US list rows used:", n_us)


if __name__ == "__main__":
    main()
