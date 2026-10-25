"""Scan library OCR (metadata.json) for strike-related terms, per page."""
import json, re, glob, sys
from pathlib import Path

KW = re.compile(r"strik|walk-?out|walked out|boycott|picket|labou?r|workers|coolie|general strike|"
                r"unemploy|trade union|union|agitat|shameen|shakee|shanghai.{0,20}(riot|trouble|affair)|"
                r"strikers|lock-?out|wages|mill hands|mutiny", re.I)
STRONG = re.compile(r"strik|walk-?out|walked out|boycott|picket|lock-?out|general strike", re.I)

rows = []
for d in sorted(glob.glob("data/raw/hkpl/china_mail_june_july_1925/NPCM*")):
    m = json.load(open(Path(d) / "metadata.json", encoding="utf-8"))
    for p in m["ocrList"]:
        t = p["ocrContent"] or ""
        rows.append((Path(d).name[:12], p["sequence"], len(t), len(STRONG.findall(t)), len(KW.findall(t))))
json.dump(rows, open("agent-sandbox/strike_scan.json", "w"))
print("pages:", len(rows), "avg chars/page:", sum(r[2] for r in rows)//len(rows))
print("pages with strong hit:", sum(1 for r in rows if r[3]), " any kw:", sum(1 for r in rows if r[4]))
by = {}
for e, s, n, st, k in rows:
    by.setdefault(e, [0, 0, 0]); by[e][0] += 1; by[e][1] += bool(st); by[e][2] += st
for e, (n, h, c) in by.items():
    print(e, f"pages={n} strong_pages={h} hits={c}")
