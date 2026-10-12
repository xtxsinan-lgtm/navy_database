"""Step 2: fetch each curated class page, parse infobox, store raw fields as JSON."""
import json, pathlib
from . import wiki, parse
from .classes import C

OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "classes_raw.json"

def main():
    res, missing = [], []
    for country, typ, page in C:
        text, rev = wiki.wikitext(page)
        if text is None:
            missing.append((country, page, "no page")); continue
        ib = parse.infobox(text)
        if not ib:
            missing.append((country, page, "no infobox"))
        res.append({"country": country, "type": typ, "page": page, "revid": rev, "infobox": ib})
        print(country, page, len(ib), flush=True)
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print("MISSING:", json.dumps(missing, ensure_ascii=False))

if __name__ == "__main__":
    main()
