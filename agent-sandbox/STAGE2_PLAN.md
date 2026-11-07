# Plan: normalisation, embedding and clustering (v1)

Status: draft, 2026-11-06. Normalisation is running; embedding and clustering have not started. This updates
`KG_PLAN.md` Stage 2. Input is the 590 kept claims from the extraction run.

## 1. Normalisation

Normalisation writes a short, self-contained description of each cause and effect, so the embedding model has
enough context. It replaces the canonical phrases and direction tags in `KG_PLAN.md`; direction returns only if
the test in section 3 requires it.

- **One call per claim**, `qwen3.5:9b-q8_0`, no thinking, temperature 0. Claims from the same article run together.
- **Input:** full article, headline, source, dateline, quote, cause and effect. Article first, so Ollama can reuse it across claims.
- **Output:** `reasoning`, `cause_place`, `cause_description`, `effect_place`, `effect_description`.
- **Originals are kept unchanged,** so each description can be checked against its quote.
- **Why not embed the quote or article directly:** a claim's cause and effect share them, which would pull the two
  together and create self-loops, and phrases would cluster by article and not by event.
- **Time:** measured at 3.3 s per claim, so ~35 min for 590 claims.

### Prompt

The working prompt, 5 hand-written worked examples and the user message are in `kg/normalise_prompt.py`, and printed
in `extraction_prompts.md`. The answer has a `reasoning` field first, then `cause_place`, `cause_description`,
`effect_place`, `effect_description`. The examples' claims must be left out of any test of this prompt.

### Rulings on prompt behaviour (user, 2026-11-06)

| Case | Ruling |
| --- | --- |
| Counterfactuals | No hypotheticals in the graph; reverse both sides into what really happened |
| Hedged or reported claims | State the event plainly; the quote keeps the hedge |
| Two-part cause or effect | One sentence for v1 |
| Specificity | Keep names, and add a free general phrase of up to 4 words |
| Vague terms | Only what the article states, so "the strike" stays "a strike" if unidentified |
| Place | One place per side; "unknown" if unclear |
| Spelling | The paper's 1925 names, with obvious OCR errors corrected |
| Conditions | Describe as a condition, with no invented actor |

To check when reading the output: whether the general phrase pulls clusters toward broad topics, and whether unidentified
"a strike" descriptions merge different strikes.

`source` and `dateline` are now fields in the article files and go in the user message, since a line like "Canton,
June 15" is evidence of place.

## 2. Embedding

- **Model:** `qwen3-embedding:8b` (user's choice; 4B if too slow). `bge-small-en-v1.5` is the comparison.
- **Pool:** causes and effects together, so chains can connect through shared nodes.
- **Instruction (user, 2026-11-06):** "Represent this event from a 1925 Hongkong newspaper so that descriptions of the
  same event are close, and different events are far apart, even if they share a topic." Same text on every description.
  This replaced a topic-level instruction, whose results are kept as `kg/out/nodes_topic.json` and `edges_topic.json`.

## 3. Tests before clustering

1. **Descriptions:** read every counterfactual and a sample of the rest, for invented details and reversed claims.
   The full run went ahead without a 50-claim review first.
2. **Nearest neighbours:** for ~20 phrases, compare neighbours across inputs (phrase, phrase + place, description)
   and models (`qwen3-embedding:8b`, `bge`).
3. **Direction:** measure distances for ~20 opposite pairs and ~20 same-topic pairs that aren't opposites.

| Direction test result | Action |
| --- | --- |
| Opposites clearly farther apart than same-topic pairs | No direction split |
| Slight overlap | No split; review step looks for mixed clusters |
| Heavy overlap | Add a direction tag and cluster within it |

## 4. Clustering (to be discussed)

**Done (2026-11-06):** `kg/cluster_final.py`, average-link agglomerative clustering, cosine distance threshold 0.35, no place
separation. 413 nodes (235 groups, 178 singletons). Output: `kg/out/nodes.json`, `kg/out/edges.json`. HDBSCAN was tried first
and replaced, since it left 40–80% of descriptions unclustered. Unmatched descriptions stay as their own nodes. No dimension
reduction was used. Node labels are provisional. Review of mixed clusters and a spot check of the largest nodes are still to do.

## 5. Comparison pages

`kg/build_viewers.py` builds `kg/viewer/event-030.html`, `event-035.html`, `topic-030.html` and `topic-035.html` in the user's simplified
demo format (`demo_kg/causal_kg_demo_local.html`), each linking to the others. No filters or colours. Self-loop claims are listed on their node.

## 6. Missing-edge analysis (user's goal, 2026-11-06)

The goal is to find pairs of nodes where a connection is expected but absent. `kg/missing_edge_power.py` tests whether each version can
support this statistically, with a simple null model: expected claims a → b = out(a) × in(b) / total claims.

| Version | Nodes | Arrows present | Missing pairs, expected ≥ 1 | Expected ≥ 3 |
| --- | --- | --- | --- | --- |
| Event, 0.30 | 540 | 0.15% | 1 | 0 |
| Event, 0.35 | 372 | 0.28% | 2 | 0 |
| Topic, 0.30 | 435 | 0.21% | 1 | 0 |
| Topic, 0.35 | 289 | 0.39% | 4 | 1 |

None has enough claims per pair. Coarser nodes do help, but only slightly at these thresholds. An absent edge can also mean a pipeline miss,
since extraction recall is unmeasured and the corpus is selected.

**Shared neighbours (user's method).** If two causes share k or more effects, each effect only one of them has is a candidate missing edge.
`kg/shared_neighbours.py`, cause pairs sharing k effects: Event 0.30: 2+ 0; Event 0.35: 2+ 6, 3+ 0; Topic 0.30: 2+ 8, 3+ 0; Topic 0.35: 2+ 17, 3+ 1.
Most 2-shared pairs read as noise from vague catch-all nodes ("The city remains calm"); some are meaningful, such as Bolshevik influence and
lack of a central government, both linked to discontent and Shanghai disturbances.

## 7. Further months (user, 2026-11-06)

`kg/run_batches.py` runs Aug–Sep, then Apr–May, then Oct–Nov 1925, on the same rules: pages scoring ≥ 8, CORE or BROAD term, letters removed,
full article + check, then normalisation. Each batch has its own folder in `kg/out/batches/`, and June–July stays frozen. After each batch,
`kg/combine.py` merges all finished sets and rebuilds `kg/viewer_combined/`. To stop: create `kg/out/batches.stop`. Log: `kg/out/batches.log`.
New months use a dateline pattern covering all months; June–July keeps its original pattern so its article IDs don't change.

## Open decisions

1. What to do with self-loops: 144 of 590 claims have cause and effect in the same node.
2. Repeated notices: the same item printed on several days inflates some edges.

Settled for now: no place separation (user, 2026-11-06). Threshold 0.35 is Claude's choice, pending the user's view.
