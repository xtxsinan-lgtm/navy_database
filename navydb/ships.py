"""Extract per-ship rows (name / pennant / commissioning date) from wikitables."""
import re
from bs4 import BeautifulSoup

NAME_H = re.compile(r"^(name|ship|vessel|boat|hull|unit)", re.I)
PEND_H = re.compile(r"pennant|hull|hull no|number|^no\.?$|^id$|identification|^p\.? ?no|designation", re.I)
DATE_H = re.compile(r"commission|in service|service entry|entered service|entry into service|enter service|"
                    r"^service$|^date$|^accepted|^delivered|^completed", re.I)
SKIP_H = re.compile(r"laid down|launched|builder|shipyard|decommission|fate|retired", re.I)
DATE_RE = re.compile(r"(\d{1,2}\s+\w+\s+(?:19|20)\d\d|\w+\s+\d{1,2},\s+(?:19|20)\d\d|\w+\s+(?:19|20)\d\d|(?:19|20)\d\d(?:-\d\d(?:-\d\d)?)?)")


def _text(c):
    for s in c.find_all(["sup", "style"]):
        s.decompose()
    t = re.sub(r"\s+", " ", c.get_text(" ", strip=True))
    return re.sub(r"\s*\[\s*[\w ]{1,6}\s*\]", "", t).strip()


STATUS_H = re.compile(r"^status|^fate|^current status", re.I)
DECOM_H = re.compile(r"decommission|retired|withdrawn|stricken", re.I)
ACTIVE_RE = re.compile(r"\b(active|in service|in commission|commissioned|operational|serving|undergoing|refit|reserve fleet in)\b", re.I)
INACTIVE_RE = re.compile(r"decommission|retired|scrapp|sunk|museum|preserved|stricken|transferred|sold|broken up|"
                         r"cancel|lost|disposed|withdrawn|hulk|paid off|memorial|expended|target", re.I)


def classify(status_txt, decom_txt):
    if decom_txt and re.search(r"(19|20)\d\d", decom_txt):
        return "inactive"
    if status_txt:
        if INACTIVE_RE.search(status_txt) and not re.search(r"^in service|^active", status_txt, re.I):
            return "inactive"
        if ACTIVE_RE.search(status_txt):
            return "active"
        return "unknown"
    return "unknown"


def _iso(raw):
    from datetime import datetime
    raw = raw.replace("\xa0", " ").strip()
    m = DATE_RE.search(raw)
    if not m:
        return None
    s = m.group(1)
    for fmt in ("%d %B %Y", "%d %b %Y", "%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%B %Y", "%b %Y", "%Y-%m", "%Y"):
        try:
            d = datetime.strptime(s, fmt)
            return {"%Y": d.strftime("%Y"), "%B %Y": d.strftime("%Y-%m"), "%b %Y": d.strftime("%Y-%m"), "%Y-%m": d.strftime("%Y-%m")}.get(fmt, d.strftime("%Y-%m-%d"))
        except ValueError:
            pass
    return None


def tables(html):
    """Yield (section_heading, [row dicts]) for wikitables that have a commissioning-date column."""
    soup = BeautifulSoup(html, "lxml")
    head = ""
    for el in soup.find_all(["h2", "h3", "h4", "table"]):
        if el.name != "table":
            head = el.get_text(" ", strip=True); continue
        if "wikitable" not in (el.get("class") or []):
            continue
        rows = el.find_all("tr")
        hdr = None
        for r in rows[:3]:
            ths = r.find_all("th")
            if len(ths) >= 3:
                hdr = [_text(t) for t in ths]; break
        if not hdr:
            continue
        di = next((i for i, h in enumerate(hdr) if DATE_H.search(h) and not SKIP_H.search(h)), None)
        ni = next((i for i, h in enumerate(hdr) if NAME_H.search(h)), None)
        if di is None or ni is None:
            continue
        pi = next((i for i, h in enumerate(hdr) if PEND_H.search(h) and i != ni), None)
        si = next((i for i, h in enumerate(hdr) if STATUS_H.search(h)), None)
        xi = next((i for i, h in enumerate(hdr) if DECOM_H.search(h)), None)
        out = []
        for r in rows:
            cells = r.find_all(["td", "th"])
            if len(cells) != len(hdr) or r.find_all("th") and len(r.find_all("th")) == len(cells):
                continue
            t = [_text(c) for c in cells]
            if not t[ni]:
                continue
            out.append({"name": t[ni], "pennant": t[pi] if pi is not None else None,
                        "commissioned_raw": t[di], "commissioned": _iso(t[di]),
                        "status_raw": t[si] if si is not None else None,
                        "decommissioned_raw": t[xi] if xi is not None else None,
                        "status": classify(t[si] if si is not None else "", t[xi] if xi is not None else "")})
        if out:
            yield head, out
