# Agent notes

Log of data and decision-making for the causal-knowledge-graph project, kept so that everything needed
for the **final writeup** is in one place: what was done, the numbers measured, the options considered,
what was chosen and why, and what is still open. Work done with Claude (Opus 5.5) in `agent-sandbox/`.
The forward-looking plan is in `KG_PLAN.md`. Purely technical setup details (section 3) are kept short;
they matter only where they affected a methodological choice.

Last updated: 2026-10-30.

---

## 0. Source data, OCR and page selection (done before the KG work)

This section records how the 40-page corpus came to exist. It was built before these notes started
(commits 2026-10-08 to 10-24), so it is reconstructed from the scripts and `strike_pages_md/README.md`.

### Source

- *China Mail* (Hongkong), June–July 1925: **50 editions, 496 page images**, scraped from the Hong Kong
  Public Libraries digital collection with `scrape_hkpl.py` into `data/raw/hkpl/china_mail_june_july_1925/`.
  Each edition folder also has the library's own OCR (`metadata.json` → `ocrList`, headlines only, for 193
  of the 496 pages) and `library_indexed_ocr.txt`.

### Why page selection was needed

The good OCR (PaddleOCR-VL) takes **about 3 minutes per page** on the RTX 5080. All 496 pages would take
~25 hours, and most pages are adverts, shipping lists, sport and court news. So every page was first
screened with a fast, inaccurate OCR, and only the pages most likely to be about worker strikes got the
VL treatment.

### Pipeline

1. **Fast OCR of every page** (`ocr_fast.py` → `ocr_fast_out/<page>.txt`). PaddleOCR PP-OCRv5 *mobile*
   detection and recognition models on GPU, no orientation/unwarping steps, about **2 s per page**. Accuracy
   is poor on this print (misreadings like "gtrikes", "unton"), so it is used only for recall.
2. **Fuzzy keyword scoring** (`strike_screen.py` → `strike_screen.csv`, one row per page with score, flag
   and which concepts hit). Page text = fast-OCR text + the library's headline OCR where it exists.
   - Two concept lists. **CORE** = direct strike vocabulary: strike, walkout, boycott, picket, lockout,
     stoppage, "downed tools". **BROAD** = labour/unrest vocabulary (28 concepts): labour, worker, coolie,
     union, wage, agitation, riot, demonstration, mob, communist, propaganda, Shameen, martial law,
     casualties, demands, etc. Full lists in `strike_pages_md/README.md`.
   - `score = 3 × (CORE concepts found) + (BROAD concepts found)`. A concept counts once however many of
     its variants appear, so a long page doesn't win just by repetition.
   - A page is "flagged" if it has any CORE concept or ≥ 2 BROAD concepts (recorded, not used for the
     selection).
3. **Matching built for OCR errors:**
   - lower-case, remove hyphens, map digits `0`/`1` to `o`/`l`, split into letter tokens; adjacent tokens are
     also joined so a split word ("str ike") still matches.
   - edit-distance tolerance by term length: ≤ 4 letters exact, otherwise `max(1, len // 5)` edits.
   - guard against false fuzzy matches: a token is never taken as a misreading of a term if it is an
     ordinary word in the clean VL text (seen ≥ 3 times across the VL pages; 2,911-word vocabulary at
     scoring time), e.g. "onions", "wales", "aviator". Real OCR errors don't occur in that vocabulary.
   - hard skip list for near-misses of CORE terms the vocabulary missed (cricket season): wicket(s),
     ticket(s), picked, pocket(s), packet(s), stroke(s), stripe(s), strife, strive, stride.
4. **Calibration** (`strike_eval.py`) against the 24 pages of 1925-06-01 and 06-02, which already had VL
   text (VL text with a strike regex used as ground truth): every page with an on-topic strike mention was
   flagged; the one miss was a boxing "strike". About 7 of 17 pages without strike terms were also flagged
   (broad words only), so flags are generous; the score is what ranks.
5. **Cutoff: score ≥ 15**, excluding the 24 pages that already had VL output. That leaves **40 pages from 32
   editions (06-03 to 07-30), 21 of them front pages**, listed in `vl_selected_pages.txt`.
6. **VL OCR** (`ocr_vl.py @agent-sandbox/vl_selected_pages.txt` → `ocr_vl_out/`): PaddleOCR-VL pipeline on
   GPU, layout detection + reading order, each block read by the vision-language model; orientation,
   unwarping, chart and seal recognition off. Per page it writes `<page>.md`, `<page>_res.json` (all blocks
   with label, bounding box, reading order; this is what `build_articles.py` uses),
   `<page>_blocks.json` (compact summary) and `<page>_layout_det_res.png` (reading-order overlay).
   `ocr_vl_out/` holds 65 pages in total: the 40 selected, the 24 calibration pages, and a test image.
7. **Corpus copy:** the 40 selected `.md` files were copied to `strike_pages_md/` (image links inside them
   point to `ocr_vl_out/imgs/` and don't resolve from there).

Both OCR scripts call `truststore.inject_into_ssl()`: Norton antivirus re-signs HTTPS traffic, which
Python's bundled CA list rejects (same cause as the SSL problem in section 3).

### Coverage and limits of the selection

- Full run: 496 pages scored, 328 flagged, 217 with a CORE hit. The ≥ 15 cutoff keeps only the densest
  40. **About 180 pages with a CORE hit are not transcribed**, plus pages flagged on broad terms only.
- Pages per cutoff (total / still to transcribe, ~3 min each): ≥ 12: 76 / 34; ≥ 10: 101 / 57; ≥ 8: 137 / 92; ≥ 5: 215 / 169; ≥ 2: 328 / 275; all: 496 / 432. The README's "pages left" figures (74 / 97 / 132 / 209 / 315) include the 40 selected pages; they only exclude the calibration pages. Corrected 2026-10-30 after an earlier misreading.
  At ≥ 8 that is ~4.6 h of VL OCR. 64 pages have VL text: the 40 selected + 24 of the 28 calibration pages (06-01/02). One calibration page also scores ≥ 15.
- A CORE hit can be off-topic (e.g. a London telegraph messengers' strike, 06-01 p10). A page can also
  cover the strike without any of these words and be missed.
- The corpus is biased toward pages *dense* in strike vocabulary: front pages and strike round-ups.
  Short strike items on inner pages, and pages about consequences (food prices, shipping) that don't
  use the vocabulary, are under-represented. Worth stating when presenting results.
- Re-running `strike_screen.py` now would use a larger VL vocabulary (64 pages, not 24), so scores can shift
  slightly; `strike_screen.csv` is the record of the scores actually used. It needs `rapidfuzz` and was run
  from a separate venv, not the project `.venv`.
- Other layout experiments exist in the sandbox (`ocr_structure.py`, `as_layout.py` with
  `as_layout_out/`, `ocr_vl_crops.py`: AmericanStories layout regions read by PaddleOCR-VL). They were not
  used for the corpus, and their results aren't recorded here.

---

## 1. Starting point

- Corpus: `strike_pages_md/`: 40 PaddleOCR-VL transcriptions of *China Mail* pages, 3 June – 30 July
  1925, chosen by strike-keyword score (section 0). About 123k words; 2,400–4,200
  words per page; roughly half of each page is advertising.
- Hardware: RTX 5080, 16 GB VRAM. No local LLM runtime installed yet.
- User's plan: (1) causal relation extraction with a local LLM (Llama / Mistral), (2) argument
  clustering (SimCSE + k-means / HDBSCAN), (3) knowledge graph with a visualiser.
- Advice given at the start (accepted in principle):
  - add a step 0: split pages into articles, drop ads, keep provenance (page, date, headline, source).
  - record `asserted_by` for every relation. The *China Mail* is a British colonial paper, so a link
    is a claim made in print, not an established cause.
  - use current embedding models (bge / e5 / gte) instead of SimCSE; prefer HDBSCAN to k-means.
  - expect clustering to group opposites (e.g. "strike began" / "strike ended").

## 2. Proof-of-concept demo (`demo_kg/`)

User asked for a quick visual demo to send to their professor, and asked Claude to do the extraction
itself instead of a local LLM.

**Pages used (8):** 1925-06-16 p1, 06-20 p1, 06-23 p1, 06-27 p2, 06-29 p2, 06-30 p2, 07-02 p2, 07-03 p1
(the start of the Canton–Hongkong strike).

| Step | What | Result |
|---|---|---|
| Extraction | Claude read the pages and wrote `relations.jsonl` (cause, effect, verbatim quote, date, headline, `asserted_by`, `kind` = explicit / implicit / counterfactual) | 105 relations; script check: **all 105 quotes appear verbatim** in the OCR text |
| Clustering | `cluster.py`: 157 distinct cause/effect phrases → `bge-small-en-v1.5` (fastembed) → scikit-learn HDBSCAN, `min_cluster_size=2` | 29 multi-phrase groups; changing `cluster_selection_epsilon` made no difference |
| Review | Claude reviewed the clusters and wrote `nodes.json` | kept 9 groups, **split 20**, almost all because opposites were grouped ("Central Market closed" / "reopens", "pirate raid" / "pirates repelled") |
| Graph | `build_graph.py` → `graph.json` + viewer | **100 event nodes, 91 edges**. Biggest hubs: general strike (13 quotes), seamen's strike (9), intimidation (9), shipping deadlock (8), strike spreading to other trades (8) |

- Main lesson: embeddings group short phrases by topic, not by direction. Clustering needs a
  polarity step or an LLM review (now in `KG_PLAN.md` Stage 2).
- Viewer: Cytoscape.js page; clicking an arrow shows the 1925 quotes; theme filters; date slider;
  "hide isolated pairs" option. Contested claims (who fired first at Shameen) are kept as separate,
  contradicting edges.
  - Published privately on claude.ai: https://claude.ai/artifact/GpySVkvuy3Ko8jx2RPkA2o
    (must be shared from its Share menu before others can open it).
  - Local copy: `demo_kg/causal_kg_demo_local.html` (full HTML document; needs internet for
    Cytoscape and Google Fonts). `build_graph.py` writes both versions.
- Caveat stated on the page: extraction and review were done by Claude and have not been hand-checked.

## 3. Environment notes

- `agent-sandbox/.venv-kg`: separate venv for this work, created from the uv-managed **Python 3.13**
  (`C:\Users\georg\AppData\Roaming\uv\python\cpython-3.13-windows-x86_64-none`). A first attempt with the
  default Python 3.15 failed: onnxruntime (needed by fastembed) has no 3.15 wheels.
- Packages: `fastembed`, `scikit-learn`, `numpy`, `truststore`, `pillow`.
- **SSL:** Hugging Face model downloads fail certificate verification with the default certifi
  bundle on this machine. `truststore.inject_into_ssl()` (Windows certificate store) fixes it;
  `demo_kg/cluster.py` calls it.
- Node.js is not installed (no local JS syntax check).
- **Ollama 0.40.9** installed 2026-10-30 via `winget install --id Ollama.Ollama -e --source winget` (per-user,
  `%LOCALAPPDATA%\Programs\Ollama`; models in `C:\Users\georg\.ollama\models`). The tray app failed to start
  when launched from the agent session ("Unable to init instance"), so the server was run headless with
  `ollama serve`; it detects the RTX 5080 via CUDA. After a reboot, start the Ollama app or `ollama serve`.
- Model downloaded: **`qwen3.5:9b-q8_0`** (10 GB, id `a8ee95bc3592`), the first extraction candidate. Chosen
  over `qwen3.8` (only a 27B / 18 GB version, which doesn't fit in 16 GB VRAM) and over the Qwen3.5 27B/35B
  versions (17–22 GB). Other screen candidates: the same model with thinking on, `qwen3.5:35b-a3b`
  (mixture-of-experts, partly in system RAM; 31 GB RAM available), `qwen3:14b`, and a non-Qwen model of similar size.
- Don't run Ollama and PaddleOCR-VL on the GPU at the same time: VL OCR uses ~9 GB, the 9B q8 model ~10 GB
  plus context.

## 4. Full-pipeline plan

Written to `KG_PLAN.md`. Stages: 0 corpus (more VL OCR + articles), 1 local-LLM extraction (Ollama,
JSON schema, quote verification), evaluation set before the full run, 2 normalisation + polarity-aware
clustering + LLM review, 3 graph + GraphML/Neo4j + viewer upgrades.

**Decisions still open for the user:**
1. Corpus size: stay at 40 pages, or VL-OCR pages with score ≥ 8 (137 total, 92 more, ~4.6 h)?
2. Who hand-annotates the gold set; is ~15 articles enough?
3. Scope of "causal": include government measures and their effects, or only the strike's own causes and effects?
4. Neo4j needed, or HTML viewer + Gephi enough?

**Discussion: why split pages into articles?** Not strictly necessary: a page (3–6k tokens) fits a
14B model's context. Reasons to split: smaller models miss relations in long inputs; headline/source
attribution is more reliable per article; dropping ads roughly halves model time. Suggested to test
whole-page vs per-article extraction on the evaluation set.

## 5. Column splicing in the OCR, and article reconstruction

### Problem

PaddleOCR-VL's reading order sometimes jumps between columns, so its `.md` splices unrelated
paragraphs together. Example (06-16 p1): the British Cigarette Co. strike paragraph sits inside the
Shanghai murder story, and its continuation is 20 blocks earlier. Because of this, the demo's relation
for that strike was filed under the wrong headline ("Hankow Quiet").

- Measured over the 40 pages: **107 of 2,117 (5.1%)** transitions between substantial text blocks
  in PaddleOCR order leave the column flow. Worst page 06-10 p1 (14 of 40); clean editorial pages have 0.
- What it breaks: false cause/effect links across a splice, wrong headline/source attribution,
  missed links when one item is split apart.
- Data available: `ocr_vl_out/<page>_res.json` → `parsing_res_list` gives every block's label,
  bounding box and reading-order position; `*_layout_det_res.png` shows the model's order.

### `build_articles.py`

Rebuilds article-ordered markdown from block geometry, ignoring PaddleOCR's order.

```
agent-sandbox/.venv-kg/Scripts/python agent-sandbox/build_articles.py      # all 40 pages
```

Output in `articles_md/`: `<page>.md` (readable), `<page>_articles.png` (blocks outlined and numbered
per article; colours repeat after 12, go by the numbers), `articles.jsonl` (page, date, article,
headline, parent, parent_headline, block ids, columns, text, is_ad).

Rules, and why each was added (in the order problems were found):

| Rule | Problem it fixed |
|---|---|
| Columns from **left edges** of ordinary-width text blocks; a small cluster overlapping a bigger one is dropped | Clustering by block centres merged two columns on 06-16 (two blocks start mid-column), interleaving two articles line by line |
| CAPS title blocks = headline; consecutive headline lines stack (headline + decks) | — |
| Short CAPS text blocks (< 60 chars) count as headlines or decks | Layout model labels some headlines as body text ("HOME POLICY.", 06-10) |
| Vertical gap > **90 px** within a column starts a new article (unless the article has no body yet) | Layout model misses some headlines entirely (06-10: "SHANGHAI TROUBLE. / QUESTIONS IN HOUSE OF COMMONS."); article 1 swallowed 1,014 words. Gap statistics: text→text gaps median 3 px, p90 63 px |
| Continue into the next column only if the text reads on (previous ends mid-sentence or next starts lowercase) | Ad columns and unrelated items merging into news |
| Headline directly above a picture belongs to the picture and its caption; the running article continues past it. Captions and "Photo by…" credits stand alone | "LAST NIGHT'S HEAVY RAIN" (06-16) took over the drugs-case text below the photo; a two-column caption dragged a continuation into the wrong article |
| Front page: everything above the masthead line (issue no., price, date line) is set aside as furniture | Date line became a headline; corner ad text leaked into "CANTON FIGHTING" (06-10) |
| Mixed-case subheads start a **section** that keeps its parent headline as context | 06-20: "SHANGHAI TROUBLE." absorbed 1,600 words across six columns; the paper runs separate items under mixed-case subheads ("Chinese Banks to Open", "Queen's College") |
| **Continuation repair**: a block starting mid-sentence right after a finished sentence (or opening an unheadlined unit) moves, with what follows it, to the nearest article to its left that ends mid-sentence | Articles that run off a column bottom and resume part-way down a later column (under another article) were glued onto that other article |
| Ads: an article is an ad unless it has a prose block (≥ 25 words, < 35% capitals) and fewer than 4 ad words per 100 words | — |

### Results (40 pages)

| Measure | PaddleOCR `.md` | Rebuilt |
|---|---|---|
| Transitions breaking column flow | 107 / 2,117 (5.1%) | 40 / 1,353 (3.0%) (measured before continuation repair) |
| Largest single news unit | — | 933 words (1,600 before sections) |
| News units / median size | — | 639 / 126 words |
| News text without headline or parent | — | 8% |

**Is body text grouped consistently?** (User's priority: body text matters, headlines less so.)

| Error | Flagged | Real rate (hand-checked samples) |
|---|---|---|
| Wrong text glued into an article (sentence cut, next block starts fresh) | 70 of 1,293 joins (PaddleOCR order: 213 of 2,112) | ~1 in 3 → **~2% of joins (~25)**; about half are ad copy glued into news |
| Fragment glued after a finished sentence | 7 (36 before continuation repair) | — |
| Article cut off, rest elsewhere (ends mid-sentence) | 79 of 639 (106 before repair) | ~2 in 3 → **~8% of articles (~50)** |

Repair spot check: 2 moves clearly correct ("…in the hands of the Communists. Trenches" → "had been
dug…"; "Particulars have been obtained" → "of the casualties…"); 2 on 06-04 p1 unclear (garbled OCR).

**Conclusion:** stories are split far more often than mixed. For extraction this means missed relations
(cause in one part, effect in the other) rather than false ones. Combined with the planned rule that a
quote must lie inside one block or two neighbouring blocks, the grouping is safe to extract from.

**Known remaining errors:**
- Wrong parent headline for some sections (06-20: "River Steamers", "Chinese Banks to Open" under SHANGHAI
  TROUBLE instead of LOCAL STRIKE). Body text intact.
- Layouts no rule handles: the cigarette-strike paragraph (06-16 p1) continues in the column to its *left*.
- Prose-like ads pass the filter ("K" Shoes).
- Headlines the layout model never boxed (~15–20% on the busiest front pages) leave "no headline" units.
- Only 06-10 p1, 06-16 p1 and 06-20 p1 were inspected closely; inner pages (p2+) have a different layout
  and have only been checked through the statistics above.

**Agreed next step:** keep the grouping as is for now (option 1). When Ollama is set up for extraction,
add an LLM check for the ~80 cut-off articles: show the cut-off ending and the 2–3 mid-sentence
fragments nearby, ask which continues it (option 2). `KG_PLAN.md` Stage 0 still describes heading-based
splitting and should be updated to use `articles_md/articles.jsonl`.

## 5b. HKPL scrape: China Mail, August and September 1925

- Dry run (`hkpl_dry_run.py`): the search URL from the user, with the date range 1925-08-01 to 1925-10-01,
  returned 53 unique records. The end date is inclusive, so 1925-10-01 was in the results. The URL was
  changed to end 1925-09-30, which returns 52 records (1925-08-01 to 1925-09-30). No October issue is included.
- Environment: `selenium` was missing from `.venv-kg`, so it was installed (selenium 4.52.0, pillow 13.0.0).
  Chrome is not installed; the scraper falls back to Edge, which works.
- Batch command: `scrape_hkpl.py --search-url <URL ending 1925-09-30> -o ../data/raw/hkpl/china_mail_aug_sep_1925 --no-pdf`.
  Log: `hkpl_aug_sep.log`. `--no-pdf` matches the June–July folder, which has no PDFs.
- Output: `data/raw/hkpl/china_mail_aug_sep_1925/`, one folder per issue (`NPCM1925MMDD_The_China_Mail_1925-MM-DD`).
- Queue (`hkpl_queue.py`, log `hkpl_queue.log`): runs after the Aug–Sep batch finishes. It covers 12 months,
  Apr 1925 to Mar 1926. June–Sep 1925 are already done or queued, so the queue runs the other 8 months:
  Apr, May, Oct, Nov, Dec 1925 and Jan, Feb, Mar 1926. Each month is one `scrape_search_results` call with
  the date range set to that month, written to `data/raw/hkpl/china_mail_<mon>_<year>/`, with `--no-pdf`.
  Pauses: 30 s between issues and 3 s between pages. `scrape_search_results` gained a
  `delay_between_pages` parameter so the page pause can be set; the default is still 0.5 s.
  Apr 1926 is not included, because the request was read as 12 months (Apr 1925 to Mar 1926).
- Aug–Sep batch finished: 52 of 52 issues scraped, 0 failed. `hkpl_verify.py` checked every issue's page
  images against `metadata.json` `totalPages`: 52 issues, 0 mismatches.
- Queue recovery: the queue (`hkpl_queue.py`) had been waiting for the Aug–Sep batch but had written nothing to
  its log for about 10 minutes, even though the completion line was present. The cause was not confirmed. I
  stopped the waiting processes and relaunched the queue with the same command (appending to `hkpl_queue.log`).
  It started with April 1925.
- `pipeline_new_scrapes.py` (not written by this session) was running when this was checked. It OCRs new
  pages as the scrape writes them and waits while `hkpl_queue.py` is running. It was left untouched.

## 5c. Extending VL OCR: score ≥ 8 for June–July, then all newly scraped months

**Decision (user, 2026-10-30): VL-transcribe every page scoring ≥ 8**, first for June–July, then for each
newly scraped month, with the same scoring and cutoff.

- **June–July:** 92 pages scored 8–14 and had no VL text (list: `vl_pages_score8.txt`, highest score
  first). VL run started 2026-10-30 ~19:30, log `ocr_vl_score8.log`, ~3 min/page. With it, June–July has
  VL text for all 137 pages scoring ≥ 8, plus the 24 calibration pages.
- **Why the cutoff is 8:** a compromise between coverage and VL time (about 4.6 h for June–July). It is
  well below the ≥ 15 used for the first 40 pages, so far fewer moderately relevant pages are missed.
  Even so, 217 June–July pages have a CORE strike term, and ≥ 8 covers 137 pages in total. Pages that
  mention a strike only once, on an otherwise unrelated page, are still excluded.
- **Scoring new months the same way** (`strike_screen_batch.py` → `strike_screen_batch.csv`):
  `strike_screen.py` decides which fuzzy matches are OCR errors by checking a "real word" vocabulary built
  from *all VL text on disk when it runs*. That vocabulary grows as pages are transcribed (24 calibration
  pages at the June–July scoring; 156+ now), so rerunning it would score new months under different
  conditions. `strike_screen_batch.py` reuses the same matching code but **fixes the vocabulary to the 24
  calibration pages** (06-01/02), scores every collection, and leaves `strike_screen.csv` untouched.
  Check: rescoring the 496 June–July pages with it reproduces `strike_screen.csv` exactly (0 differences).
  So a score of 8 means the same thing in every month.
- **Unattended pipeline** (`pipeline_new_scrapes.py`, log `pipeline_new_scrapes.log`), started 2026-10-30
  20:46 while the user was away. It waits for the June–July VL run, then cycles:
  1. fast-OCR any edition the scraper has finished (no file written for 10 min);
  2. rescore;
  3. VL-OCR the next 20 pages with score ≥ 8, highest score first across all months;
  4. repeat until the scraper (Aug–Sep, then the 8-month queue) has stopped and nothing is left.

  Failure handling: a failing fast-OCR batch is retried page by page; a page that fails twice in either
  step is skipped and listed in `pipeline_failed.txt`. Creating `pipeline.stop` ends it cleanly.
  Separate logs per step: `ocr_fast_batch.log`, `strike_screen_batch.log`, `ocr_vl_batch.log`.
- **Scope note:** the queue covers Apr 1925 – Mar 1926, so the VL backlog will grow over several days.
  It is processed in score order across all months, not month by month. A month's VL coverage is
  complete only when the pipeline log reports "done".

## 6. File index (all in `agent-sandbox/`)

| Path | What |
|---|---|
| `scrape_hkpl.py`, `src/china_causal_kg/ingestion/hkpl_scraper.py` | HKPL scraper (page images, library OCR, metadata) |
| `ocr_fast.py`, `ocr_fast_out/` | Fast PP-OCRv5 mobile OCR of all 496 pages (screening only) |
| `strike_screen.py`, `strike_screen.csv`, `strike_eval.py` | Strike-relevance scoring and its calibration |
| `vl_selected_pages.txt` | The 40 pages chosen for VL OCR (score ≥ 15) |
| `vl_pages_score8.txt`, `ocr_vl_score8.log` | The 92 further June–July pages scoring 8–14, and their VL run |
| `vl_cutoff_table.txt` | Pages per score cutoff for June–July (total / already VL / to do) |
| `strike_screen_batch.py`, `strike_screen_batch.csv` | Scoring for all collections with the frozen June–July vocabulary |
| `pipeline_new_scrapes.py`, `pipeline_new_scrapes.log`, `pipeline_failed.txt` | Unattended fast OCR → score → VL (≥ 8) for new scrapes |
| `ocr_vl.py`, `ocr_vl_out/` | PaddleOCR-VL OCR (65 pages: 40 selected + 24 calibration + test) |
| `strike_pages_md/` | The 40 VL `.md` files used as the corpus, with selection README |
| `KG_PLAN.md` | Full pipeline plan |
| `agent_notes.md` | This file |
| `demo_kg/README.md` | How to rerun the demo |
| `demo_kg/relations.jsonl` | 105 Claude-extracted relations (8 pages) |
| `demo_kg/cluster.py`, `clusters.json` | Embedding + HDBSCAN |
| `demo_kg/nodes.json` | Reviewed event nodes |
| `demo_kg/build_graph.py`, `graph.json` | Graph build |
| `demo_kg/viewer_template.html`, `causal_kg_demo.html`, `causal_kg_demo_local.html` | Viewer (template, claude.ai version, local version) |
| `build_articles.py` | Article reconstruction from layout blocks |
| `articles_md/` | Rebuilt per-page markdown, overlay images, `articles.jsonl` |
| `.venv-kg/` | Python 3.13 venv for the above |
