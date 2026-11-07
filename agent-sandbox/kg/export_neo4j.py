"""Export the combined graph as CSV files, one folder per version, in kg/out/graph_v1/<version>/. Works for Python analysis or Neo4j.

Usage (from agent-sandbox/):  .venv-kg/Scripts/python kg/export_neo4j.py
Runs automatically at the end of kg/combine.py, so the folder always holds every finished batch.

Model:
    (:Event)-[:CAUSES {claims, articles, pages, first_date, last_date}]->(:Event)   one per arrow, cause and effect in different groups
    (:Event)-[:SELF_LOOP {claims, articles, pages, first_date, last_date}]->(:Event) cause and effect in the same group
    (:Claim)-[:HAS_CAUSE]->(:Event), (:Claim)-[:HAS_EFFECT]->(:Event), (:Claim)-[:FROM_ARTICLE]->(:Article)

Same clustering and repeat filter as kg/build_viewers.py. Events with self-loops only are included here, though the pages leave them out.
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.cluster import AgglomerativeClustering

from refilmed import remove_repeats

KG = Path(__file__).resolve().parent
SRC = KG / "out" / "combined"
DEST = KG / "out" / "graph_v1"
VERSIONS = [("event-030", "embed_qwen_event.npy", 0.30), ("event-035", "embed_qwen_event.npy", 0.35),
            ("topic-030", "embed_qwen_topic.npy", 0.30), ("topic-035", "embed_qwen_topic.npy", 0.35)]

ROWS, REMOVED = remove_repeats([json.loads(line) for line in open(SRC / "normalised.jsonl", encoding="utf-8")])
ALL_TEXTS = json.load(open(SRC / "embed_texts.json", encoding="utf-8"))
USED = {r[k] for r in ROWS for k in ("cause_description", "effect_description")}
KEEP = [i for i, t in enumerate(ALL_TEXTS) if t in USED]
T = [ALL_TEXTS[i] for i in KEEP]


def short(description):
    return description.rsplit(",", 1)[0].strip() if "," in description else description.rstrip(".")


def write(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, rows[0].keys())
        w.writeheader()
        w.writerows(rows)


def export(slug, file, threshold):
    m = np.load(SRC / file)[KEEP].astype(np.float64)
    d = np.clip(1 - m @ m.T, 0, 2)
    np.fill_diagonal(d, 0)
    labels = AgglomerativeClustering(n_clusters=None, metric="precomputed", linkage="average", distance_threshold=threshold).fit_predict(d)
    groups = defaultdict(list)
    for i, l in enumerate(labels):
        groups[int(l)].append(i)
    events, node_of = [], {}
    for n, k in enumerate(sorted(groups, key=lambda k: -len(groups[k]))):
        ids = groups[k]
        centre = ids[int(np.argmin(d[np.ix_(ids, ids)].sum(1)))]
        events.append({"id": f"n{n}", "label": short(T[centre]), "descriptions": len(ids)})
        for i in ids:
            node_of[T[i]] = f"n{n}"
    links = defaultdict(list)
    claims, has_cause, has_effect, from_article = [], [], [], []
    for r in ROWS:
        a, b = node_of[r["cause_description"]], node_of[r["effect_description"]]
        links[(a, b)].append(r)
        claims.append({"id": r["key"], "date": r["date"], "quote": r["quote"], "cause": r["cause"], "effect": r["effect"], "reasoning": r["reasoning"],
                       "cause_place": r["cause_place"], "cause_description": r["cause_description"],
                       "effect_place": r["effect_place"], "effect_description": r["effect_description"]})
        has_cause.append({"claim": r["key"], "event": a})
        has_effect.append({"claim": r["key"], "event": b})
        from_article.append({"claim": r["key"], "article": r["article_id"]})
    arrows, loops = [], []
    for (a, b), rs in links.items():
        days = sorted(r["date"] for r in rs)
        row = {"source": a, "target": b, "claims": len(rs), "articles": len({r["article_id"] for r in rs}), "pages": len({r["page"] for r in rs}),
               "first_date": days[0], "last_date": days[-1]}
        (loops if a == b else arrows).append(row)
    articles = {r["article_id"]: {"id": r["article_id"], "page": r["page"], "date": r["date"], "headline": r["headline"] or ""} for r in ROWS}
    out = DEST / slug
    out.mkdir(parents=True, exist_ok=True)
    for name, rows in [("events", events), ("causes", arrows), ("self_loops", loops), ("claims", claims), ("articles", list(articles.values())),
                       ("has_cause", has_cause), ("has_effect", has_effect), ("from_article", from_article)]:
        write(out / f"{name}.csv", rows)
    print(slug, {"events": len(events), "singletons": sum(e["descriptions"] == 1 for e in events), "arrows": len(arrows),
                 "multi_claim": sum(a["claims"] >= 2 for a in arrows), "multi_article": sum(a["articles"] >= 2 for a in arrows),
                 "loop_claims": sum(l["claims"] for l in loops), "claims": len(claims), "articles": len(articles)})


for slug, file, threshold in VERSIONS:
    export(slug, file, threshold)
(DEST / "manifest.json").write_text(json.dumps({"claims": len(ROWS), "removed_as_refilmed": len(REMOVED), "first_date": min(r["date"] for r in ROWS),
                                                "last_date": max(r["date"] for r in ROWS), "source": str(SRC.relative_to(KG))}, indent=2), encoding="utf-8")
