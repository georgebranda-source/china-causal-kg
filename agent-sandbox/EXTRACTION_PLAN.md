# Plan: causal relation extraction with local Qwen, June–July 1925 (v1)

Status: draft, revised 2026-11-06 after user changes. Nothing here has run at scale yet.

**Goal:** a quick first version. Run `qwen3.5:9b-q8_0` (Ollama, no thinking) over the strike-term news
articles on the **137 June–July 1925 pages scoring ≥ 8**, and produce `relations.jsonl`: one row per causal
claim the paper makes directly and clearly, with reasoning, exact quote, cause and effect, plus page, date
and headline.

**Scope:** this covers Stage 0b and Stage 1 of `KG_PLAN.md`. It stops at `relations.jsonl`. Event nodes and
the graph (Stages 2–3) come later. There's no gold set for v1, and the demo relations aren't a target: they
were built for an illustrative graph and are useful only for obvious cases.

**What this replaces in `KG_PLAN.md`:** Stage 0b splitting (now `build_articles.py`), the model comparison
(only the installed Qwen, thinking off), the Stage 1 schema and prompt, the evaluation section and the
throughput estimate.

---

## What counts as a claim

Agreed with the user through real examples (`annotation_study.md`). The prompt is built from these rulings.

| Case | Ruling | Example |
| --- | --- | --- |
| Stated reason or result | Extract | "due to", "owing to", "as a result of", "since" |
| Named cause with a causal verb | Extract | "An excited meeting of 1,500 students and workers… forced the Chairman…" |
| Causal verb, no clear cause | Skip | "they were mobbed and prevented from doing so"; "has been compelled to supplement…" |
| Action against a threat | Extract: threat → action | molestation of foreigners → Indian soldiers sent to Shameen |
| Protest, reply or demand about something | Extract: the thing → the response | firing on the mob → Commissioner's protest |
| Justification by a speaker | Extract: reason → action | danger to foreign lives → firing |
| Sequence only | Skip | "After this the hesitators opened their doors." |
| Side by side, no link | Skip | "The strike continues and all Chinese have left Shameen." |
| Reported speech and officials | Extract | Labour MP in the Commons |
| Readers' letters | Skip | "CORRESPONDENCE" items |
| Hedged claims | Extract | "due, it is said, to threatening letters" |
| Counterfactual about past events | Extract | "Had the Chinese authorities co-operated…" |
| Prediction or conditional | Skip | "will probably lead to"; "If these measures were adopted…" |
| Denied link | Skip | "had no connection whatever with the strike" |
| "This" pointing back | Extract only if the previous sentence names it; quote covers both | "This was due to an attempt to exploit…" |
| Causes unrelated to the strike | Extract | "The cause of his death beyond doubt was apoplexy." |

`cause` and `effect` are short cleaned-up phrases, with OCR errors fixed and pronouns resolved. `quote`
stays verbatim.

## Output format

The model returns a list for each article, fields in this order:

```json
{"relations": [{"reasoning": "...", "quote": "...", "cause": "...", "effect": "..."}]}
```

The pipeline writes one JSONL row per claim:

```json
{"page": "...", "date": "...", "headline": "...",
 "extraction": {"reasoning": "...", "quote": "...", "cause": "...", "effect": "..."}}
```

Ollama's schema keeps `reasoning` first. An article with no claims writes no row, and a progress file
records that it was processed. `headline` falls back to the parent headline, then `null`.

## Pipeline

1. **Articles.** Update `build_articles.py` to take the ≥ 8 page list, add `article_id`, and write
   `articles_score8.jsonl`. Run the agreed LLM continuation check for articles ending mid-sentence.
2. **Filter.** Keep articles with a strike-related term (decision 1). Drop items headed "CORRESPONDENCE" or
   "to the editor" (25 on these pages; letters without those headings will slip through).
3. **Extract twice.** The v1 prompt (`extraction_probe/prompt_v1.py`) on the whole article, and again on
   ~150-word chunks. Each finds claims the other misses.
4. **Automatic checks.** Quote is verbatim after collapsing whitespace, or a `rapidfuzz` match ≥ 95 replaced
   by the original text. Cause differs from effect. Duplicates are merged by overlapping quote. Failures go
   to `rejected.jsonl`.
5. **Run.** Pilot on 2 issues, read the output, then run unattended. Resume by `article_id` + prompt hash,
   and record the model digest (`a8ee95bc3592`), prompts and options in `run_manifest.json`.

## Test results

**Rulings test:** the user's 20 rulings, as 12 sentences to extract and 8 to skip, in 15 articles.

| Setup | Extract | Skip | Total |
| --- | --- | --- | --- |
| Whole article, no check | 9 of 12 | 3 of 8 | 12 of 20 |
| Chunks, no check | 9 of 12 | 4 of 8 | 13 of 20 |
| **Both, merged (plan)** | **11 of 12** | **3 of 8** | **14 of 20** |
| Both + check (not used) | 11 of 12 | 8 of 8 | 19 of 20 |

**Second-pass check removed (user, 2026-11-06).** It can only lower recall, and it sees the quote without the
article, so v1 runs without it. The cost is that v1 output will include claims the rulings exclude. In the test,
5 of the 8 "skip" sentences were still extracted: sequence ("hesitators opened"), causal verbs with no clear
cause ("mobbed and prevented", "compelled to supplement"), a conditional ("If these measures were adopted"), and
a denial ("no connection whatever"), which reads as a causal link in a row. The check stays in
`extraction_prompts.md` and can be run on `relations.jsonl` later without re-extracting.

The test is optimistic, since the prompt was written from these same rulings. The remaining "extract" miss is the
Shameen soldiers sentence. The pilot read-through is the real test.

A few quotes use "..." to skip text, which fails the quote check.

**Earlier demo comparison, for reference only:** 56 articles, against a broader target than the rulings.
Demo quotes found: V0 14, V1 36, V2 55, V3 61, V4 60 of 98.

## Time

Measured on the 15 test articles, which are longer than average: ~13 s per article for both extractions. That's
**up to ~3.3 h for 926 articles, or ~2.6 h for 732**. The pilot should replace this estimate.

## Limits to state in the write-up

- The ≥ 8 cutoff leaves out 359 of the 496 pages, and the term filter drops more within those pages. The
  corpus leans toward pages dense in strike vocabulary.
- Dropping `asserted_by` and `kind` means the graph can't separate a Reuter cable from a union secretary or
  an editorial. `KG_PLAN.md` called attribution mandatory, and `demo_kg/build_graph.py` and the viewer use
  both fields, so Stage 3 needs a small change. Attribution could be added later from the saved quotes.
- v1 has no measured precision or recall on a held-out set.

## Decisions needed

1. **Which strike-term list?** The improvised regex gives 732 articles (761 counting headlines) and keeps 89
   of the 104 demo quotes. The project's own CORE + BROAD vocabulary gives 926 and keeps 94. Recommended:
   CORE + BROAD, checked against headlines as well as body text. It's the same vocabulary that produced the
   score, and it catches items like "SHANGHAI TROUBLES", at the cost of ~40 min more GPU time.

## Planned files (all in `agent-sandbox/`)

```
build_articles.py            updated; -> articles_md/articles_score8.jsonl
kg/extract.py                -> kg/out/relations.jsonl, progress.jsonl, rejected.jsonl, run_manifest.json
extraction_prompts.md        exact prompts, settings and examples
annotation_study.md          the rulings behind the prompts
extraction_probe/            prompts, tests and raw output from 2026-11-06
```
