"""Nearest neighbours and opposite-pair distances for each embedding setup."""
import json, re, sys, random
from pathlib import Path
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
OUT = Path(__file__).resolve().parent / "out"
T = json.load(open(OUT / "embed_texts.json", encoding="utf-8"))
E = {n: np.load(OUT / f"embed_{n}.npy") for n in ("qwen_instruct", "qwen_plain", "bge")}
for n, m in E.items():
    s = m @ m.T; np.fill_diagonal(s, -1)
    iu = np.triu_indices(len(T), 1)
    print(n, "pairwise cosine: median %.3f, p99 %.3f; nearest neighbour: median %.3f" % (np.median(s[iu]), np.percentile(s[iu], 99), np.median(s.max(1))))
random.seed(3)
pick = random.sample(range(len(T)), 8) + [i for i, t in enumerate(T) if t.startswith("A strike is under way")][:1]
for i in pick:
    print("\n#", T[i])
    for n in ("qwen_instruct", "bge"):
        s = E[n] @ E[n][i]; s[i] = -1
        print(" ", n)
        for j in np.argsort(-s)[:3]:
            print(f"    {s[j]:.2f} {T[j][:100]}")
PAIRS = [(r"market.*(clos|shut)", r"market.*(reopen|re-open|resum)"), (r"strike (begins|starts|spreads|continues)|go on strike|join", r"strike (ends|collapses)|return to work|resume work"),
         (r"\bboycott.*(begins|imposed|declared|continues)", r"\bboycott.*(ends|lifted|called off)"), (r"bank.*(clos|shut)", r"bank.*(open|reopen)"), (r"shops.*(clos|shut)", r"shops.*(open|reopen)"),
         (r"(prices?).*(rise|increase|go up|high)", r"(prices?).*(fall|drop|reduc|lower)"), (r"restrict.*(impose|place|introduc)", r"restrict.*(lift|lighten|remov|relax)")]
print("\n## candidate opposites")
for a, b in PAIRS:
    A = [t for t in T if re.search(a, t, re.I)]; B = [t for t in T if re.search(b, t, re.I)]
    print(a[:30], len(A), "|", b[:30], len(B))
    for t in A[:3]: print("   +", t[:95])
    for t in B[:3]: print("   -", t[:95])
