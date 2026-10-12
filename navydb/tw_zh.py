"""Taiwan (ROCN): ships from zh.wikipedia '中華民國海軍現役艦艇' -> data/ships_tw_zh.json.

Each class row has a cell like 'PFG-1101 /1993 PFG-1103 /1994 ...' (hull number / year in ROCN service)."""
import json, pathlib, re
from bs4 import BeautifulSoup
from . import wiki, ships

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAIR = re.compile(r"([A-Z]{2,4}-\d{3,4})\s*/\s*((?:19|20)\d\d)?")


def main():
    h, rev = wiki.html("中華民國海軍現役艦艇", "zh")
    soup = BeautifulSoup(h, "lxml")
    head, out = "", []
    for el in soup.find_all(["h2", "h3", "table"]):
        if el.name != "table":
            head = el.get_text(" ", strip=True)[:20]; continue
        if "wikitable" not in (el.get("class") or []):
            continue
        cur = None
        for tr in el.find_all("tr")[1:]:
            tds = tr.find_all(["td", "th"])
            for sup in tr.find_all("sup"):
                sup.decompose()
            if len(tds) >= 5:
                cur = {"class_zh": tds[0].get_text(" ", strip=True), "tonnage": tds[4].get_text(" ", strip=True),
                       "note": tds[5].get_text(" ", strip=True) if len(tds) > 5 else ""}
                cell = tds[3].get_text(" ", strip=True)
            elif cur and len(tds) >= 2:                    # continuation row (rowspan) of the same class
                cell = tds[0].get_text(" ", strip=True) + " " + tds[1].get_text(" ", strip=True)
                cur = dict(cur, tonnage=tds[-1].get_text(" ", strip=True) or cur["tonnage"])
            else:
                continue
            for m in PAIR.finditer(cell):
                out.append({"section": head, "rev": rev, **cur, "pennant": m.group(1), "year": m.group(2)})
    # class pages with a per-ship table (traditional-Chinese headers)
    for zh_page, en_class in [("光華六號飛彈快艇", "Kuang Hua VI-class missile boat"), ("海鯤級潛艦", "Hai Kun-class submarine")]:
        hh, rv = wiki.html(zh_page, "zh")
        for head, rows in ships.tables(hh, any_class=True):
            for r in rows:
                out.append({"section": head, "rev": rv, "class_zh": zh_page, "en_class": en_class, "tonnage": "", "note": "", "kind": "table",
                            "pennant": r["pennant"] or r["name"], "name": r["name"], "year": (r["commissioned"] or "")[:4] or None,
                            "commissioned": r["commissioned"], "status": r["status"], "status_raw": r["status_raw"],
                            "decommissioned_raw": r["decommissioned_raw"]})
    (ROOT / "data" / "ships_tw_zh.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print("DONE", len(out))


if __name__ == "__main__":
    main()
