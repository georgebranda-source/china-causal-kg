"""Cluster the event descriptions with HDBSCAN. Usage: python kg/cluster.py            # compare settings
                                                     python kg/cluster.py 3 leaf       # write kg/out/clusters.json"""
import json, sys
from collections import Counter
from pathlib import Path
import numpy as np
from sklearn.cluster import HDBSCAN
sys.stdout.reconfigure(encoding="utf-8")
OUT = Path(__file__).resolve().parent / "out"
T = json.load(open(OUT / "embed_texts.json", encoding="utf-8"))
M = np.load(OUT / "embed_qwen_instruct.npy").astype(np.float64)
D = np.clip(1 - M @ M.T, 0, 2)
np.fill_diagonal(D, 0)
rows = [json.loads(l) for l in open(OUT / "normalised.jsonl", encoding="utf-8")]


def run(size, method, samples=1):
    return HDBSCAN(min_cluster_size=size, min_samples=samples, metric="precomputed", cluster_selection_method=method, copy=True).fit_predict(D)


def stats(labels):
    idx = {t: i for i, t in enumerate(T)}
    sizes = sorted(Counter(l for l in labels if l >= 0).values(), reverse=True)
    node = lambda t: labels[idx[t]]
    pairs = [(node(r["cause_description"]), node(r["effect_description"])) for r in rows]
    loops = sum(a == b and a >= 0 for a, b in pairs)
    both = sum(a >= 0 and b >= 0 for a, b in pairs)
    return dict(clusters=len(sizes), noise=int((labels < 0).sum()), largest=sizes[:5], median=int(np.median(sizes)) if sizes else 0, self_loops=loops, claims_both_clustered=both)


if len(sys.argv) > 2:
    size, method = int(sys.argv[1]), sys.argv[2]
    labels = run(size, method)
    groups = {}
    for t, l in zip(T, labels):
        groups.setdefault(int(l), []).append(t)
    (OUT / "clusters.json").write_text(json.dumps({"min_cluster_size": size, "method": method, "embedding": "qwen3-embedding:8b, instruction",
        "stats": stats(labels), "clusters": {str(k): v for k, v in sorted(groups.items())}}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(stats(labels))
    for k, v in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        if k < 0: continue
        print(f"\n[{k}] {len(v)}")
        for t in v[:6]: print("   ", t[:105])
else:
    for size in (2, 3, 4, 5, 8):
        for method in ("eom", "leaf"):
            print(size, method, stats(run(size, method)), flush=True)
