"""Group descriptions into topic nodes. Usage: python kg/cluster_final.py [cosine distance threshold, default 0.30]

Average-link agglomerative clustering on qwen3-embedding:8b vectors with the topic instruction. Writes kg/out/nodes.json, with each
node's most central description as a provisional label, and kg/out/edges.json, with the claims behind each cause -> effect link."""
import json, re, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from sklearn.cluster import AgglomerativeClustering
sys.stdout.reconfigure(encoding="utf-8")
OUT = Path(__file__).resolve().parent / "out"
THRESHOLD = float(sys.argv[1]) if len(sys.argv) > 1 else 0.30
T = json.load(open(OUT / "embed_texts.json", encoding="utf-8"))
M = np.load(OUT / "embed_qwen_instruct.npy").astype(np.float64)
D = np.clip(1 - M @ M.T, 0, 2); np.fill_diagonal(D, 0)
labels = AgglomerativeClustering(n_clusters=None, metric="precomputed", linkage="average", distance_threshold=THRESHOLD).fit_predict(D)
members = defaultdict(list)
for i, l in enumerate(labels):
    members[int(l)].append(i)
order = sorted(members, key=lambda k: -len(members[k]))
node_of, nodes = {}, []
for n, k in enumerate(order):
    ids = members[k]
    centre = ids[int(np.argmin(D[np.ix_(ids, ids)].sum(1)))]
    nodes.append({"node": n, "label": T[centre], "size": len(ids), "members": [T[i] for i in ids]})
    for i in ids:
        node_of[T[i]] = n
rows = [json.loads(l) for l in open(OUT / "normalised.jsonl", encoding="utf-8")]
edges, loops = defaultdict(list), []
for r in rows:
    a, b = node_of[r["cause_description"]], node_of[r["effect_description"]]
    ev = {k: r[k] for k in ("article_id", "page", "date", "headline", "quote", "cause", "effect", "cause_description", "effect_description")}
    (loops.append({"node": a, **ev}) if a == b else edges[(a, b)].append(ev))
out = [{"source": a, "target": b, "claims": v} for (a, b), v in sorted(edges.items(), key=lambda kv: -len(kv[1]))]
(OUT / "nodes.json").write_text(json.dumps({"threshold": THRESHOLD, "method": "agglomerative, average link, cosine", "nodes": nodes}, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "edges.json").write_text(json.dumps({"edges": out, "self_loops": loops}, ensure_ascii=False, indent=1), encoding="utf-8")
deg = Counter()
for e in out:
    deg[e["source"]] += len(e["claims"]); deg[e["target"]] += len(e["claims"])
used = set(deg)
print(f"threshold {THRESHOLD}: {len(nodes)} nodes ({sum(n['size'] >= 2 for n in nodes)} groups, {sum(n['size'] == 1 for n in nodes)} singletons)")
print(f"claims {len(rows)}: {sum(len(e['claims']) for e in out)} on {len(out)} edges, {len(loops)} self-loops; edges with 2+ claims {sum(len(e['claims']) >= 2 for e in out)}; nodes in graph {len(used)}")
print("\nlargest nodes")
for n in nodes[:14]:
    print(f"  {n['node']:>3} size {n['size']:>3} claims {deg[n['node']]:>3}  {n['label'][:88]}")
print("\ntop edges")
for e in out[:10]:
    print(f"  {len(e['claims'])}  {nodes[e['source']]['label'][:50]} -> {nodes[e['target']]['label'][:50]}")
print("\nself-loops by node", Counter(l["node"] for l in loops).most_common(6))
print("self-loop sample")
for l in loops[:60:12]:
    print(f"  {l['cause_description'][:62]} -> {l['effect_description'][:62]}")
opp = re.compile(r"resum|return to work|reopen|re-open|ends?\b|lifted|collapse|improv|revival", re.I)
print("\npossible mixed nodes")
for n in nodes[:14]:
    m = [t for t in n["members"] if opp.search(t)]
    if m:
        print(f"  node {n['node']} ({n['size']}): {len(m)} e.g. {m[0][:80]}")
