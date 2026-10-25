"""Compare screening flags to truth from PaddleOCR-VL text on pages that have both."""
import csv, re, sys
from collections import Counter
from pathlib import Path
from rapidfuzz.distance import Levenshtein
sys.path.insert(0, "agent-sandbox")
import strike_screen as s

TRUTH = re.compile(r"strik|walk-?out|walked out|boycott|picket|lock-?out", re.I)
rows = {r["page"]: r for r in csv.DictReader(open(s.OUT_CSV, encoding="utf-8"))}
tp = fn = fp = tn = 0
for f in sorted(s.VL_DIR.glob("page_*NPCM*.md")):
    r = rows.get(f.stem)
    if not r: continue
    truth = bool(TRUTH.search(f.read_text(encoding="utf-8")))
    flag = r["flag"] == "True"
    tp += truth and flag; fn += truth and not flag; fp += flag and not truth; tn += (not flag) and (not truth)
    if truth != flag or truth: print(f"{f.stem[5:9]} {f.stem[10:22]} truth={truth} flag={flag} score={r['score']} core={r['core']}")
print(f"tp={tp} fn={fn} fp={fp} tn={tn}")
# what tokens trigger 'picket'?
c = Counter()
for p in Path("agent-sandbox/ocr_fast_out").glob("page_*.txt"):
    for t in re.findall(r"[a-z]+", p.read_text(encoding="utf-8").lower()):
        if t not in ("picket","pickets","picketing") and any(Levenshtein.distance(v,t)<=s.tol(v) for v in s.CORE["picket"]): c[t]+=1
print(c.most_common(12))
