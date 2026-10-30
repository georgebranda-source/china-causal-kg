# Causal knowledge graph: full pipeline plan

Goal: a causal knowledge graph of the 1925 Canton–Hongkong strike as reported in the *China Mail*
(June–July 1925), where every edge is a causal claim found in the paper and links back to the exact
sentences, date, page and the person or source making the claim.

The proof of concept in `demo_kg/` already runs every stage on 8 pages (105 relations, 100 events,
91 edges). The full process scales that up and replaces the parts Claude did by hand with a local
LLM, plus evaluation.

```
page images ─► VL OCR ─► articles ─► causal relations ─► event nodes ─► graph + viewer
  (done)     (Stage 0)  (Stage 0)       (Stage 1)          (Stage 2)      (Stage 3)
```

---

## Where things stand

| Piece | Status | Location |
| --- | --- | --- |
| 496 page images, June–July 1925 | done | `data/raw/hkpl/china_mail_june_july_1925/` |
| Fast OCR of all pages + strike keyword scores | done | `ocr_fast_out/`, `strike_screen.csv` |
| PaddleOCR-VL transcription of the 40 highest-scoring pages | done | `strike_pages_md/` |
| Relation schema, quote verifier, clustering, graph build, viewer | done (demo) | `demo_kg/` |
| Local LLM extraction | not started | |
| Evaluation set | not started | |

---

## Stage 0: corpus

### 0a. Decide how many pages to transcribe

VL OCR takes about 3 minutes per page. Pages with a score above the cutoff that haven't been transcribed yet
(from `strike_pages_md/README.md`):

| Score cutoff | Extra pages | VL time |
| --- | --- | --- |
| ≥ 12 | 74 | ~4 h |
| ≥ 8 | 132 | ~7 h |
| ≥ 5 | 209 | ~10.5 h |

Recommendation: run **≥ 8** overnight. That covers most pages with a core strike term, including
the late-July pages where the strike is already established. Run it in the background with
`ocr_vl.py @<list>` exactly as for the first 40.

### 0b. Split pages into articles and drop ads

- Split on the markdown headings (`#`, `##`) PaddleOCR-VL already emits. Merge consecutive heading
  blocks with under ~40 words of body into the next block (subheads like "(Reuter's Service.)",
  datelines like "Canton, June 15").
- Drop ad blocks with a keyword filter: prices (`$`, `cts`, `per bottle`), "Telephone", "Ltd."
  near the top, repeated mastheads (Watson's, Mackintosh, Dragon Motor, Moutrie). The same ads
  recur every issue, so a list built from 5–6 pages catches most of them.
- Optional second pass: a cheap LLM yes/no call ("is this a news or opinion item?") on what's left.
- Output: `articles.jsonl` with `article_id`, `page`, `date`, `headline`, `text`, `char_start`.

The OCR column order is sometimes wrong. Some articles in the demo are interleaved with
unrelated text, e.g. the BAT strike paragraph in the middle of the Shanghai murder story on
06-16. Article splitting won't fix this. Extraction must tolerate it, and the quote check (below)
keeps it from producing invented text.

---

## Stage 1: causal relation extraction (local LLM)

### Runtime and models

- **Runtime:** Ollama on Windows (simplest), using its JSON-schema `format` option so output is
  always valid JSON. llama.cpp server is the fallback with the same schema support.
- **Candidates** for the RTX 5080 (16 GB VRAM):
  - `qwen2.5:14b` or `qwen3:14b` at Q4_K_M (~9 GB): the default choice
  - `mistral-small:24b` at Q4 (~14 GB): tight fit, possibly better at implicit causation
  - `llama3.1:8b`: speed baseline; expected to miss implicit links
- Pick by score on the evaluation set (below), not by reputation.

### Schema

The same schema as `demo_kg/relations.jsonl`, so the clustering and graph-building steps run unchanged:

```json
{"cause": "...", "effect": "...", "quote": "...", "asserted_by": "...",
 "kind": "explicit | implicit | counterfactual"}
```

The pipeline adds `page`, `date`, `headline` and `article_id`. Optional new fields worth testing:
`negated` (e.g. "no question about seamen's wages"), `hedged` ("it is said", "reported").

### Prompt

- One article per call. Long articles are split at paragraph boundaries with one paragraph of overlap.
- System prompt: definition of a causal claim, the three `kind` values, rules
  ("quote must be copied exactly", "asserted_by is who makes the claim, not who acts",
  "skip advertisements, sports, court cases unrelated to the strike").
- 4–6 few-shot examples taken from the demo relations. They already cover counterfactuals
  (Samuel, Hankow consul), attribution (Chan Kim-fook vs. China Mail), and contested claims (Shameen).
- Temperature 0.

### Checks after extraction (automatic)

1. **Quote verification**: the quote must appear verbatim (after collapsing whitespace) in the article.
   This check already exists in the demo. On failure, try a fuzzy match (`rapidfuzz`, ≥ 95) and replace the quote with the
   matching original text. Otherwise drop the relation and log it.
2. Drop relations where cause and effect are the same phrase or empty.
3. De-duplicate relations from overlapping chunks.

### Throughput estimate

About 20 article blocks per page, of which perhaps a third are news. A 14B model should take roughly
5–10 s per article on the 5080, so **40 pages ≈ 1–2 h, 170 pages ≈ 4–8 h**. Measure on 2 pages
before committing.

---

## Evaluation (do this before the full run)

Without this, there's no way to tell whether the local model is good enough, or which one to pick.

- **Gold set:** hand-annotate about 15 articles from pages not in the demo, about 50–80 relations.
  Mix front-page news, editorials, Reuter cables and strike-item round-ups.
  Annotate in the same JSONL schema; a simple annotation sheet (one row per relation) is enough.
- **Silver set:** the 105 demo relations (Claude-extracted) for quick iteration on prompts.
- **Matching:** a predicted relation counts as correct if its quote overlaps the gold quote and
  cause/effect are judged equivalent (embedding similarity ≥ threshold, then manual spot check).
- **Metrics:** precision, recall, F1 on relations; accuracy of `kind` and `asserted_by`.
- **Target:** precision ≥ 0.8 matters more than recall. A wrong arrow with a real-looking quote is
  worse than a missing arrow.
- Run all three candidate models; keep the prompt fixed while comparing.

---

## Stage 2: event nodes (normalization + clustering)

What the demo showed: on short phrases, HDBSCAN mostly paired nearest neighbours, and **20 of its
29 groups mixed opposites** ("Central Market closed" / "reopens", "pirate raid" / "pirates
repelled"). Embeddings capture topic, not direction. The plan handles that explicitly.

1. **Normalize** (LLM, per relation): rewrite each cause/effect as a short canonical event
   ("subject + verb + object", present tense, no dates) and tag `polarity`
   (`start/increase` vs. `end/decrease`) and `place` (Hongkong, Canton, Shanghai, Hankow, …).
2. **Embed** with `bge-small-en-v1.5` (as in the demo) or `bge-m3` if the phrase count gets large.
3. **Cluster** within blocks of the same polarity (and optionally place) so opposites cannot
   merge. HDBSCAN with `min_cluster_size=2`. With more than ~2,000 phrases, reduce with UMAP to
   10 dimensions first.
4. **LLM review**: for each cluster, the model gets the member phrases and answers: keep, split
   (into which groups), or merge with a named neighbour cluster. Then it writes a node label. This
   produces `nodes.json` in the demo format, so `build_graph.py` runs unchanged.
5. **Human spot check** of the 30 largest nodes. Those carry most of the edges.

Expected size: with ~170 pages, perhaps 1,500–2,500 relations and 300–600 event nodes.

---

## Stage 3: graph and viewer

- `build_graph.py` already merges relations into edges with evidence lists, checks every phrase is
  assigned, and rejects self-loops. Add:
  - **GraphML export** for Gephi (exploration, community detection, centrality).
  - **Optional Neo4j export** using the helpers in `src/china_causal_kg/graph/` if querying is needed
    ("all causes of the seamen's strike asserted by Reuter").
- **Viewer** (`demo_kg/viewer_template.html`) at a few hundred nodes:
  - text search for events
  - "minimum evidence" slider to hide single-quote edges
  - filter by `asserted_by` group (British officials, Chinese officials, unions, China Mail
    editorial, Reuter) to compare whose causal story is whose
  - keep the date slider. With 6 weeks of issues it shows how the explanation changes over time.

---

## Validity notes to carry into the write-up

- Every edge is a **claim in a British colonial newspaper**, not an established cause. The
  `asserted_by` field is what makes this usable for historical argument; keep it mandatory.
- Strikers' own reasons mostly appear second-hand (union secretaries, quoted demands). A useful
  research question is exactly this asymmetry: instigation narratives (Canton, Moscow,
  intimidation) vs. economic narratives (wages, child labour, machinery).
- Contested claims (e.g. who fired first at Shameen) must stay as separate, conflicting edges.
- OCR errors stay in quotes on purpose, so every quote can be found in the source text.

---

## Order of work

| # | Task | Effort | Depends on |
| --- | --- | --- | --- |
| 1 | Install Ollama, pull 2–3 candidate models | 30 min | — |
| 2 | Article splitter + ad filter (`articles.py`) | half a day | — |
| 3 | Extraction script with schema, prompt, quote check (`extract.py`) | 1 day | 1, 2 |
| 4 | Hand-annotate gold set (~15 articles) | 1 day (human) | 2 |
| 5 | Evaluate models and prompt, pick one | half a day | 3, 4 |
| 6 | VL OCR of extra pages (score ≥ 8), overnight | ~7 h unattended | — (start now) |
| 7 | Full extraction run | a few hours unattended | 5, 6 |
| 8 | Normalization + polarity-aware clustering + LLM review | 1 day | 7 |
| 9 | Graph build, GraphML export, viewer upgrades | half a day | 8 |
| 10 | Spot-check top nodes, write up findings | 1 day (human) | 9 |

Steps 2, 4 and 6 can run in parallel.

## Decisions needed

1. **Corpus size:** stay at 40 pages, or transcribe up to score ≥ 8 (~170 pages total)?
2. **Gold set:** who annotates, and is ~15 articles enough for the professor's purposes?
3. **Scope of "causal":** include government measures and their effects (bank limits, Emergency
   Regulations), or only causes and effects of the strike itself?
4. **Neo4j:** needed, or is the HTML viewer plus Gephi enough?

## Planned file layout (all in `agent-sandbox/`)

```
kg/
  articles.py        Stage 0b  -> articles.jsonl
  extract.py         Stage 1   -> relations.jsonl (+ rejected.jsonl)
  evaluate.py        gold/silver scoring
  normalize.py       Stage 2.1 -> relations_norm.jsonl
  cluster.py         Stage 2.2-2.3 (from demo_kg, polarity-blocked)
  review.py          Stage 2.4 -> nodes.json
  build_graph.py     Stage 3   -> graph.json, graph.graphml, viewer html (from demo_kg)
  gold/              hand-annotated relations
```
