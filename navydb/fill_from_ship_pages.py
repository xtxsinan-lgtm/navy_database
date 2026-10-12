"""For classes with no ship table: follow links to individual ship pages and read their own infobox.

Writes data/ships_extra.json (rows merged by build_db)."""
import json, pathlib, re, sqlite3
from bs4 import BeautifulSoup
from . import wiki, parse, classparse as cp, ships as shipmod

ROOT = pathlib.Path(__file__).resolve().parent.parent
PREFIX = re.compile(r"^(French (?:frigate|destroyer|submarine|aircraft carrier|aviso|ship)|Chinese (?:destroyer|frigate|submarine|aircraft carrier|corvette|missile boat|landing)|"
                    r"Russian (?:destroyer|frigate|submarine|corvette|ship|minesweeper|aircraft)|Soviet (?:destroyer|submarine|ship)|"
                    r"INS |TCG |ROKS |HMS |HMAS |FS |JS |JDS |BNS |PLANS? |Indian |Turkish |South Korean (?:submarine|ship))")
BAD = re.compile(r"class|List of|\bNavy\b|Category|Template|Fleet|Type \d|Project \d|\(disambiguation\)", re.I)


def candidates(page):
    h, _ = wiki.html(page)
    soup = BeautifulSoup(h, "lxml")
    out, seen = [], set()
    for a in soup.find_all("a"):
        t = a.get("title") or ""
        if not t or t in seen or BAD.search(t) or not PREFIX.match(t) or ":" in t:
            continue
        seen.add(t); out.append(t)
    return out[:20]


def ship_row(title):
    text, rev = wiki.wikitext(title)
    if not text:
        return None
    ib = parse.infobox(text)
    com = cp.plain(next((v for k, v in ib.items() if k.split("__")[0] == "commissioned"), "") or "")
    pen = next((cp.plain(v) for k, v in ib.items() if k.split("__")[0] in ("identification", "pennant", "hull number")), None)
    if not com:
        return None
    st = cp.plain(next((v for k, v in ib.items() if k.split("__")[0] == "status"), "") or "")
    return {"name": re.sub(r"^(?:French|Chinese|Russian|Soviet|South Korean|Indian|Turkish)\s+\w+(?:\s+\w+)??\s+(?=[A-ZÉ])", "", title),
            "page": title, "rev": rev, "pennant": (pen or "")[:40] or None, "commissioned_raw": com[:80],
            "commissioned": shipmod._iso(com), "status_raw": st[:80] or None}


def main():
    con = sqlite3.connect(ROOT / "data" / "navy.db")
    miss = con.execute("select country,page from ship_class c where not exists(select 1 from ship s where s.class_id=c.id)").fetchall()
    res = []
    for cc, page in miss:
        for t in candidates(page):
            r = ship_row(t)
            if r:
                res.append({"country": cc, "class_page": page, **r})
        print(cc, page, sum(1 for r in res if r["class_page"] == page), flush=True)
    (ROOT / "data" / "ships_extra.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print("DONE", len(res))


if __name__ == "__main__":
    main()
