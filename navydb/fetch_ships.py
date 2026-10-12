"""Step 3: per-ship rows from each class page's wikitables -> data/ships_raw.json."""
import json, pathlib
from . import wiki, ships
from .classes import C

OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "ships_raw.json"
SKIP_HEAD = ("cancel", "planned", "future", "former", "retired", "decommission", "export", "foreign")

def main():
    res, none = [], []
    for country, typ, page in C:
        try:
            h, rev = wiki.html(page)
        except Exception as e:
            none.append((page, f"error {e}")); continue
        n = 0
        for head, rows in ships.tables(h):
            if any(w in head.lower() for w in SKIP_HEAD):
                continue
            for r in rows:
                res.append({"country": country, "class_page": page, "section": head,
                            "source_page": page, "source_rev": rev, **r}); n += 1
        if not n: none.append((page, "no ship table"))
        print(country, page, n, flush=True)
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print("NOSHIPS:", json.dumps(none, ensure_ascii=False))
