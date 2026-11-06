"""How many node pairs have enough claims for a missing edge to mean anything? Simple null model: expected claims a -> b =
out(a) * in(b) / total claims, as if causes and effects paired at random. Zero observed at expected >= 3 is a ~5% event per pair."""
import json, re, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
V = Path(__file__).resolve().parent / "viewer"
for slug in ("event-030", "event-035", "topic-030", "topic-035"):
    html = (V / f"{slug}.html").read_text(encoding="utf-8")
    g = json.loads(re.search(r'<script id="graph-data" type="application/json">(.*?)</script>', html, re.S)[1].replace("<\/", "</"))
    label = {n["id"]: n["label"] for n in g["nodes"]}
    out, inn, seen = Counter(), Counter(), set()
    for e in g["edges"]:
        out[e["source"]] += len(e["evidence"]); inn[e["target"]] += len(e["evidence"]); seen.add((e["source"], e["target"]))
    N = sum(out.values()); n = len(label)
    exp = sorted(((out[a] * inn[b] / N, a, b) for a in out for b in inn if a != b and (a, b) not in seen), reverse=True)
    print(f"{slug}: {n} nodes, {n * (n - 1):,} possible arrows, {len(seen)} present ({100 * len(seen) / (n * (n - 1)):.2f}%)"
          f" | missing with expected >=1: {sum(e >= 1 for e, *_ in exp)}, >=2: {sum(e >= 2 for e, *_ in exp)}, >=3: {sum(e >= 3 for e, *_ in exp)} | top {exp[0][0]:.2f}")
    if slug in ("event-035", "topic-035"):
        for e, a, b in exp[:7]:
            print(f"    {e:.1f}  {label[a][:48]} -> {label[b][:48]}")
