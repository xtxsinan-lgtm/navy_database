"""MediaWiki API access with an on-disk cache (data/raw)."""
import hashlib, json, pathlib, time
import requests

API = "https://{lang}.wikipedia.org/w/api.php"
CACHE = pathlib.Path(__file__).resolve().parent.parent / "data" / "raw"
UA = {"User-Agent": "navy_database/0.1 (personal research project)"}


def _get(params, lang="en"):
    key = hashlib.sha1(json.dumps([params, lang] if lang != "en" else params, sort_keys=True).encode()).hexdigest()
    f = CACHE / f"{key}.json"
    if f.exists():
        return json.loads(f.read_text())
    for i in range(8):
        try:
            r = requests.get(API.format(lang=lang), params={**params, "format": "json", "formatversion": 2},
                             headers=UA, timeout=30)
            if r.status_code == 429 or not r.headers.get("content-type", "").startswith("application/json"):
                time.sleep(min(float(r.headers.get("Retry-After", 0) or 0) or 15 * (i + 1), 120))
                continue
            r.raise_for_status()
            f.write_text(r.text)
            time.sleep(1.0)
            return r.json()
        except requests.RequestException:
            time.sleep(2 ** (i + 1))
    raise RuntimeError(f"failed: {params}")


def wikitext(title, lang="en"):
    """Return (wikitext, revid) following redirects."""
    d = _get({"action": "query", "prop": "revisions", "rvprop": "content|ids",
              "rvslots": "main", "titles": title, "redirects": 1}, lang)
    p = d["query"]["pages"][0]
    if p.get("missing"):
        return None, None
    rev = p["revisions"][0]
    return rev["slots"]["main"]["content"], rev["revid"]


def html(title, lang="en"):
    """Rendered page HTML (templates expanded) and revid."""
    d = _get({"action": "parse", "page": title, "prop": "text|revid", "redirects": 1,
              "disablelimitreport": 1, "disableeditsection": 1}, lang)
    return d["parse"]["text"], d["parse"]["revid"]


def expand(text):
    """Expand templates in a snippet (for infobox fields that are bare template transclusions)."""
    d = _get({"action": "expandtemplates", "text": text, "prop": "wikitext"})
    return d["expandtemplates"]["wikitext"]
