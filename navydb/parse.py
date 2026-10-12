"""Parse ship-class infoboxes into structured fields."""
import re
import mwparserfromhell as mw

INFOBOX = re.compile(r"infobox (ship|military unit)", re.I)


def infobox(text):
    """Merge all sibling 'Infobox ship *' templates (begin/career/characteristics/...).

    Repeated keys (e.g. several sub-class characteristics blocks) are kept as key, key__2, ...
    """
    out = {}
    for t in mw.parse(text).filter_templates(recursive=True):
        name = str(t.name).strip().lower()
        if not name.startswith("infobox ship"):
            continue
        for p in t.params:
            k = str(p.name).strip().lower()
            if not k or k.startswith("section") or not str(p.value).strip():
                continue
            n, kk = 1, k
            while kk in out:
                n += 1; kk = f"{k}__{n}"
            out[kk] = str(p.value).strip()
    return out


def clean(s):
    return re.sub(r"\s+", " ", mw.parse(s or "").strip_code()).strip()


def full_load_tonnes(raw):
    """Pick the full-load / submerged figure, else the largest tonnage figure."""
    txt = clean(raw)
    best = None
    for m in re.finditer(r"([\d,]{3,})\s*(?:t|tonnes|tons|long tons)", txt, re.I):
        v = float(m.group(1).replace(",", ""))
        ctx = txt[max(0, m.start() - 40):m.end() + 15].lower()
        if "full" in ctx or "submerged" in ctx:
            return v
        best = max(best or 0, v)
    return best


def years(raw):
    ys = re.findall(r"\b(19[4-9]\d|20[0-3]\d)\b", clean(raw))
    return ys[0] if ys else None


def split_items(raw):
    """Split an armament/sensors field into bullet-ish items."""
    raw = re.sub(r"<br\s*/?>|\{\{(?:plainlist|ubl|unbulleted list|flatlist)\||\}\}", "\n", raw or "", flags=re.I)
    items = [clean(x.lstrip("*| ")) for x in re.split(r"\n|\*", raw)]
    return [i for i in items if i]


VLS_RE = re.compile(r"(\d+)\s*(?:×|x|-cell|cell)?[^,;]*?\b(Mk\s*41|Mk\s*57|Mk\s*48|Sylver\s*A\d+|SYLVER\s*[A-Z]\d+|K-VLS|KVLS|UKSK|3S14|Redut|[A-Z]?VLS[-\w]*)", re.I)


def parse_qty(item):
    m = re.match(r"(\d+)\s*[×x]\s*(.+)", item)
    return (int(m.group(1)), m.group(2)) if m else (None, item)
