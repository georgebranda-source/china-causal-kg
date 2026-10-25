"""Step 3 of the demo: turn relations + reviewed nodes into graph.json for the viewer.

    agent-sandbox/.venv-kg/Scripts/python agent-sandbox/demo_kg/build_graph.py

Checks that every extracted phrase is assigned to exactly one node and that no relation maps to a
self-loop, then aggregates relations into weighted edges that keep every quote as evidence.
"""

import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    rels = [json.loads(line) for line in open(HERE / "relations.jsonl", encoding="utf-8")]
    clusters = json.loads((HERE / "clusters.json").read_text(encoding="utf-8"))
    spec = json.loads((HERE / "nodes.json").read_text(encoding="utf-8"))

    phrase_node = {}
    for n in spec["nodes"]:
        for p in n["phrases"]:
            assert p not in phrase_node, f"phrase in two nodes: {p}"
            phrase_node[p] = n["id"]
    extracted = {p for r in rels for p in (r["cause"], r["effect"])}
    assert extracted == set(phrase_node), (
        f"unassigned: {extracted - set(phrase_node)}; unknown: {set(phrase_node) - extracted}"
    )

    edges = {}
    for r in rels:
        src, dst = phrase_node[r["cause"]], phrase_node[r["effect"]]
        assert src != dst, f"self-loop {src}: {r['cause']} -> {r['effect']}"
        e = edges.setdefault((src, dst), {"source": src, "target": dst, "evidence": []})
        e["evidence"].append({k: r[k] for k in ("date", "page", "headline", "cause", "effect", "quote", "asserted_by", "kind")})

    degree = Counter()
    for (s, t), e in edges.items():
        degree[s] += len(e["evidence"])
        degree[t] += len(e["evidence"])

    # how the review changed HDBSCAN's proposal: a multi-phrase HDBSCAN cluster is "kept" if all its
    # phrases landed in one node, otherwise "split"
    p2c = clusters["phrase_to_cluster"]
    hdb_multi = {c: ps for c, ps in clusters["clusters"].items() if len(ps) > 1}
    kept = sum(1 for ps in hdb_multi.values() if len({phrase_node[p] for p in ps}) == 1)
    merged_nodes = sum(1 for n in spec["nodes"] if len({p2c[p] for p in n["phrases"]}) > 1)

    graph = {
        "themes": spec["themes"],
        "nodes": [
            {"id": n["id"], "label": n["label"], "theme": n["theme"], "phrases": n["phrases"],
             "hdbscan": sorted({p2c[p] for p in n["phrases"]}), "weight": degree[n["id"]]}
            for n in spec["nodes"]
        ],
        "edges": sorted(edges.values(), key=lambda e: (e["source"], e["target"])),
        "stats": {
            "pages": len({r["page"] for r in rels}),
            "relations": len(rels),
            "phrases": len(extracted),
            "embedding_model": clusters["model"],
            "hdbscan_clusters": len(clusters["clusters"]),
            "hdbscan_multi": len(hdb_multi),
            "review_kept": kept,
            "review_split": len(hdb_multi) - kept,
            "review_merged_nodes": merged_nodes,
            "nodes": len(spec["nodes"]),
            "edges": len(edges),
        },
    }
    (HERE / "graph.json").write_text(json.dumps(graph, indent=1, ensure_ascii=False), encoding="utf-8")

    # self-contained viewer: graph.json inlined into the template (escape "</" so it can't close the script tag)
    template = (HERE / "viewer_template.html").read_text(encoding="utf-8")
    payload = json.dumps(graph, ensure_ascii=False).replace("</", "<\\/")
    page = template.replace("__GRAPH_JSON__", payload)
    (HERE / "causal_kg_demo.html").write_text(page, encoding="utf-8")  # claude.ai artifact adds the skeleton
    local = (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<style>body{margin:0}</style>\n</head>\n<body>\n" + page + "\n</body>\n</html>\n"
    )
    (HERE / "causal_kg_demo_local.html").write_text(local, encoding="utf-8")  # open directly in a browser

    print(json.dumps(graph["stats"], indent=1))
    print("top nodes:", degree.most_common(8))


if __name__ == "__main__":
    main()
