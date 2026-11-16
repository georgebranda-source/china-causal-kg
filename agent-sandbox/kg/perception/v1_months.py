"""Apply the perception anchors and scope rule (graph.py) to the frozen v1 graph (Apr 1925 - Nov 1926), by month.

v1 has no speaker field, so this counts strike-cause claims only, without the British/Chinese split. It reuses v1's stored
event-instruction embeddings (same model, instruction and input format as graph.py); only the anchors are embedded anew.
Writes kg/out/perception/v1_months.md and v1_in_scope_claims.csv.
Usage: .venv-kg/Scripts/python kg/perception/v1_months.py
"""
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import graph as Gr  # noqa: E402

V1 = C.KG / "out" / "combined"  # embeddings and claims behind graph_v1; refilmed duplicates removed as in graph_v1
removed = {r["removed"]["key"] for r in C.load_jsonl(V1 / "refilmed_removed.jsonl")}
rows = [r for r in C.load_jsonl(V1 / "normalised.jsonl") if r["key"] not in removed]
assert len(rows) == 3479, len(rows)
texts = json.loads((V1 / "embed_texts.json").read_text(encoding="utf-8"))
T = np.load(V1 / "embed_qwen_event.npy").astype(np.float64)
idx = {t: i for i, t in enumerate(texts)}
anchor_texts = Gr.STRIKE + [t for v in Gr.ANCHORS.values() for t in v]
A = Gr.embed(anchor_texts)
cats = ["STRIKE"] * len(Gr.STRIKE) + [c for c, v in Gr.ANCHORS.items() for _ in v]


def sims(i):
    out = defaultdict(lambda: -1.0)
    for c, s in zip(cats, T[i] @ A.T):
        out[c] = max(out[c], float(s))
    return dict(out)


out_rows, table = [], {th: defaultdict(Counter) for th in Gr.SENSITIVITY}
months = Counter()
for r in rows:
    m = r["date"][:7]
    months[m] += 1
    es, cs = sims(idx[r["effect_description"]]), sims(idx[r["cause_description"]])
    cs.pop("STRIKE")
    ep = (r.get("effect_place") or "").lower()
    place_ok = any(p in ep for p in Gr.HK_CANTON) or ep.strip() in ("", "unknown")
    for th in Gr.SENSITIVITY:
        if place_ok and Gr.assign(es, th) == "STRIKE":
            cc = Gr.assign(cs, th)
            table[th][m][cc] += 1
            if th == Gr.THRESHOLD:
                out_rows.append({"id": r["key"], "date": r["date"], "headline": r["headline"], "cause_concept": cc,
                                 "effect_place": r.get("effect_place", ""), "quote": r["quote"],
                                 "cause_description": r["cause_description"], "effect_description": r["effect_description"]})

cols = list(Gr.ANCHORS) + ["other"]
lines = ["# Perception anchors applied to v1 (Apr 1925 - Nov 1926), broad scope, no speaker split", ""]
for th in Gr.SENSITIVITY:
    lines += [f"## Threshold {th}", "", "| month | all v1 claims | in scope | " + " | ".join(cols) + " |",
              "|" + "---|" * (len(cols) + 3)]
    for m in sorted(months):
        c = table[th][m]
        lines.append(f"| {m} | {months[m]} | {sum(c.values())} | " + " | ".join(str(c[k]) for k in cols) + " |")
    tot = Counter()
    for c in table[th].values():
        tot.update(c)
    lines += [f"| total | {sum(months.values())} | {sum(tot.values())} | " + " | ".join(str(tot[k]) for k in cols) + " |", ""]
(C.OUT / "v1_months.md").write_text("\n".join(lines), encoding="utf-8")
with open(C.OUT / "v1_in_scope_claims.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out_rows[0]))
    w.writeheader()
    w.writerows(out_rows)
print("\n".join(lines))
