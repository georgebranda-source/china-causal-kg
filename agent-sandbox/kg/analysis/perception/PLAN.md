# Plan: British perceptions of the Hongkong strike in the China Mail, May–July 1925

Status: **approved 2026-11-16, NOT started.** The user wants to discuss further ideas before anything runs.
Deadline given by the user: extraction and a completed graph by 11:00 at the latest, with timing from the start of the run.

## Research question
To what extent does the China Mail graph data show the accuracies and inaccuracies in British perception
that the literature describes?

| # | Perception (literature) | Reality (literature) | What the data must show |
|---|---|---|---|
| 1a | Communist conspiracy caused it | Accurate: agitators instigated and supported the strike | British voices give Bolshevik or Red *agitators* as the cause |
| 1b | (same) | Inaccurate: the strikers themselves weren't Communist; unclear whether the British believed they were | British voices call the *strikers* Red |
| 2 | Canton government support caused it | Accurate: means to leave, instigation, support | British voices give Canton (orders, pay, food, housing, transport, pickets) as the cause |
| 3 | Not caused by nationalism or anti-foreign feeling | Inaccurate: the Shanghai and Shakee massacres, foreign privilege, patriotism | Nationalism missing from British-voice causes |
| 3b | (same) | Partly accurate: many strikers weren't nationalist | Intimidation and labour as contrast categories |

## Principles (user decisions)
- **Systematic, with no labelling by Claude.** Every measure comes from the pipeline: the local Qwen extraction with a frozen, versioned prompt, the embedding step, and deterministic rules. Claude does not hand-code anything.
- **Denials:** inferred from absence. Ruling 2.3 (skip denied links) stays. The recall problem is noted, and the user may come back to it later.
- **Scope:** causes of the strike only, May–July 1925.
- **Re-extract everything** in scope with the new schema, so there is one instrument. v1 and `graph_v1` are not touched.
- **Validation:** a gold sample of about 50 claims hand-coded by the user for speaker_type and category, done after the deadline. The first results are reported as unvalidated.
- **Overnight run is autonomous**, with safe error recovery as for the HKPL scrapes, and every decision logged.

## 1. Page selection
- Score every May–July page from the existing fast OCR: strike score (`strike_screen_batch.csv`) plus perception score (`agent-sandbox/perception_screen.py` → `perception_screen.csv`).
- **VL-OCR the un-OCRed pages with combined score ≥ 7: 76 pages, about 3.8 h.** All 301 May–July pages that already have VL OCR are kept.
- Perception dictionary (approved), one point per concept:
  - bolshevik\*; communis\*; "reds"; soviet/Borodin/Moscow; agitator/instigat\*/ringleaders; intimidat\*/terroris\*/coercion
  - kuomintang/whampoa/cantonese
  - nationalis\*; patriot\*; anti-foreign/anti-British/xenophob\*; Shakee/Shaji/Shameen/massacre/shooting; extraterritorial\*/imperialis\*/unequal/concessions; students
  - Dropped: bare "canton" (on 299 of 572 un-OCRed pages, mostly shipping lists) and "russian(s)" (general Russia news).
- Vocabulary note: `strike_screen_batch.frozen_vocab()` now fails its assert (28 files, not 24), because pages 11–14 of 2 June 1925 were VL-OCRed on 2026-11-02. `perception_screen.py` leaves those four out, which reproduces the original 24.

## 2. Article selection
- Rebuild articles for all May–July VL pages, using the same ad rule as v1.
- An article goes to extraction if it contains at least one strike CORE term **or** at least one perception concept.
- Letters are **included** and tagged `is_letter` by the existing deterministic letter detector in `kg/build_corpus.py`.

## 3. Extraction schema (v1 prompt plus speaker fields, with a new prompt hash)
- `speaker`: the name as printed, or "the paper" for the paper's own voice.
- `speaker_type`, one of:
  - `PAPER`
  - `BRITISH_OFFICIAL`
  - `BRITISH_OTHER` (meetings, residents, British press)
  - `CHINESE` (individuals, notices, guilds)
  - `CANTON_GOVT` (the government, the Strike Committee, the Kuomintang)
  - `OTHER_FOREIGN`
  - `UNKNOWN`
- `is_letter`: deterministic, from the article, not from Qwen.
- Everything else (few-shot examples, check pass, normalisation) is as in v1. Smoke test before the full run.

## 4. Categorisation in the embedding step
- Embedder: `qwen3-embedding:8b` with the v1 event-level instruction. The anchors are written in the style of the normalised descriptions.
- **In scope:** `effect_place` is Hongkong or Canton (deterministic) **and** the effect description is closest to one of these strike anchors:
  - "Chinese workers in Hongkong go on strike, a general strike."
  - "Workers leave Hongkong for Canton, an exodus of labour."
  - "A boycott of British trade and shipping, a boycott."
- **Cause categories** (approved anchors):

| Category | Anchors |
|---|---|
| 1a Red agitators | "Bolshevik agitators instigate the strike, a Communist conspiracy." / "Soviet agents and Communist propaganda stir up labour unrest, a Bolshevik plot." |
| 1b Strikers are Red | "The striking workers are Communists, a Bolshevik labour movement." / "Hongkong workers adopt Bolshevism, a Red labour movement." |
| 2 Canton support | "The Canton Government orders and directs the strike, a political intervention." / "Canton authorities pay, feed and house strikers who leave Hongkong, strike support." / "Canton provides transport for workers leaving Hongkong, an organised evacuation." / "Canton pickets prevent strikers returning to Hongkong, picket enforcement." |
| 3T Trigger: shootings | "The shooting of Chinese demonstrators at Shakee in Canton, a massacre." / "Police fire on Chinese students in Shanghai, a shooting." |
| 3M Motive: patriotic / anti-foreign feeling | "Chinese patriotic anger at the shooting of students in Shanghai, a nationalist protest." / "Chinese resentment of foreign privilege and unequal treaties, an anti-foreign movement." / "Workers strike in sympathy with their compatriots in Shanghai, a patriotic protest." |
| Contrast: Intimidation | "Workers are forced to strike by threats and intimidation, coercion." |
| Contrast: Labour | "Workers demand higher wages and better conditions, an economic grievance." |

- Nationalism is split into 3T and 3M (user, 2026-11-16). Both count toward item 3, so a British voice that cites the shootings but not the motive shows up. The second 3T anchor is new and still needs the user's approval. The others are the approved wording, regrouped.
- **Assignment rule:** nearest anchor's category if similarity ≥ 0.65 and it beats the next category by ≥ 0.02; otherwise "other". Sensitivity reported at 0.60 and 0.70.
- Known weakness: the embedder separates topics better than direction (v1 test: opposites 0.59, same-topic 0.73). Telling 1a from 1b is the riskiest distinction, and the gold sample will test it.

## 5. Graph design (user, 2026-11-16)
A layered property graph. Every edge above the evidence layer links back to its claims and quotes.
1. **Evidence layer:** articles → claims (date, speaker, speaker_type, is_letter, page, quote).
2. **Event layer:** cluster nodes, built bottom-up as in v1 (event-035 settings), used for chains and traversal.
3. **Concept layer:** the anchor categories plus the HK Strike node. Every event node, not only direct causes, is mapped to a concept or to "other", so upstream chains can be read at concept level.
4. **Speaker layer:** a speaker node for each named speaker, linked to concepts.

**Network analyses** (all four chosen):
- **Discourse network analysis:** a speakers × concepts bipartite network, with a speaker projection showing shared framings, and British against Chinese coalitions. Standard DNA also records agreement and disagreement; here only assertions are available, because denials are not extracted.
- **Upstream paths:** ancestors of the HK Strike node within 3 hops. **Asserted** paths (within one article) are kept separate from **composed** paths (joined across articles or speakers). Findings rest on asserted paths; composed paths are for exploration in the viewer only, because they can show a perception nobody held.
- **Voice-split comparison:** separate British-voice (PAPER, BRITISH_OFFICIAL, BRITISH_OTHER) and Chinese-voice (CHINESE, CANTON_GOVT) graphs, compared by in-edge weights and ancestor sets.
- **Fortnightly snapshots** of the strike node's ancestry, May–July 1925.
- Not done: global centrality, community detection or PageRank on the event layer. The node definition drives them, and v1 showed little structure there (5i).

**Viewer:** a local self-contained HTML file in agent-sandbox, extending `demo_kg/viewer_template.html`. It opens at the concept layer, with edges weighted and filtered by voice and fortnight, and expands to events and then to quotes. The asserted/composed toggle is visible.

**Deadline split:** by 11:00, the graph data (all layers as files), category counts and a basic concept-level view. The full viewer and the network analyses come afterwards.

## 6. Outputs
- New output folder; `kg/out/graph_v1` is left alone.
- Counts of category × speaker_type × fortnight, with British voices (PAPER, BRITISH_OFFICIAL, BRITISH_OTHER) against Chinese voices (CHINESE, CANTON_GOVT).
- A presence and accuracy matrix per literature item.
- `FINDINGS.md` and a gold-sample file for the user.
- Findings are not described as a test of "British Hong Kong media" in general: there is one paper, the selected pages, and explicit causal claims only.

## 7. Timeline (durations from the start)
| Duration | Step |
|---|---|
| 0:00–3:50 | VL OCR of 76 pages. On CPU meanwhile: schema and prompt edits, logging |
| 3:50–4:20 | Article rebuild and filter, schema smoke test |
| 4:20–~7:50 | Extraction, check, normalisation |
| ~7:50–8:50 | Embedding, anchor assignment, graph |
| 8:50–9:50 | Counts, FINDINGS.md, gold-sample file |
| remainder | Buffer |

## Open
- Approve the new 3T anchor wording ("Police fire on Chinese students in Shanghai, a shooting.").
- Start time not set; the user is still discussing ideas.

## Update 2026-11-16 (evening): item 4 and anchors v2
From the user's draft, the literature has a fourth item: **4. The British denied that working conditions caused the strike.** This is inaccurate: racial wage disparity, demands for labour legislation and workplace discrimination mattered (Cao & Seifert; Horrocks), although the strike was primarily political.
- `C_labour` (one contrast anchor) is replaced by the substantive category **4_working_conditions**, with these anchors:
  - "Chinese workers are paid far less than foreigners for the same work, a racial wage disparity."
  - "Chinese employees suffer discrimination and ill-treatment by foreign employers, a workplace grievance."
  - "Workers demand labour laws to protect them from exploitation, a labour reform demand."
  - "Workers seek higher wages and shorter working hours, an economic grievance."
  - "Workers cannot afford rising rents and the price of rice, a cost-of-living grievance."
- `C_intimidation` gains "Secret societies compel workers to stop work by threats, intimidation."
- An anchor for 1a organising ("Communist organisers fund and coordinate…") was considered and **rejected**, because it overlaps Canton support (2) and would blur the 1a/2 distinction.
- Wording rules: no new anchor says "strike", because effects are matched against every anchor; none ends in a generic "a labour dispute".
- Only `graph.py` reruns, with no re-extraction. v1 results stay in `snapshots/through_1926-04/` and v2 results are in `snapshots/through_1926-04_anchors_v2/` (also the live `graph/`).
