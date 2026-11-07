"""Merge coder output, validate it, and measure agreement on the double-coded claims. Reads tags/output/*.csv; writes tags/claim_tags.csv and tags/agreement.csv.
For double-coded claims the kept row is the one from the coder who had that claim in its own chronological batch."""
import collections as C
import csv
import glob
import json
import re
import sys

from sklearn.metrics import cohen_kappa_score

sys.stdout.reconfigure(encoding="utf-8")
FIELDS = ["relevance", "cause_type", "effect_type", "cause_actor", "effect_actor", "effect_mode", "cause_place", "effect_place", "voice", "stance", "confidence"]
book = open("CODEBOOK.md", encoding="utf-8").read()
valid_tokens = set(re.findall(r"`([A-Za-z_]+)`", book))
overlap = json.load(open("tags/overlap.json"))
ids = [json.loads(l)["id"] for p in sorted(glob.glob("tags/input/batch_*.jsonl")) for l in open(p, encoding="utf-8")]
coded = C.defaultdict(dict)
for p in sorted(glob.glob("tags/output/batch_*.csv")):
    b = int(re.search(r"batch_(\d)", p)[1])
    for r in csv.DictReader(open(p, encoding="utf-8")):
        coded[r["id"]][b] = r
missing = set(ids) - set(coded)
print("input rows", len(ids), "distinct", len(set(ids)), "coded", len(coded), "missing", len(missing))
bad = C.Counter()
for per in coded.values():
    for r in per.values():
        for f in FIELDS:
            if r.get(f) not in valid_tokens:
                bad[(f, r.get(f))] += 1
print("invalid values", bad.most_common(20))
rows = []
for i, per in coded.items():
    home = overlap[i][0] if i in overlap else next(iter(per))
    rows.append(per.get(home) or next(iter(per.values())))
w = csv.DictWriter(open("tags/claim_tags.csv", "w", newline="", encoding="utf-8"), fieldnames=["id"] + FIELDS)
w.writeheader()
w.writerows({k: r.get(k, "") for k in ["id"] + FIELDS} for r in rows)
pairs = [list(per.values()) for i, per in coded.items() if i in overlap and len(per) == 2]
print("double-coded pairs", len(pairs))
out = []
for f in FIELDS[:-1]:
    a = [p[0][f] for p in pairs]
    b = [p[1][f] for p in pairs]
    agree = sum(x == y for x, y in zip(a, b)) / len(a)
    k = cohen_kappa_score(a, b)
    out.append({"field": f, "agreement": round(agree, 3), "kappa": round(k, 3)})
    print(f"{f:14} agreement {agree:.2f} kappa {k:.2f}")
w = csv.DictWriter(open("tags/agreement.csv", "w", newline="", encoding="utf-8"), fieldnames=["field", "agreement", "kappa"])
w.writeheader()
w.writerows(out)
print("low confidence", sum(r["confidence"] == "low" for r in rows), "of", len(rows))
for f in ["relevance", "voice", "stance", "effect_mode"]:
    print(f, C.Counter(r[f] for r in rows).most_common())
