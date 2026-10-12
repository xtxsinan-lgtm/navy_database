"""Heuristic parsing of free-text infobox fields into structured values.

Everything extracted keeps its raw text next to it so results can be audited.
"""
import re
import mwparserfromhell as mw

CONV = re.compile(r"\{\{\s*(?:convert|cvt)\s*\|\s*([\d.,]+)\s*(?:\|\s*(?:–|-|to|and)\s*\|\s*([\d.,]+))?\s*\|\s*([A-Za-z]+)[^}]*\}\}", re.I)
REF = re.compile(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>|<!--.*?-->", re.S | re.I)
UNIT_T = {"t": 1.0, "mt": 1.0, "tonne": 1.0, "tonnes": 1.0, "lt": 1.016, "st": 0.9072, "ton": 1.0, "tons": 1.0}


def plain(raw):
    """Wikitext -> readable text, keeping {{convert}} numbers and bullet line breaks."""
    s = REF.sub("", raw or "")
    s = re.sub(r"\[\[(?:[^\]|\[]*\|)([^\]\[]*)\]\]", r"\1", s)
    s = re.sub(r"\[\[([^\]\[|]*)\]\]", r"\1", s)
    s = CONV.sub(lambda m: f"{m.group(1)}{'-' + m.group(2) if m.group(2) else ''} {m.group(3)}", s)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"\{\{\s*(?:plainlist|ubl|unbulleted list|flatlist|hlist)\s*\|", "\n", s, flags=re.I)
    s = re.sub(r"\n?\s*(\*+|#+|:+\*+)\s*", lambda m: "\n" + ("  " * (len(m.group(1)) - 1)) + "- ", s)
    s = mw.parse(s).strip_code(normalize=True, collapse=True)
    s = s.replace("]]", "").replace("}}", "")
    s = re.sub(r"\[\[(?:[^\]|\n]*\|)?", "", s)
    s = re.sub(r"'{2,}", "", s)
    lines = [re.sub(r"[ \t]+", " ", l).rstrip() for l in s.splitlines()]
    return "\n".join(l for l in lines if l.strip())


def num(x):
    return float(x.replace(",", ""))


def displacement(raw):
    """-> (tonnes or None, basis, text). Picks the largest full-load figure (submerged for submarines)."""
    txt = plain(raw)
    cands = []
    for m in re.finditer(r"([\d]{1,3}(?:,\d{3})+|\d{3,6}(?:\.\d+)?)(?:\s*[-–]\s*([\d,]{3,}))?\s*(tonnes|tons|ton|t|LT|ST|MT)\b", txt, re.I):
        val = num(m.group(2) or m.group(1))
        unit = UNIT_T.get(m.group(3).lower(), 1.0)
        ctx = txt[max(0, m.start() - 60):m.end() + 40].lower()
        basis = ("full" if re.search(r"full|loaded|deep", ctx) else
                 "submerged" if "submerged" in ctx else
                 "standard" if re.search(r"standard|light|surfaced|empty", ctx) else "other")
        cands.append((val * unit, basis))
    for want in ("full", "submerged", "other", "standard"):
        pool = [v for v, b in cands if b == want]
        if pool:
            return round(max(pool)), want, txt
    return None, None, txt


def years(raw):
    return [int(y) for y in re.findall(r"\b(19[4-9]\d|20[0-3]\d)\b", plain(raw))]


def items(raw):
    out = [re.sub(r"^\s*-\s*", "", l).strip() for l in plain(raw).splitlines() if len(l.strip()) > 2]
    return [i for i in out if not (len(i) < 70 and re.search(r":\s*-?\s*$", i) and not re.search(r"\d|VLS|cell", i))]


RADAR_WORDS = re.compile(r"radar|AESA|phased array|PESA|SPY-|SPG-|SPS-|Furke|Poliment|Fregat|MR-\d|3D|search|fire.control|FCS", re.I)
SONAR_ONLY = re.compile(r"^(?:.*\b(?:sonar|ESM|ECM|EW|electronic warfare|decoy|jammer|IRST|infrared|optronic|combat system|CMS|datalink|link)\b)(?!.*radar)", re.I)
MODEL = re.compile(r"(AN/[A-Z]{3}-\d+[A-Z]*(?:\([A-Z]\)\d*)?|Type\s?\d{2,4}[A-Z]?(?:/[A-Z0-9]+)?|"
                   r"[A-Z]{2,}[-/ ]?\d{2,4}[A-Za-z]*(?:-\d+[A-Za-z]*)?|[A-Z][a-z]+[- ]?\d[A-Za-z0-9-]*|"
                   r"\d[A-Z]\d{1,3}[A-Z]?(?:-\d+)?|[A-Z]{3,}[A-Za-z0-9]*)")


def radars(raw):
    out = []
    for it in items(raw):
        if not RADAR_WORDS.search(it) or SONAR_ONLY.match(it):
            continue
        m = MODEL.search(it)
        role = ("fire-control" if re.search(r"fire.control|illuminat|tracking", it, re.I) else
                "air-search" if re.search(r"air.search|3D|volume|multi.?function|multifunction|AESA|phased", it, re.I) else
                "surface-search" if re.search(r"surface|navigation|i-band|x-band|j-band", it, re.I) else None)
        out.append({"model": (m.group(1).strip() if m else it[:80]), "role": role, "raw": it})
    return out


VLS_MODEL = re.compile(r"(H/AKJ-16|Mk\.?\s?41|Mk\.?\s?57|Mk\.?\s?48|Mk\.?\s?45 VLS|Sylver\s?[A-Z]?\d{2}|SYLVER\s?[A-Z]?\d{2}|UKSK|3S[- ]?14M?|3S[- ]?24|K-?VLS|KVLS|"
                       r"Redut|Polyment|Poliment|H/AJK-16|GJB 5860-2006|VL MICA|VL-?MICA|VLS Mk\s?\d+|S-?VLS|MBDA|[A-Z]{2,}VLS)", re.I)
CELLS = [re.compile(r"(\d+)\s*[×xX]\s*(\d+)[- ]?cell", re.I), re.compile(r"(\d+)[- ]?cells?", re.I), re.compile(r"(\d+)\s*[×xX]\s*(?:VLS|vertical)", re.I)]


VLS_LINE = re.compile(r"\bVLS\b|PVLS|vertical(?:ly)? launch|vertically|UKSK|Sylver|SYLVER|Redut|\bVPM\b|3S[- ]?14|3S[- ]?24|K-?VLS|GJB 5860|H/AKJ-16|Mk\.? ?41|Mk\.? ?57|revolver|Polyment|Poliment|VL MICA|S-VLS", re.I)
NOT_VLS = re.compile(r"\bCIWS\b|close.in|Rolling Airframe|\bRAM\b|Sea ?RAM|HQ-10|HHQ-10|HQ-7|FL-3000|launcher for .*MANPADS|decoy|chaff", re.I)


def vls(raw):
    out = []
    for it in items(raw):
        if not VLS_LINE.search(it) or (NOT_VLS.search(it) and not re.search(r"\bVLS\b|vertical|Mk\.? ?41|Mk\.? ?57", it, re.I)):
            continue
        cells = None
        it_n = re.sub(r"GJB\s*5860-2006|\b(?:Mk|Type)\s?\.?\s?\d+\b|\bK-?VLS\b", lambda m: m.group().replace("-", "_").replace(" ", "_"), it)
        tot = re.search(r"\(\s*(?:total\s+)?(\d+)\s*(?:total\s+|launch\s+)?cells?\s*(?:total)?\)", it_n, re.I)
        m = CELLS[0].search(it_n)
        if tot:
            cells = int(tot.group(1))
        elif m:
            cells = int(m.group(1)) * int(m.group(2))
        else:
            m = (re.search(r"(\d+)\s*[×x]?\s*(?:[\w/.\-]+\s+){0,5}?(?:VLS\s+)?cells?", it_n, re.I) or CELLS[1].search(it_n)
                 or CELLS[2].search(it_n) or re.search(r"(\d+)\s*[×x]?\s*(?:vertical|VLS)", it_n, re.I))
            if m:
                cells = int(m.group(1))
        mm = VLS_MODEL.search(it)
        out.append({"model": mm.group(1) if mm else "VLS", "cells": cells, "raw": it})
    return out


CATS = [("ciws", r"CIWS|close.in|Phalanx|Goalkeeper|AK-630|Kashtan|Pantsir|Type 730|Type 1130|RAM\b|Sea ?RAM"),
        ("torpedo", r"torpedo|Mk 32|Mk 46|Mk 54|Mk 48|ASROC|A244|MU90|Yu-\d|RBU"),
        ("gun", r"\bgun\b|\bmm\b|inch|cal(?:iber|ibre)?\b|/\d{2}\b|OTO|Bofors|Oerlikon|AK-\d|AK-\d+M"),
        ("aircraft", r"helicopter|aircraft|\bUAV\b|Seahawk|Ka-\d|Z-\d|Merlin|Lynx|Sea King|Dhruv|MH-60|Fighter|F-35|Rafale|MiG|Su-"),
        ("missile", r"missile|SAM|SSM|ASM|Harpoon|Exocet|Tomahawk|Standard|SM-\d|ESSM|Aster|Kalibr|Oniks|Yakhont|Club|Klub|YJ-|HHQ|HQ-|C-8\d\d|BrahMos|Barak|MICA|Naval Strike|NSM|Sea Sparrow|RIM-|AGM-|Hellfire|Type 90|Type 12|Type 17")]


def weapons(raw):
    out = []
    for it in items(raw):
        if re.search(r"\bVLS\b|vertical launch|\bcells?\b", it, re.I) and not re.match(r"\d+\s*[×x]\s", it):
            continue
        m = re.match(r"(?:\w+\s*:\s*)?(\d+)\s*[×xX]\s*(.+)", it)
        qty, name = (int(m.group(1)), m.group(2).strip()) if m else (None, it)
        if len(name) < 3 or name.endswith(":") or re.match(r"^(batch|flight|block|project|type)[^×]*:$", name, re.I):
            continue
        cat = next((c for c, pat in CATS if re.search(pat, name, re.I)), "other")
        out.append({"name": name[:160], "qty": qty, "category": cat, "raw": it})
    return out


def first(ib, key):
    return ib.get(key) or next((v for k, v in ib.items() if k.split("__")[0] == key), None)
