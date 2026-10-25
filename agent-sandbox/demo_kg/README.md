# demo_kg: proof-of-concept causal knowledge graph

A small end-to-end run of the three-step plan (extract → cluster → graph) on 8 pages of
`agent-sandbox/strike_pages_md/` (China Mail, 1925-06-16 to 07-03). The output is
`causal_kg_demo.html`, a self-contained interactive page (Cytoscape.js from cdnjs).

## Files

| File | Step | What it is |
| --- | --- | --- |
| `relations.jsonl` | 1 | 105 cause → effect claims. Fields: `page`, `date`, `headline`, `cause`, `effect`, `quote` (verbatim OCR text), `asserted_by`, `kind` (`explicit` / `implicit` / `counterfactual`). **Written by Claude**, standing in for the planned local LLM. Headlines are lightly cleaned of OCR errors; quotes are not. |
| `cluster.py` → `clusters.json` | 2 | Embeds the 157 distinct cause/effect phrases with `BAAI/bge-small-en-v1.5` (fastembed, ONNX) and clusters them with scikit-learn HDBSCAN (`min_cluster_size=2`). |
| `nodes.json` | 2b | LLM review of the HDBSCAN output (also by Claude): the final 100 event nodes, each listing the phrases it covers, plus a theme for colour. HDBSCAN grouped many opposites (market closed / reopens, pirate raid / pirates repelled); the review splits those and merges synonyms it missed. |
| `build_graph.py` → `graph.json`, `causal_kg_demo.html` | 3 | Checks every phrase is in exactly one node and that no relation becomes a self-loop, merges relations between the same two nodes into one edge carrying every quote, and inlines the graph into `viewer_template.html`. |

`causal_kg_demo_local.html` is the same page wrapped in a full HTML document. Open it directly in a
browser (double-click it). It needs internet only for Cytoscape.js (cdnjs) and Google Fonts. The data is inlined.

## Run

```
python -m venv agent-sandbox/.venv-kg          # Python 3.13; onnxruntime has no 3.15 wheels
agent-sandbox/.venv-kg/Scripts/python -m pip install fastembed scikit-learn numpy truststore
agent-sandbox/.venv-kg/Scripts/python agent-sandbox/demo_kg/cluster.py
agent-sandbox/.venv-kg/Scripts/python agent-sandbox/demo_kg/build_graph.py
```

`truststore` is needed on this machine: the Hugging Face model download fails SSL verification
with the default certifi bundle. Re-running `cluster.py` renumbers clusters only if the phrases change;
after editing `relations.jsonl`, update `nodes.json` so every new phrase is assigned (the build asserts this).

## Swapping in a local LLM

Replace step 1 with a model that writes the same `relations.jsonl` schema (JSON-schema constrained
output), and optionally step 2b with a prompt that proposes `nodes.json` from `clusters.json`.
Steps 2 and 3 run unchanged.
