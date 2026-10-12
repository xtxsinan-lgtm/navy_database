"""MediaWiki API access with an on-disk cache (data/raw)."""
import hashlib, json, pathlib, time
import requests

API = "https://en.wikipedia.org/w/api.php"
CACHE = pathlib.Path(__file__).resolve().parent.parent / "data" / "raw"
UA = {"User-Agent": "navy_database/0.1 (personal research project)"}


def _get(params):
    key = hashlib.sha1(json.dumps(params, sort_keys=True).encode()).hexdigest()
    f = CACHE / f"{key}.json"
    if f.exists():
        return json.loads(f.read_text())
    for i in range(4):
        try:
            r = requests.get(API, params={**params, "format": "json", "formatversion": 2},
                             headers=UA, timeout=30)
            r.raise_for_status()
            f.write_text(r.text)
            time.sleep(0.2)
            return r.json()
        except requests.RequestException:
            time.sleep(2 ** (i + 1))
    raise RuntimeError(f"failed: {params}")


def wikitext(title):
    """Return (wikitext, revid) following redirects."""
    d = _get({"action": "query", "prop": "revisions", "rvprop": "content|ids",
              "rvslots": "main", "titles": title, "redirects": 1})
    p = d["query"]["pages"][0]
    if p.get("missing"):
        return None, None
    rev = p["revisions"][0]
    return rev["slots"]["main"]["content"], rev["revid"]
