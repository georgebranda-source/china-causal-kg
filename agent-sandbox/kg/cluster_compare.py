import json, sys, random
from collections import Counter
from pathlib import Path
import numpy as np
from sklearn.cluster import AgglomerativeClustering, HDBSCAN
sys.stdout.reconfigure(encoding="utf-8")
OUT = Path(__file__).resolve().parent / "out"
T = json.load(open(OUT / "embed_texts.json", encoding="utf-8"))
M = np.load(OUT / "embed_qwen_instruct.npy").astype(np.float64)
D = np.clip(1 - M @ M.T, 0, 2); np.fill_diagonal(D, 0)
rows = [json.loads(l) for l in open(OUT / "normalised.jsonl", encoding="utf-8")]
idx = {t: i for i, t in enumerate(T)}
def stats(l):
    c = Counter(l); multi = {k: v for k, v in c.items() if v >= 2 and k >= 0}
    s = sorted(multi.values(), reverse=True)
    single = sum(v == 1 for v in c.values()) + int((np.array(l) < 0).sum()) * (1 if -1 in c else 0) - (1 if c.get(-1) == 1 else 0)
    p = [(l[idx[r["cause_description"]]], l[idx[r["effect_description"]]]) for r in rows]
    loops = sum(a == b and a >= 0 for a, b in p)
    return f"groups {len(s)}, in groups {sum(s)}, singletons {len(T) - sum(s)}, largest {s[:6]}, median {int(np.median(s))}, self-loops {loops}"
res = {}
for t in (0.25, 0.30, 0.35, 0.40):
    l = AgglomerativeClustering(n_clusters=None, metric="precomputed", linkage="average", distance_threshold=t).fit_predict(D)
    res[t] = l; print("agglomerative", t, stats(l), flush=True)
print("hdbscan 3 eom", stats(HDBSCAN(min_cluster_size=3, min_samples=1, metric="precomputed", copy=True).fit_predict(D)))
l = res[0.35]
g = {}
for t, k in zip(T, l): g.setdefault(int(k), []).append(t)
big = sorted(g.values(), key=len, reverse=True)
print("\n=== agglomerative 0.35: largest 8")
for v in big[:8]:
    print(f"\n[{len(v)}]"); [print("   ", t[:100]) for t in random.Random(1).sample(v, min(6, len(v)))]
print("\n=== mid-sized sample")
mid = [v for v in big if 3 <= len(v) <= 6]
for v in random.Random(2).sample(mid, 6):
    print(f"\n[{len(v)}]"); [print("   ", t[:100]) for t in v[:5]]
