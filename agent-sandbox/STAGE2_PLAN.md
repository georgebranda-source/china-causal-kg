# Plan: normalisation, embedding and clustering (v1)

Status: draft, 2026-11-06. Nothing here has run. This updates `KG_PLAN.md` Stage 2. Input is
`kg/out/relations.jsonl`, expected to hold about 550 claims.

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
- **Estimated time:** about 5 s per claim, ~45 min. Timed in the 50-claim test.

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

To check in the 50-claim test: whether the general phrase pulls clusters toward broad topics, and whether unidentified
"a strike" descriptions merge different strikes.

`source` and `dateline` are now fields in the article files and go in the user message, since a line like "Canton,
June 15" is evidence of place.

## 2. Embedding

- **Model:** `qwen3-embedding:8b` (user's choice; 4B if too slow). `bge-small-en-v1.5` is the comparison.
- **Pool:** causes and effects together, so chains can connect through shared nodes.
- **Instruction, to be tested:** represent the event so that descriptions of the same event are close, and
  different events are far apart even if they share a topic.

## 3. Tests before clustering

1. **Descriptions:** run normalisation on ~50 claims. Read them for invented details, and time the step.
2. **Nearest neighbours:** for ~20 phrases, compare neighbours across inputs (phrase, phrase + place, description)
   and models (`qwen3-embedding:8b`, `bge`).
3. **Direction:** measure distances for ~20 opposite pairs and ~20 same-event pairs.

| Direction test result | Action |
| --- | --- |
| Opposites clearly farther apart than same-event pairs | No direction split |
| Slight overlap | No split; review step looks for mixed clusters |
| Heavy overlap | Add a direction tag and cluster within it |

## 4. Clustering (to be discussed)

HDBSCAN with `min_cluster_size=2` is the starting point. Unmatched phrases stay as their own nodes. Dimension
reduction is probably unnecessary at ~1,100 phrases. Review of mixed clusters and a spot check of the largest
nodes follow.

## Open decisions

1. Is a node a specific event, or a recurring kind of event? Recommended: a specific event tied to a place, with
   no date in the node, so that claims connect across weeks.
2. Clustering details, in section 4.
