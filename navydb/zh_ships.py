"""Chinese Wikipedia: per-ship rows for PLAN classes -> data/ships_zh.json."""
import json, pathlib, re
from . import wiki, ships

ROOT = pathlib.Path(__file__).resolve().parent.parent
# en class page -> candidate zh titles (first existing page wins)
ZH = {
    "Chinese aircraft carrier Liaoning": ["辽宁号航空母舰", "辽宁舰"],
    "Chinese aircraft carrier Shandong": ["山东号航空母舰", "山东舰"],
    "Chinese aircraft carrier Fujian": ["福建号航空母舰", "福建舰"],
    "Type 055 destroyer": ["055型导弹驱逐舰"], "Type 052D destroyer": ["052D型导弹驱逐舰"],
    "Type 052C destroyer": ["052C型导弹驱逐舰"], "Type 052B destroyer": ["052B型导弹驱逐舰"],
    "Type 051C destroyer": ["051C型导弹驱逐舰"], "Chinese destroyer Shenzhen": ["051B型导弹驱逐舰"],
    "Sovremenny-class destroyer": ["现代级导弹驱逐舰", "现代级驱逐舰"], "Type 052 destroyer": ["052型导弹驱逐舰"],
    "Type 054A frigate": ["054A型导弹护卫舰"], "Type 054B frigate": ["054B型导弹护卫舰"],
    "Type 054 frigate": ["054型导弹护卫舰"], "Type 053H3 frigate": ["053H3型导弹护卫舰"],
    "Type 056 corvette": ["056型轻型护卫舰", "056型护卫舰"], "Type 022 missile boat": ["022型导弹艇"],
    "Type 037 corvette": ["037型猎潜艇"],
    "Type 094 submarine": ["094型核潜艇"], "Type 093 submarine": ["093型核潜艇"], "Type 091 submarine": ["091型核潜艇"],
    "Type 039 submarine": ["039型潜艇"], "Type 039A submarine": ["039A型潜艇"], "Type 035 submarine": ["035型潜艇"],
    "Kilo-class submarine": ["基洛级潜艇"],
    "Type 075 landing helicopter dock": ["075型两栖攻击舰"], "Type 071 amphibious transport dock": ["071型船坞登陆舰"],
    "Type 072A landing ship": ["072A型坦克登陆舰", "072A型登陆舰"], "Type 072III landing ship": ["072III型登陆舰", "072III型坦克登陆舰"],
    "Type 074A landing ship": ["074A型登陆舰", "074A型中型登陆舰"],
}


def main():
    out, rep = [], []
    for en, cands in ZH.items():
        got = None
        for t in cands:
            text, rev = wiki.wikitext(t, "zh")
            if text:
                got = (t, rev); break
        if not got:
            rep.append((en, "no zh page")); print(en, "NO PAGE", flush=True); continue
        h, rev = wiki.html(got[0], "zh")
        n = 0
        for head, rows in ships.tables(h, any_class=True):
            if re.search(r"退役|规划|计划|参考|外销|出口", head):
                continue
            for r in rows:
                out.append({"class_page": en, "zh_page": got[0], "rev": rev, "section": head, **r}); n += 1
        rep.append((en, got[0], n)); print(en, got[0], n, flush=True)
    (ROOT / "data" / "ships_zh.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print("DONE", len(out))


if __name__ == "__main__":
    main()
