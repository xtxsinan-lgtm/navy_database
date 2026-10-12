"""Extract per-ship rows (name / pennant / commissioning date) from wikitables."""
import re
from bs4 import BeautifulSoup

NAME_H = re.compile(r"^(name|ship|vessel|boat|hull|unit|舰名|艦名|名称|名稱)", re.I)
PEND_H = re.compile(r"舷号|舷號|pennant|hull|hull no|number|^no\.?$|^id$|identification|^p\.? ?no|designation", re.I)
DATE_H = re.compile(r"服役|服役时间|入役|入列|commission|in service|service entry|entered service|entry into service|enter service|"
                    r"^service$|^date$|^accepted|^delivered|^completed", re.I)
SKIP_H = re.compile(r"开工|下水|退役|除役|laid down|launched|builder|shipyard|decommission|fate|retired", re.I)
DATE_RE = re.compile(r"(\d{1,2}\s+\w+\s+(?:19|20)\d\d|\w+\s+\d{1,2},\s+(?:19|20)\d\d|\w+\s+(?:19|20)\d\d|(?:19|20)\d\d(?:-\d\d(?:-\d\d)?)?)")


def _text(c):
    for s in c.find_all(["sup", "style"]):
        s.decompose()
    t = re.sub(r"\s+", " ", c.get_text(" ", strip=True))
    return re.sub(r"\s*\[\s*[\w ]{1,6}\s*\]", "", t).strip()


STATUS_H = re.compile(r"^status|^fate|^current status|现状|現狀|状态|狀態", re.I)
DECOM_H = re.compile(r"decommission|retired|withdrawn|stricken", re.I)
ACTIVE_RE = re.compile(r"现役|現役|服役中|\b(active|in service|in commission|commissioned|operational|serving|undergoing|refit|reserve fleet in)\b", re.I)
INACTIVE_RE = re.compile(r"退役|除役|沉没|沉沒|报废|報廢|出售|转让|轉讓|decommission|retired|scrapp|sunk|museum|preserved|stricken|transferred|sold|broken up|"
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
    zm = re.search(r"((?:19|20)\d\d)\s*年\s*(?:(\d{1,2})\s*月)?\s*(?:(\d{1,2})\s*日)?", raw)
    if zm:
        y, m, d = zm.group(1), zm.group(2), zm.group(3)
        return f"{y}-{int(m):02d}-{int(d):02d}" if m and d else (f"{y}-{int(m):02d}" if m else y)
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


def _grid(table):
    """Expand rowspan/colspan into a rectangular grid of (text, is_th) per row."""
    grid, spans = [], {}
    for tr in table.find_all("tr"):
        row, col = [], 0
        cells = tr.find_all(["td", "th"], recursive=False)
        it = iter(cells)
        while True:
            while col in spans and spans[col][1] > 0:
                row.append(spans[col][0]); spans[col][1] -= 1; col += 1
            c = next(it, None)
            if c is None:
                break
            cell = (_text(c), c.name == "th")
            rs = int(re.sub(r"\D", "", c.get("rowspan") or "1") or 1)
            cs = int(re.sub(r"\D", "", c.get("colspan") or "1") or 1)
            for _ in range(cs):
                row.append(cell)
                if rs > 1:
                    spans[col] = [cell, rs - 1]
                col += 1
        while col in spans and spans[col][1] > 0:
            row.append(spans[col][0]); spans[col][1] -= 1; col += 1
        grid.append(row)
    return grid


def tables(html, any_class=False):
    """Yield (section_heading, [row dicts]) for wikitables that have a commissioning-date column."""
    soup = BeautifulSoup(html, "lxml")
    head = ""
    for el in soup.find_all(["h2", "h3", "h4", "table"]):
        if el.name != "table":
            head = el.get_text(" ", strip=True); continue
        cls = " ".join(el.get("class") or [])
        if "wikitable" not in cls and not (any_class and not re.search(r"navbox|infobox|ambox|metadata|vcard", cls)):
            continue
        grid = _grid(el)
        def _looks_header(r):
            return sum(1 for t, _ in r if t and (NAME_H.search(t) or DATE_H.search(t) or PEND_H.search(t) or STATUS_H.search(t) or t == "序号")) >= 3

        hi = next((i for i, r in enumerate(grid[:4]) if sum(1 for _, th in r if th) >= 3 or _looks_header(r)), None)
        if hi is None:
            continue
        hdr = [t for t, _ in grid[hi]]
        di = next((i for i, h in enumerate(hdr) if DATE_H.search(h) and not SKIP_H.search(h)), None)
        ni = next((i for i, h in enumerate(hdr) if NAME_H.search(h)), None)
        pi0 = next((i for i, h in enumerate(hdr) if re.search(r"舷号|舷號", h)), None)
        if ni is None and pi0 is not None:
            ni = pi0        # e.g. PLAN submarines: only hull numbers, no names
        if di is None or ni is None:
            continue
        pi = next((i for i, h in enumerate(hdr) if re.search(r"舷号|舷號|pennant|hull|^p\.? ?no|identification|designation", h, re.I) and i != ni), None)
        if pi is None:
            pi = next((i for i, h in enumerate(hdr) if PEND_H.search(h) and i != ni), None)
        ci = next((i for i, h in enumerate(hdr) if re.match(r"^class", h, re.I) and i != ni), None)
        si = next((i for i, h in enumerate(hdr) if STATUS_H.search(h)), None)
        xi = next((i for i, h in enumerate(hdr) if DECOM_H.search(h)), None)
        out, sub = [], ""
        for r in grid[hi + 1:]:
            if r and len({t for t, _ in r}) == 1 and r[0][0] and (len(r) != len(hdr) or len(r) > 2):
                sub = r[0][0]; continue
            if len(r) != len(hdr) or all(th for _, th in r):
                continue
            t = [x for x, _ in r]
            if not t[ni]:
                continue
            out.append({"sub": sub, "name": t[ni], "pennant": t[pi] if pi is not None else None,
                        "commissioned_raw": t[di], "commissioned": _iso(t[di]),
                        "class_raw": t[ci] if ci is not None else None,
                        "status_raw": t[si] if si is not None else None,
                        "decommissioned_raw": t[xi] if xi is not None else None,
                        "status": classify(t[si] if si is not None else "", t[xi] if xi is not None else "")})
        if out:
            yield head, out
