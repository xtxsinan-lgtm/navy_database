"""Step 4: build data/navy.db from data/classes_raw.json + data/ships_raw.json (+ US list page)."""
import json, pathlib, re, sys
from . import db, wiki, ships as shipmod, classparse as cp
from .countries import LIST_PAGES

ROOT = pathlib.Path(__file__).resolve().parent.parent
COUNTRY_WORDS = {"CN": r"china|chinese|plan\b|people.s liberation", "RU": r"russia|soviet|russian",
                 "IN": r"india|indian", "TR": r"turk", "KR": r"korea", "JP": r"japan",
                 "GB": r"british|united kingdom|royal navy", "FR": r"france|french", "US": r"united states|u\.?s\.? navy"}
ALL_NATIONS = (r"vietnam|algeria|indonesia|egypt|iran|libya|syria|ukrain|poland|polish|bulgaria|belgi|netherlands|dutch|latvia|pakistan|bangladesh|"
               r"myanmar|philippines|malaysia|thailand|brazil|chile|greece|greek|israel|saudi|venezuela|peru|argentin|mexic|nigeria|angola|"
               r"cuba|north korea|taiwan|vietnam|singapore|australia|canada|german|italy|italian|spain|spanish|norway|sweden|denmark|"
               r"portugal|romania|estonia|lithuania|finland|qatar|oman|uae|emirates|kuwait|morocco|tunisia|cameroon|ghana|kenya|"
               r"sri lanka|nepal|new zealand|colombia|ecuador|uruguay|croatia|slovenia|georgia|azerbaijan|kazakhstan|turkmen|iraq|jordan|yemen")
SUPPLEMENT = {
    "IN": ["List of destroyers of India", "List of frigates of India", "List of ships of the Indian Navy"],
    "TR": ["List of patrol vessels of the Turkish Navy", "List of submarines of the Turkish Navy",
           "List of amphibious warfare vessels of the Turkish Navy"],
}
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
        ctx = f'{r.get("sub", "")} {r["section"]}'
        own = COUNTRY_WORDS[r["country"]]
        if re.search(ALL_NATIONS, ctx, re.I) and not re.search(own, ctx, re.I):
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
        con.execute("INSERT INTO ship(class_id,country,name,pennant,commissioned,commissioned_raw,status,status_raw,status_basis,source_page,source_rev) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (k, r["country"], r["name"], r["pennant"], r["commissioned"], r["commissioned_raw"],
                     r["status"], r.get("status_raw"), "table" if r["status"] != "unknown" else None, r["source_page"], r["source_rev"]))

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
    filled = set()

    # ---- fill classes that still have no ships
    def nostar(k):
        return con.execute("select count(*) from ship where class_id=?", (k,)).fetchone()[0] == 0

    def ascii_(x):
        import unicodedata
        return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", x or "").encode("ascii", "ignore").decode().lower())

    # (a) single-ship pages: the ship's own infobox
    for c in classes:
        k = cid[(c["country"], c["page"])]
        ib = c["infobox"]
        if not nostar(k) or re.search(r"class|Type \d", c["page"]) or not (ib.get("commissioned") or ib.get("in_commission_range")):
            continue
        nm = re.sub(r"^(Chinese|Russian|French|Soviet)\s+(aircraft carrier|destroyer|frigate|submarine)\s+|^(INS|TCG|USS|HMS)\s+", "", c["page"])
        stt = cp.plain(ib.get("status", "")) or None
        low = (stt or "").lower()
        status = "inactive" if re.search(r"decommission|retired|scrap|sunk|museum", low) else "active"
        com = cp.plain(ib.get("commissioned") or "") or (str((cp.years(ib.get("in_commission_range")) or [""])[0]))
        con.execute("INSERT INTO ship(class_id,country,name,pennant,commissioned,commissioned_raw,status,status_raw,status_basis,source_page,source_rev) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?)", (k, c["country"], nm, None, shipmod._iso(com), com[:80], status, stt, "table",
                                                       c["page"], c["revid"]))

    # (b) per-ship rows of the country's active list that carry a class column
    for cc, pages in LIST_PAGES.items():
        if cc == "US":
            continue
        mine = {c["page"]: ascii_(re.sub(r"[-\s]class.*$", "", c["page"], flags=re.I)) for c in classes if c["country"] == cc}
        for pg in pages:
            hh, rv = wiki.html(pg)
            for head, trs in shipmod.tables(hh):
                if re.search(r"auxil|support|train|tug|survey|research|replen|logistic|misc|service craft|intelligence|icebreak|landing craft", head, re.I):
                    continue
                for r in trs:
                    cl = ascii_(re.sub(r"[-\s]?class", "", r.get("class_raw") or "", flags=re.I))
                    page = next((p for p, st in mine.items() if st and cl.startswith(st)), None)
                    if not page:
                        continue
                    k = cid[(cc, page)]
                    if not nostar(k) and (k, "list") not in filled:
                        continue
                    filled.add((k, "list"))
                    com = r["commissioned"] if r["commissioned"] and int(r["commissioned"][:4]) >= 1940 else None
                    con.execute("INSERT INTO ship(class_id,country,name,pennant,commissioned,commissioned_raw,status,status_basis,source_page,source_rev) "
                                "VALUES (?,?,?,?,?,?,?,?,?,?)", (k, cc, r["name"], r["pennant"], com, r["commissioned_raw"][:80],
                                                                 "active", "country-list", pg, rv))


    # ---- supplementary per-class lists: add ships the class page lacked (match by class heading, dedupe by name/pennant)
    def sup_norm(x):
        return ascii_(re.sub(r"\(.*?\)|^(?:INS|TCG|HMIS|JS|JDS|ROKS|FS|USS|HMS)\s+", "", x or "", flags=re.I))


    PEN = re.compile(r"^[A-Z]{1,4}[- ]?\d{1,4}$")

    def reconcile(k, r):
        """True if the list row r is already present (matched by name or pennant); fixes name/pennant columns that were swapped."""
        rp = ascii_(r["pennant"]) if r["pennant"] else None
        for sid, nm, pn in con.execute("select id,name,pennant from ship where class_id=?", (k,)).fetchall():
            if sup_norm(nm) == sup_norm(r["name"]):
                return True
            if rp and (ascii_(pn or "") == rp or (PEN.match((nm or "").strip()) and ascii_(nm) == rp)):
                if PEN.match((nm or "").strip()):
                    con.execute("UPDATE ship SET name=?, pennant=? WHERE id=?", (re.sub(r"^(?:JS|JDS|INS|TCG)\s+", "", r["name"]), r["pennant"], sid))
                return True
        return False

    stems = {}
    for c in classes:
        stems.setdefault(c["country"], {})[c["page"]] = ascii_(re.sub(r"[-\s]class.*$|\s*\(\d{4}\)$", "", c["page"], flags=re.I))
    added = 0
    for cc, pages in SUPPLEMENT.items():
        for pg in pages:
            hh, rv = wiki.html(pg)
            for head, trs in shipmod.tables(hh):
                hs = ascii_(re.sub(r"[-\s]*class.*$", "", head, flags=re.I))
                page = next((p for p, st in stems[cc].items() if len(st) >= 3 and hs == st), None)
                if not page:
                    continue
                k = cid[(cc, page)]
                for r in trs:
                    if r["status"] == "inactive" or re.match(r"never|cancel|not commission", r["commissioned_raw"], re.I) or reconcile(k, r):
                        continue
                    nm = re.sub(r"\s*\(.*?\)", "", re.sub(r"^(?:INS|TCG)\s+", "", r["name"])).strip()
                    con.execute("INSERT INTO ship(class_id,country,name,pennant,commissioned,commissioned_raw,status,status_raw,status_basis,source_page,source_rev) "
                                "VALUES (?,?,?,?,?,?,?,?,?,?,?)", (k, cc, nm, r["pennant"] or (re.search(r"\(([A-Z]-?\d+)\)", r["name"]) or [None, None])[1],
                                                                   r["commissioned"], r["commissioned_raw"][:80], r["status"], r.get("status_raw"),
                                                                   "supplement" if r["status"] != "unknown" else None, pg, rv))
                    added += 1
    print("supplement rows added:", added)

    # ---- JP / RU: complete classes from the country's active list (class column), add only missing ships
    for cc in ("JP", "RU"):
        for pg in LIST_PAGES[cc]:
            hh, rv = wiki.html(pg)
            for head, trs in shipmod.tables(hh):
                if re.search(r"auxil|support|train|tug|survey|research|replen|logistic|misc|service craft|intelligence|icebreak|landing craft", head, re.I):
                    continue
                for r in trs:
                    cl = ascii_(re.sub(r"[-\s]?class|Project \d+", "", r.get("class_raw") or "", flags=re.I))
                    page = next((p for p, st in stems[cc].items() if st and cl.startswith(st)), None)
                    if not page:
                        continue
                    k = cid[(cc, page)]
                    if reconcile(k, r):
                        continue
                    com = r["commissioned"] if r["commissioned"] and int(r["commissioned"][:4]) >= 1940 else None
                    con.execute("INSERT INTO ship(class_id,country,name,pennant,commissioned,commissioned_raw,status,status_basis,source_page,source_rev) "
                                "VALUES (?,?,?,?,?,?,?,?,?,?)", (k, cc, re.sub(r"^(?:JS|JDS)\s+", "", r["name"]), r["pennant"], com,
                                                                 r["commissioned_raw"][:80], "active", "country-list", pg, rv))
                    added += 1

    # ---- targeted single-ship pages (data/ships_extra_targeted.json): read from each ship's own infobox
    tpath = ROOT / "data" / "ships_extra_targeted.json"
    if tpath.exists():
        for r in json.load(open(tpath)):
            k = cid.get((r["country"], r["class_page"]))
            if not k:
                continue
            pen = (re.findall(r"[A-Z]{1,3}[- ]?\d{1,4}", r.get("pennant") or "") or [None])[-1]
            if r["class_page"].startswith("Son Won-il") and not (pen and 72 <= int(re.sub(r"\D", "", pen)) <= 82):
                continue            # the page's link list also contains the Dosan Ahn Changho class
            row = {"name": re.sub(r"\s*\(\d{4}\)$", "", re.sub(r"^ROKS\s+", "", r["name"])), "pennant": pen,
                   "commissioned": r["commissioned"], "commissioned_raw": r["commissioned_raw"],
                   "status": shipmod.classify(r.get("status_raw") or "", ""), "status_raw": r.get("status_raw")}
            if re.match(r"never|cancel|not commission", r["commissioned_raw"], re.I):
                continue
            row["name"] = re.sub(r"^(?:INS|TCG|HMS)\s+", "", row["name"])
            hit = next((sid for sid, nm, cm in con.execute("select id,name,commissioned from ship where class_id=?", (k,)).fetchall()
                        if sup_norm(nm) == sup_norm(row["name"]) or (pen and ascii_(pen) == ascii_(nm))), None)
            if hit is not None:      # a list row without a date: enrich it from the ship's own page
                con.execute("UPDATE ship SET name=?, pennant=?, commissioned=?, commissioned_raw=?, status=?, status_raw=?, status_basis='ship-page', "
                            "source_page=?, source_rev=? WHERE id=?", (row["name"], pen, row["commissioned"], row["commissioned_raw"][:80], row["status"],
                                                                       row["status_raw"], r["page"], r["rev"], hit))
                continue
            con.execute("INSERT INTO ship(class_id,country,name,pennant,commissioned,commissioned_raw,status,status_raw,status_basis,source_page,source_rev) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?)", (k, r["country"], row["name"], pen, row["commissioned"], row["commissioned_raw"][:80],
                                                           row["status"], row["status_raw"], "ship-page", r["page"], r["rev"]))
            added += 1
    print("total supplement/complete rows added:", added)


    # ---- China: per-ship rows from zh.wikipedia (hull numbers, names, commissioning dates, status)
    zpath = ROOT / "data" / "ships_zh.json"
    if zpath.exists():
        def zh_status(raw):
            t = (raw or "").strip()
            if not t:
                return "unknown"
            if re.search(r"海警|转隶|轉隶|移交|转让|轉讓|出口|退役|除役|沉没|沉沒|拆解|报废", t) and not re.match(r"现役|現役|在役", t):
                return "inactive"
            if re.search(r"试验|试航|海试|建造|下水|舾装|在建|预定|计划", t) and not re.match(r"现役|現役|在役", t):
                return "planned"
            if re.match(r"现役|現役|在役|服役", t):
                return "active"
            return "unknown"

        zadded = zupd = 0
        for r in json.load(open(zpath)):
            k = cid.get(("CN", r["class_page"]))
            if not k:
                continue
            pen = r["pennant"] if r["pennant"] and re.fullmatch(r"[0-9]{2,3}[A-Z]?", r["pennant"].strip()) else None
            nm = re.sub(r"(?:号|號|舰|艦|艇)$", "", r["name"].strip())
            if not pen and re.fullmatch(r"[0-9]{2,3}", nm):
                pen = nm
            if r["class_page"] == "Kilo-class submarine" and not (pen and re.fullmatch(r"\d{3}", pen) and 364 <= int(pen) <= 375):
                continue                                 # the zh Kilo page lists every operator; keep PLAN boats only
            if not nm:
                continue
            st = zh_status(r.get("status_raw"))
            hit = next((sid for sid, p in con.execute("select id,pennant from ship where class_id=?", (k,)).fetchall()
                        if p and pen and ascii_(p) == ascii_(pen)), None)
            if hit is None and pen:
                # existing rows whose 'name' holds the hull number or Chinese name
                hit = next((sid for sid, n in con.execute("select id,name from ship where class_id=?", (k,)).fetchall()
                            if ascii_(n) == ascii_(pen) or (nm and nm in n)), None)
            if hit is not None:
                con.execute("UPDATE ship SET pennant=coalesce(pennant,?), commissioned=coalesce(commissioned,?), commissioned_raw=coalesce(commissioned_raw,?), "
                            "status=CASE WHEN status='unknown' THEN ? ELSE status END, status_raw=coalesce(status_raw,?) WHERE id=?",
                            (pen, r["commissioned"], r["commissioned_raw"][:80], st, r.get("status_raw"), hit))
                zupd += 1
                continue
            con.execute("INSERT INTO ship(class_id,country,name,pennant,commissioned,commissioned_raw,status,status_raw,status_basis,source_page,source_rev) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?)", (k, "CN", nm if not pen or nm != pen else pen, pen, r["commissioned"], r["commissioned_raw"][:80], st,
                                                           r.get("status_raw"), "zh-wiki" if st != "unknown" else None, "zh:" + r["zh_page"], r["rev"]))
            zadded += 1
        print("zh rows added:", zadded, "enriched:", zupd)

    # ---- not-yet-in-service ships are kept but marked 'planned' (never counted as active)
    con.execute("""UPDATE ship SET status='planned', status_basis=coalesce(status_basis,'date/name')
                   WHERE (name LIKE 'TB_%' AND length(name)<=6)
                      OR substr(commissioned,1,7) > '2026-10'
                      OR (commissioned IS NULL AND status!='inactive' AND (
                            lower(coalesce(status_raw,'')) GLOB '*planned*' OR lower(coalesce(status_raw,'')) GLOB '*under construction*'
                         OR lower(coalesce(status_raw,'')) GLOB '*building*' OR lower(coalesce(status_raw,'')) GLOB '*on order*'
                         OR lower(coalesce(status_raw,'')) GLOB '*fitting out*' OR lower(coalesce(status_raw,'')) GLOB '*sea trials*'))""")
    # ---- drop exact duplicates (same class, name, commissioned date)
    con.execute("""DELETE FROM ship WHERE id NOT IN (SELECT min(id) FROM ship GROUP BY class_id, lower(name), coalesce(commissioned,''), coalesce(pennant,''))""")

    # ---- manual corrections reviewed against the page text (data/overrides/<CC>.json)
    for f in sorted((ROOT / "data" / "overrides").glob("*.json")):
        for page, o in json.load(open(f)).items():
            k = cid.get((f.stem, page))
            if not k:
                print("override for unknown class", f.stem, page); continue
            sets, args = [], []
            for col, key in (("displacement_full_t", "disp"), ("displacement_basis", "basis"), ("service_start", "svc")):
                if key in o:
                    sets.append(f"{col}=?"); args.append(o[key] if key != "svc" else str(o[key]))
            sets.append("note=coalesce(note||'; ','')||?"); args.append("manual review: " + o.get("src", ""))
            con.execute(f"UPDATE ship_class SET {', '.join(sets)} WHERE id=?", (*args, k))
            if "radars" in o:
                con.execute("DELETE FROM radar WHERE class_id=?", (k,))
                for r in o["radars"]:
                    con.execute("INSERT INTO radar VALUES (?,?,?,?)", (k, r["model"], r.get("role"), "manual"))
            if "vls" in o:
                con.execute("DELETE FROM vls WHERE class_id=?", (k,))
                for v in o["vls"]:
                    con.execute("INSERT INTO vls VALUES (?,?,?,?)", (k, v["model"], v["cells"], v.get("raw", "manual")))
            if "weapons" in o:
                con.execute("DELETE FROM weapon WHERE class_id=?", (k,))
                for x in o["weapons"]:
                    con.execute("INSERT INTO weapon VALUES (?,?,?,?,?)", (k, x["name"], x["qty"], x["category"], "manual"))

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
