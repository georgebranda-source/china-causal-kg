"""Step 2 of the demo: cluster the cause/effect phrases in relations.jsonl into event nodes.

Embeds each distinct phrase with bge-small-en-v1.5 (fastembed, ONNX on CPU) and clusters with
scikit-learn's HDBSCAN. Phrases HDBSCAN leaves as noise become their own single-phrase cluster.

    agent-sandbox/.venv-kg/Scripts/python agent-sandbox/demo_kg/cluster.py

Writes clusters.json next to this file: {"phrase_to_cluster": {...}, "clusters": {id: [phrases]}}.
"""

import json
from pathlib import Path

import numpy as np
import truststore

truststore.inject_into_ssl()  # use the Windows cert store (plain certifi fails on this machine)

from fastembed import TextEmbedding
from sklearn.cluster import HDBSCAN

HERE = Path(__file__).resolve().parent
MODEL = "BAAI/bge-small-en-v1.5"


def main():
    rels = [json.loads(line) for line in open(HERE / "relations.jsonl", encoding="utf-8")]
    phrases = sorted({p for r in rels for p in (r["cause"], r["effect"])})

    vecs = np.array(list(TextEmbedding(MODEL).embed(phrases)))
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)  # euclidean on unit vectors ~ cosine

    labels = HDBSCAN(min_cluster_size=2, min_samples=1, cluster_selection_epsilon=0.0).fit_predict(vecs)

    # noise (-1) -> singleton clusters numbered after the real ones
    next_id = labels.max() + 1
    for i, lab in enumerate(labels):
        if lab == -1:
            labels[i] = next_id
            next_id += 1

    clusters = {}
    for phrase, lab in zip(phrases, labels):
        clusters.setdefault(f"c{lab}", []).append(phrase)

    out = {
        "model": MODEL,
        "phrase_to_cluster": {p: f"c{lab}" for p, lab in zip(phrases, labels)},
        "clusters": clusters,
    }
    (HERE / "clusters.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    multi = {k: v for k, v in clusters.items() if len(v) > 1}
    print(f"{len(phrases)} phrases -> {len(clusters)} clusters ({len(multi)} with 2+ phrases)")
    for k, v in sorted(multi.items(), key=lambda kv: -len(kv[1])):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
