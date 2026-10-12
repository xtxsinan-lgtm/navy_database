"""Step 1: harvest class-page link candidates from each country's active-ships list."""
import json, re, sys
from bs4 import BeautifulSoup
from . import wiki
from .countries import LIST_PAGES

CLASS_RE = re.compile(r"(-class|\bclass\b|^Type \d|^Project \d|^Type-\d|submarine|destroyer|frigate|corvette|carrier)", re.I)
SKIP_HEAD = re.compile(r"auxiliar|support|training|replenish|tanker|logistic|research|survey|icebreaker|hospital|"
                       r"tracking|spy|intelligence|salvage|rescue|repair|tug|reserve|future|construction|on order|"
                       r"planned|proposed|authorized|reference|external|see also|image|bibliograph|misc|engineering|"
                       r"landing craft|landing crafts|barge|hovercraft|air-cushion|coast guard|submersible|drone mother|"
                       r"patrol vessel|survey|oceanograph|cable|sail|museum|historic", re.I)


def harvest():
    out = []
    for country, pages in LIST_PAGES.items():
        for page in pages:
            h, rev = wiki.html(page)
            soup = BeautifulSoup(h, "lxml")
            head = ""
            for el in soup.find_all(["h2", "h3", "h4", "a"]):
                if el.name in ("h2", "h3", "h4"):
                    head = el.get_text(" ", strip=True)
                    continue
                href = el.get("href", "")
                if not href.startswith("/wiki/") or ":" in href[6:]:
                    continue
                title = el.get("title") or ""
                if not title or not CLASS_RE.search(title) or SKIP_HEAD.search(head):
                    continue
                out.append({"country": country, "heading": head, "title": title, "list_rev": rev})
    seen, uniq = set(), []
    for o in out:
        k = (o["country"], o["title"])
        if k not in seen:
            seen.add(k); uniq.append(o)
    return uniq


if __name__ == "__main__":
    res = harvest()
    json.dump(res, open("data/candidates.json", "w"), ensure_ascii=False, indent=1)
    from collections import Counter
    print(Counter(r["country"] for r in res))
