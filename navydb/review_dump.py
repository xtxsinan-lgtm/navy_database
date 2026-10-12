"""Print parsed-vs-raw spec text for manual review: python -m navydb.review_dump US"""
import json, sys, pathlib, re
from . import classparse as cp, wiki

ROOT = pathlib.Path(__file__).resolve().parent.parent

def field(ib, key):
    v = cp.first(ib, key)
    if v and re.fullmatch(r"\{\{[^{}|]+\}\}", v.strip()):
        try: v = wiki.expand(v.strip())
        except Exception: pass
    return v

def main(country, limit=1300):
    for c in json.load(open(ROOT / "data" / "classes_raw.json")):
        if c["country"] != country: continue
        ib = c["infobox"]
        print("=" * 100); print(c["country"], c["type"], c["page"])
        d = cp.displacement(field(ib, "displacement"))
        print("PARSED disp:", d[:2], "| svc:", cp.first(ib, "in_service_range") or cp.first(ib, "in_commission_range"))
        for key in ("displacement", "sensors", "armament"):
            t = cp.plain(field(ib, key) or "")
            print(f"--{key.upper()}--"); print(t[:limit])

if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1300)
