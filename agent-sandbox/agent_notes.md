# Agent notes

Log of data and decision-making for the causal-knowledge-graph project, kept so that everything needed
for the **final writeup** is in one place: what was done, the numbers measured, the options considered,
what was chosen and why, and what is still open. Work done with Claude (Opus 5.5) in `agent-sandbox/`.
The forward-looking plan is in `KG_PLAN.md`. Purely technical setup details (section 3) are kept short;
they matter only where they affected a methodological choice.

Last updated: 2026-11-06.

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
- **Memory stop and restart (2026-10-30 night → 2026-10-31 15:21).** Overnight, all background jobs were
  killed because system RAM ran critically low: the June–July VL run (40 of 92 pages done, all saved), the
  waiting pipeline, the idle Ollama server, and the scrape queue. The queue stopped after Oct 1925 issue
  10-03. The likely cause: one `ocr_vl.py` process had been kept open for the whole 92-page list, and its
  RAM grew to about 10 GB by page 28 and kept growing.
  Changes before restarting:
  - VL batches cut from 20 pages to **10**. Each batch is a fresh process, so its memory is released
    every ~35 min.
  - A **RAM guard** in the pipeline: a batch starts only with ≥ 4 GB free, and is ended early if free RAM
    drops below 3 GB. Pages already finished are kept, and the stop does not count as a page failure.
  The 52 remaining June–July pages need no separate run: they are in the pipeline's score-ordered backlog.
  The queue was relaunched with `.venv-kg` (the root `.venv` lacks selenium). Already complete issues
  are skipped. Ollama stays off until OCR is done.
- **Model cache failure and June–July priority (2026-10-31 16:09–16:44).** The first VL batch failed with
  "Permission denied" on PaddleOCR's model files. 7 of the 10 folders in `~/.paddlex/official_models`
  (including both VL models) became unreadable. Files there reported "not found" yet refused to open,
  which points to them being stuck pending deletion. Disabling Norton features did not help. The pipeline
  was paused first so pages would not be wrongly marked as failed (none were).
  Fix: the pipeline now sets `PADDLE_PDX_CACHE_HOME=~/.paddlex_cache2`, where the VL models
  (PaddleOCR-VL-1.6 1.8 GB, PP-DocLayoutV3 126 MB) were re-downloaded. A one-page test (06-05 p.1) ran
  normally. The re-downloaded models are PaddleX's official ones under the same names. Output was not
  compared byte-for-byte with an earlier page.
  **User priority: June–July VL first.** The VL backlog is now sorted June–July first, then by score.
  The 52 remaining June–July pages run before any other month.
- **Scrape queue finished (2026-10-31 ~18:00).** Apr 1925 – Mar 1926 are all scraped.

  | Collection | Issues | Pages |
  |---|---|---|
  | Apr 1925 | 25 | 341 |
  | May 1925 | 25 | 377 |
  | June–July 1925 | 50 | 496 |
  | Aug–Sep 1925 | 52 | 566 |
  | Oct 1925 | 27 | 335 |
  | Nov 1925 | 25 | 301 |
  | Dec 1925 | 26 | 312 |
  | Jan 1926 | 25 | 302 |
  | Feb 1926 | 23 | 279 |
  | Mar 1926 | 27 | 324 |
  | **Total** | **305** | **3,633** |

  `hkpl_verify.py` found one gap: page 3 of 1925-12-05, which had failed with a network error mid-run.
  It was re-downloaded on its own (`scrape_document`, same 3 s page delay). After that, every collection
  has 0 mismatches against `metadata.json` `totalPages`.
- **VL pass complete (2026-11-01 13:46).** The pipeline exited normally: "done: scraper stopped, nothing
  left". All **3,633** pages are fast-OCR'd and scored, and **568** score ≥ 8. Every one of the 568 now
  has VL text, with **0 failed pages**. There are 587 VL pages on disk in total; the other 19 are the
  calibration pages and earlier selections below the cutoff. June–July finished first, at
  2026-10-31 20:38. The other months then ran at about 2 min/page, in 10-page batches. The RAM guard
  never triggered: free RAM stayed at ~22 GB.
- **Extension to Apr–May 1926 (user, 2026-11-01).** The study window is now **Apr 1925 – May 1926**
  (14 months). Before, it ended at Mar 1926, read as 12 months from Apr 1925. Apr and May 1926 are
  scraped and OCR'd exactly as the other months:
  - `hkpl_queue.py 1926-04 1926-05`: the queue now accepts months as arguments. Same search URL and
    filters, 30 s / 3 s delays.
  - `pipeline_new_scrapes.py`: fast OCR, then scoring with the frozen vocabulary, then VL for score ≥ 8.
  Started 14:02.

  Results:
  - Scrape done at ~15:15. Apr 1926: 25 issues, 300 pages. May 1926: 26 issues, 317 pages. 0 failed
    downloads, 0 page-count mismatches.
  - Pipeline done at 19:57, 0 failed pages. Apr 1926 has 44 pages scoring ≥ 8; May 1926 has 77. All have
    VL text.
  - **Full corpus: 356 issues, 4,250 pages, all fast-OCR'd and scored. 689 score ≥ 8, all VL-transcribed**
    (708 VL pages on disk).
  - May 1926 has the most ≥ 8 pages of any single month, and more than Apr 1926. This may reflect strike
    or boycott news in that period, but it has not been checked.
- **Extension to Jun–Nov 1926 (user, 2026-11-01 20:05).** The study window is now **Apr 1925 – Nov 1926**
  (20 months). Same scrape command and standards (`hkpl_queue.py 1926-06 … 1926-11`), and the same
  pipeline: fast OCR, frozen-vocabulary scoring, VL for score ≥ 8.
  - Scrape done at ~23:40. 157 issues, 1,890 pages. 0 failed downloads, 0 page-count mismatches.
  - Aug, Sep and Oct each have exactly 26 issues and 313 pages. This was checked: each folder holds only
    its own month's dates, with no duplicate images. It is a coincidence; issues are mostly 12 pages.
  - Early scoring (1,638 of 1,890 pages scored): **411 score ≥ 8 (25%)**. Compare 16% for Apr 1925 – May
    1926 (689 of 4,250). The strike–boycott ran until Oct 1926, so this may be real coverage, but it has
    not been checked. It roughly doubles the VL work to ~11 h.
  - Pipeline done 2026-11-02 09:48, 0 failed pages. **Final for Jun–Nov 1926: 462 of 1,890 pages score
    ≥ 8 (24%)**, all VL-transcribed. By month: Jun 81, Jul 78, Aug 77, Sep 79, Oct 83, Nov 64.
  - The rate stays high in Nov 1926, after the boycott ended in Oct 1926. So the higher rate may not be
    strike coverage alone; for example, other labour news could match BROAD terms. Check before treating
    these months as comparable to 1925.
  - **Full corpus, Apr 1925 – Nov 1926: 513 issues, 6,140 pages, all fast-OCR'd and scored. 1,151 score
    ≥ 8, all with VL text** (1,170 VL pages on disk).
- **VL below the cutoff (user, 2026-11-02 ~09:55): expand the score scope, in chronological order, until
  the user says stop.** `pipeline_new_scrapes.py --tiers 5,2,1,0` works through one score band at a time,
  highest band first. Within each band it goes in date order, then page order. If it is stopped at any
  point, every higher band is complete and the current band is complete up to a known date. Pages still
  without VL text:

  | Score band | Pages | Est. time at ~2 min/page |
  |---|---|---|
  | 5–7 | 964 | ~32 h |
  | 2–4 | 2,010 | ~67 h |
  | 1 | 1,268 | ~42 h |
  | 0 | 728 | ~24 h |
  | **Total** | **4,970** | **~7 days** |

  The bands are an ordering choice for interruptibility, not a new selection rule. The analysis can still
  use any cutoff, since every page keeps its score.
- **Replaced (user, 2026-11-02 ~15:25): VL every page of June–July 1925 instead.** The band run was
  stopped after a few minutes, during its first batch, with no pages lost. The new run,
  `pipeline_new_scrapes.py --only china_mail_june_july_1925 --tiers 0`, takes all **340 remaining
  June–July pages** regardless of score, in date order. 156 of the 496 already had VL text. When done,
  June–July 1925 will be **fully VL-transcribed (496/496)**. This makes it the core corpus that does not
  depend on the score screen: no page is excluded by the keyword cutoff. Other months stay at score ≥ 8.
- **Then full VL for every month (user, 2026-11-02 ~15:35).** `vl_full_queue.py` waits for the June–July
  run, then VLs every page of each group in this order, each group in date order:

  | Order | Group | Pages | Without VL |
  |---|---|---|---|
  | 1 | Aug–Sep 1925 | 566 | 411 |
  | 2 | Apr–May 1925 | 718 | 671 |
  | 3 | Oct–Nov 1925 | 636 | 559 |
  | 4 | Dec 1925 – Jan 1926 | 614 | 546 |
  | 5 | Feb–Mar 1926 | 603 | 518 |
  | 6 | Apr–May 1926 | 617 | 496 |
  | 7 | Jun–Jul 1926 | 639 | 480 |
  | 8 | Aug–Sep 1926 | 626 | 470 |
  | 9 | Oct–Nov 1926 | 625 | 478 |

  That is 4,629 pages after June–July, about 6½–12 days at 2–3¾ min/page. The order works outward from
  the strike's core months. If the run stops early, the corpus is complete VL for a contiguous span
  around June 1925.
- **Paused 2026-11-02 21:07 for a computer shutdown (user request).** June–July 1925 was at 277/496 VL
  pages, through 06-16 p.2. All processes were stopped and `pipeline.stop` was left in place. To resume,
  delete `pipeline.stop` and run `vl_full_queue.py` after restarting `pipeline_new_scrapes.py --only
  china_mail_june_july_1925 --tiers 0`. Pages are skipped once they have `_blocks.json`, so a page cut off
  mid-run is simply redone.

## 5d. Planning local-LLM extraction for June–July 1925 (2026-11-06)

User asked for a plan to extract causal relations from each June–July 1925 article with the installed
Qwen. Plan: `EXTRACTION_PLAN.md`. It supersedes `KG_PLAN.md` Stage 0b and the Stage 1 model comparison and
throughput estimate. Not yet approved; four decisions are open there.

**State on disk:** 277 of 496 June–July pages have VL text; 219 are missing and `pipeline.stop` is in place.
`articles_md/articles.jsonl` still covers only the first 40 pages.

**Article builder on the 277 pages** (output to a temp folder, repo files unchanged): 275 pages processed,
2 crashed in `find_columns` (06-02 p8, 06-03 p12; no ordinary text blocks). 8,002 units, 3,813 news, 622k
news words, median 110, p90 344, max 3,025; 35 over 800 words; 610 news units have no headline; 951 (25%)
contain a strike-related term. These pages aren't a random sample: they are all of 06-01 to 06-13 plus
high-scoring pages after that.

**Found while reading `build_articles.py`:** `plain_text()` leaves out `source` and `dateline` items, so
`articles.jsonl` has no "(Reuter's Service.)" lines. This must change before extraction, as it would
weaken `asserted_by`.

**Possible date problem, unconfirmed:** the 06-26 issue has 24 pages against 2–8 for its neighbours, with
"STRIKE EDITION" mastheads on at least pp. 1, 6 and 12, and the collection has no 06-15, 06-18 or 06-25
issue. The file may bundle several editions under one date.

**Qwen probe** (`extraction_probe/`; `qwen3.5:9b-q8_0`, temperature 0; 5 strike-dense demo articles, plus
2 no-strike articles in the first run). "Demo found" is quote overlap with Claude's unverified relations,
not a true recall figure.

| Setup | Time/article | Relations | Verbatim | Demo found |
|---|---|---|---|---|
| No thinking, zero-shot, schema | ~4 s | 12 | 12 | 8/24 |
| No thinking, 3-shot, schema | ~5 s | 12 | 12 | 9/24 |
| Thinking, schema, 6k cap | 73 s | 0 | – | 6 of 7 calls hit the cap and gave no JSON |
| Thinking, no schema, 14k cap (3 articles) | ~90 s, ~7,500 tokens | 16 | 14 | 9/18 (no-thinking: 6/18) |

Zero-shot credited named speakers' claims to "China Mail"; few-shot corrected this. The few-shot run
flipped one counterfactual (quote correct, "failing to co-operate → loss of life avoided"), which is why
the plan adds a verifier pass. Both no-strike articles returned no relations (zero-shot). Thinking on all
articles would take ~7 days, so it is held back as an option for strike-term articles only.

## 5e. Extraction plan revised: score ≥ 8 pages, reasoning-first schema (user, 2026-11-06)

**Decisions (user):**
- Run extraction only on pages scoring ≥ 8, not every article. This replaces the every-article scope
  proposed in 5d.
- No thinking.
- Model output is `reasoning`, `quote`, `cause`, `effect`, in that order. `reasoning` goes first because it
  should improve the accuracy of the later fields. Rows wrap this as `extraction` beside `page`, `date` and
  `headline`.
- No attribution field. `kind` and `hedged` are also left out, since they aren't in the requested format.

**Consequences:**
- All 137 pages have VL text (61 June, 76 July), so extraction doesn't depend on the 219 missing pages. The
  two pages that crashed `find_columns` score 0, so they are out of scope. Of the 06-26 issue only p2 scores
  ≥ 8, and its fast OCR reads "JUNE 26", so the possible date problem in 5d barely touches this run.
- Without `asserted_by`, the `source`/`dateline` fix from 5d is no longer needed for this run.
- The score is per page, so all news items on those pages are in scope: 1,995 units, 343k words, median 120,
  p90 366, max 2,755, 17 over 800 words, 198 without a headline. 732 (37%) contain a strike-related term.
  Whether to narrow to those 732 is open.
- `KG_PLAN.md` calls `asserted_by` mandatory, and `demo_kg/build_graph.py` and the viewer use it and `kind`.
  Stage 3 needs adjusting; attribution could be added later in a separate pass over saved quotes.

**Probe of the new format** (`extraction_probe/probe3.py`, same 5 demo articles, no examples): reasoning
came first in all 8 outputs (Ollama's JSON schema keeps the order). ~4 s per article, 8 relations, 8 verbatim,
6 of 24 demo quotes found, against 8 of 24 for the earlier schema with no examples. Nothing was returned for
"LOCAL STRIKE:" (3 demo relations). Both counterfactuals came out the right way round, including the one
the earlier few-shot run reversed, so the verifier pass was dropped from the plan and kept as a fallback if
the gold set shows reversed arrows. Sample too small to judge the format's effect on recall.

**Estimated run time:** 2–3 h for 1,995 articles at 4–5 s each, down from 8–12 h for every article.

## 5f. v1 extraction target, prompt and tests (user, 2026-11-06)

**Decisions (user):** extraction runs only on strike-term articles on the ≥ 8 pages. No gold set for now: this
is v1, and speed matters. The demo relations are shaky, built for an illustrative graph, so prompt work must not
aim to match them. The purpose is claims the paper made **directly and clearly**. The definition was settled
through real examples in place of more rigorous prompt optimisation; the full table of rulings is in
`EXTRACTION_PLAN.md`. Summary: a stated causal link with a clearly named cause and effect. Included:
reported speech, hedged claims, counterfactuals about past events, actions against a named threat, protests or
replies about something, justifications, "this" resolved from the previous sentence, causes unrelated to the
strike. Excluded: sequence alone, side-by-side events, causal verbs with no clear cause, predictions and
conditionals, denied links, readers' letters. Cause and effect are short cleaned-up phrases.

**Term filter check:** the 732 figure in 5e came from an improvised regex. It keeps 48 of 59 demo articles (89
of 104 quotes). With headlines 761 articles (91 quotes). CORE only 435 (66). CORE + BROAD 926 (94). Choice open.

**Recall experiment** (`extraction_probe/recall_exp.py`, 56 demo articles, quote-span overlap with demo).
Superseded as a target by the rulings, but kept as a record. Claims / verbatim / demo quotes found of 98 / s per
article: V0 current prompt 45 / 42 / 14 / 3.3; V1 recall prompt 100 / 89 / 36 / 4.2; V2 + examples 157 / 135 /
55 / 4.8; V3 + chunks 190 / 161 / 61 / 7.9; V4 + second extraction pass 197 / 170 / 60 / 7.7. At the time of the
by-kind check, V0 found 9 of 78 "explicit" demo quotes, so its low score was not selectivity. 55 of those 78
contain no cue word from a rough list, so the demo's "explicit" label is loose.

**v1 prompt and rulings test** (`prompt_v1.py`, `rulings_test.py`, `verify_test.py`): 12 sentences to extract and
8 to skip from the user's rulings, none used as prompt examples. The first harness counted any overlap with the
sentence and gave false passes; scoring now requires the ruling's marker text in the quote. Whole article 9/12
extract, 3/8 skip; chunks 9/12, 4/8. Most failures were claims that should have been skipped, so a per-claim
check was added (3.4 s per claim): 8/8 skip for both, with extract unchanged. Each setup missed a different 3,
so the plan runs both: 11/12 extract, 8/8 skip, 19/20. This is optimistic, since the prompts were written from
these rulings and the check quotes some of their wording.

**Check removed (user, 2026-11-06).** The user chose not to use the per-claim check for now, after noting it can
only lower recall. v1 runs both extractions and merges them. On the rulings test that scores 11/12 extract and 3/8
skip, 14/20. Claims the rulings exclude will appear in the output; in the test 5 of the 8 "skip" sentences were
extracted (78 claims, 61 unique quotes, across the 15 articles). The check prompt is kept and could be run on the
saved relations later. Estimated run time drops to ~3.3 h for 926 articles, ~2.6 h for 732.

**Merge rule for combining runs** (`extraction_probe/merge_test.py`, 78 test claims, within one article only).
Identical quote: 78 → 61, misses the same claim quoted with a different span. Overlapping quote: 78 → 50, but
merges different links from one passage (four links in the "unsettled conditions" passage became one).
Overlapping quote (`rapidfuzz` partial ratio ≥ 90) plus similar cause and effect (token-set ratio ≥ 60 on each):
78 → 58, leaving a few reworded duplicates. Chosen: the third, because a leftover duplicate can be grouped at
Stage 2 while a wrongly merged claim is lost. From a duplicate pair, keep the verbatim quote, then the full-article
version. The 60 threshold is a first guess. Needed only if a chunked run is added.

**Run decision (user, 2026-11-06): full article + check,** on strike-term articles on the ≥ 8 pages. This reverses
the earlier removal of the check and leaves out the chunked run. Claude chose the CORE + BROAD term list, as
recommended, since the user had not picked one. Pre-check claims are saved, so no-check results stay available.
The continuation check for cut-off articles is not included in this run.

**Corpus for the run** (`kg/build_corpus.py`): 137 pages, 1,995 news units, 926 with a CORE or BROAD term, 10 letters
removed by headline, **916 articles** (192,693 words).

**Check prompt error, corrected.** The first check prompt listed only "a protest or reply about the cause", leaving
out demands, against the user's ruling. A smoke test showed it dropping "tax on roofs → people appeal to the
Government". The run was stopped after 23 articles (kept in `kg/out/progress_superseded_check.jsonl`, not used). The
check's KEEP list now names protests, replies, appeals and demands, states that no causal word is needed, and adds
justifications, which were also missing. Rulings test after the fix: unchanged at 17/20 per setup, skip still 8/8.
Five spot cases passed, including the tax appeal; one of them, the seamen's demand, was an invented sentence. The run
was restarted from the beginning on the corrected prompt.

**Continuation check deferred (user, 2026-11-06).** Decide from this run's results: add it only if split articles
significantly affect the results; otherwise skip it for v1. Proposed test, not yet confirmed by the user: join a
sample of ~30 flagged articles to their continuations, re-extract, and count claims that appear only after joining.

**Embedding model (user, 2026-11-06).** The user asked to try an instruction-based LLM embedder in place of
`bge-small-en-v1.5`, which is a small encoder that takes no task instruction. `qwen3-embedding:8b` was pulled (id
`64b933495768`, 7.6B parameters, Q4_K_M, 4.7 GB, 4,096 dimensions). The user confirmed 8B, with 4B as the fallback if it's
too slow. Not yet tested; to be compared with `bge` by nearest neighbours after extraction.

**Normalisation changed (user, 2026-11-06).** Because the embedder is LLM-backed, the user suggested more descriptive
context. Agreed: Qwen writes a one-sentence, self-contained description of each cause and effect from the full
article, and those are embedded. Raw quotes are not embedded, because a claim's cause and effect share them, which
would pull the two together. This replaces canonical phrases. The direction split is now conditional on a test,
since an instruction-based embedder may separate opposites without it. Plan and draft prompt: `STAGE2_PLAN.md`.

**Counterfactuals in the graph (user, 2026-11-06).** Hypotheticals don't go in the graph. A counterfactual is kept, but
normalisation rewrites it as what really happened. "Had the mob seized the arms… greater bloodshed" is about a mob
that did not seize arms, not a hypothetical seizure. Both sides are reversed in the descriptions; the extracted
`cause`, `effect` and `quote` stay as written. About 10 claims so far. A 9B model reversed only one side of such a
claim in an early test, so these need checking by eye.

**Other normalisation rulings (user, 2026-11-06, full table in `STAGE2_PLAN.md`).** Hedges dropped from descriptions;
two-part causes kept in one sentence for v1; names kept plus a free general phrase of up to 4 words, chosen over
generalising and over a fixed category list; only what the article states, so no default to Hongkong; one place per
side; 1925 names with OCR errors corrected; conditions described as conditions. The `source` and `dateline` fields
dropped by `plain_text()` must be restored for this step, since they are evidence of place.

**Normalisation prompt v1 (user, 2026-11-06).** The user asked for few-shot examples and a `reasoning` field, placed
first. Prompt and 5 hand-written examples are in `kg/normalise_prompt.py`, covering both counterfactual forms, an
unidentified strike, a condition and a hedged claim. Answers were hand-written because the extracted claims can be
wrong: the pickets claim read "number of departing strikers", where the text means strikers left in the camp.
`build_articles.py` rows now carry `source` and `dateline`; rebuilding changed no article IDs or text (150 of 916
articles have a source, 122 a dateline). Not yet run.

**Extraction run results (full article + check, 2026-11-06).** 915 of 916 articles, 2.1 h of model time. 757 claims
extracted: **590 kept**, 123 dropped by the check (16%), 40 quote not found (5%), 4 duplicates. 348 articles (38%) gave
at least one claim. Kept by month: June 280, July 310. Two articles failed with cut-off JSON; one succeeded on retry.
`page_009_NPCM19250608_01_0009#7` ("Boycott Urged", 111 words) fails every time and has no claims; the cause wasn't
investigated.

Review, by keyword search and small random samples, not a full audit or a precision figure. Of the 123 dropped, 10
contain a protest, demand or causal word; 7 of those are "Following X" (5) or conditionals (2), which fit the rulings as
applied, though whether "Following X" counts as sequence is a question for the user. Excluded cases do get through: the
denial "hardly operative at all as the cause" was kept, and a keyword search found 75 kept claims with future or
conditional words, of which a sample of 7 included real predictions ("will destroy confidence", "will most undoubtedly
stiffen"). Not all 75 are errors. The sample of articles with no claims has not been read yet.

**"Following X, Y" ruling (user, 2026-11-06).** Asked about "Following false reports… an anti-foreign riot took place" and
"Following the receipt of an appeal… the Council has requested…", the user ruled that these count as causal. The check's
KEEP list now includes "Following X, Y" where Y comes from or responds to X. Full-article rulings test unchanged at 17/20
(the chunked half of that test crashed on an over-long response and was not re-scored). Spot cases: three "Following"
claims kept, and "After this", "after which" and a denial dropped, but an invented control ("Following a morning at the
races, the Governor returned…") was wrongly kept, so some plain sequences will pass.

**Re-check cancelled (user, 2026-11-06).** Asked about dropping the check, the user decided to keep the results as they
stood, since it was mostly right, and stop the re-run. So the "Following" wording was **not applied**. It was removed from
the check prompt, so the recorded prompt matches the run (hash `7d2d2e20792f`). **v1 stands at 590 kept claims.** The ruling
stands in `annotation_study.md`, but "Following X, Y" claims the check dropped remain dropped: at least 5 were found, and
they can be read in `rejected.jsonl`. `kg/recheck.py` remains if this is revisited. No re-check decisions were saved.

**Normalisation run started (user, 2026-11-06).** All 590 kept claims, from `kg/normalise.py`, without the 50-claim
review first, at the user's instruction to run it. A 6-claim smoke test took 4.0 s per claim.

**Embedding instruction (user, 2026-11-06).** "Represent this event from a 1925-1926 Hongkong newspaper so that events of
the same topic are close, and different events or topics are far apart." This replaces Claude's draft, which asked for
the same event to be close and different events to be far apart even if they share a topic. Claude pointed out that "different
events… far apart" conflicts with "same topic… close" for two events on one topic. The user chose wording that tends more
general, so the instruction now ends "and events of different topics are far apart", and nodes lean toward topics for now.
The trade-off: fewer, larger nodes, less specific chains, and more risk of opposites merging, so the direction test matters more.

**Normalisation results (2026-11-06).** All 590 claims, 0 failures, 3.3 s each. 1,157 unique descriptions of 1,180. Median 12
words, range 6–23. 120 distinct place values; 357 of 1,180 (30%) unknown; values vary in level ("the Colony", "International
Settlement", "China"). 893 distinct general phrases, most common "a labour stoppage" (37). Read by Claude, not hand-audited:
10 counterfactual-like claims, 8 right. Errors: the "deflection" of the Communist Navy was reversed when it did happen, and
"would have been trampled" refers to the police but was described as students. A random 14 others read well.

**Embedding (2026-11-06).** `kg/embed.py`: all 1,157 descriptions with `qwen3-embedding:8b` (with and without the instruction)
and `bge-small-en-v1.5`, for comparison. The `Instruct:`/`Query:` format was written from memory of the model's documentation,
not confirmed. Neighbours from 9 phrases read sensibly for both models; Qwen looked somewhat better on topic. Real opposite pairs
are rare in this output. Qwen speed: about 0.09 s per description (101 s for 1,157), so 8B is fast enough and 4B isn't needed. An earlier 0.026 s figure was too low, probably because it re-timed texts already embedded.

**Direction test** (`kg/direction_test.py`, 6 opposite and 6 same-topic pairs picked by Claude, so small and not random). Mean
cosine, opposites vs same-topic: Qwen with instruction 0.64 vs 0.75 (ranges 0.51–0.74 and 0.70–0.79); Qwen plain 0.53 vs 0.64
(0.41–0.66, 0.57–0.74); `bge` 0.59 vs 0.65 (0.49–0.63, 0.54–0.76). Under the plan's table this is "slight overlap" for Qwen with the
instruction: no direction split, with the review step looking for mixed clusters.

**Clustering (user: no place separation, run it; 2026-11-06).** Method changed by Claude from the planned HDBSCAN. On the 1,157
descriptions, HDBSCAN left 460 unclustered at `min_cluster_size=2` (273 clusters, median size 2) and 666 at size 3 (101 clusters),
up to 910 at size 8, which suits neither topic nodes nor a connected graph. Average-link agglomerative clustering by cosine distance
assigns everything by a threshold, and read as real topics (shipping, flooding, Bolshevik influence, shootings):

| Threshold | Groups | Singletons | Largest | Self-loops |
|---|---|---|---|---|
| 0.25 | 244 | 427 | 36 | 91 |
| 0.30 | 254 | 230 | 49 | 124 |
| 0.35 | 205 | 122 | 100 | 185 |
| 0.40 | 146 | 42 | 128 | 219 |

Chosen: 0.30, as a balance. At 0.35 the largest groups were broad catch-alls and nearly a third of claims became self-loops. Result:
484 nodes; 466 claims on 405 edges, 33 of those edges with 2+ claims; 124 self-loops (21% of claims), kept in `edges.json`, not
deleted; 435 nodes in the graph. Largest node "strike in progress" (size 49, 61 claims). The two counterfactual errors from
normalisation were not corrected, since the user hadn't answered that question. Strongest edge, strike → China Mail delivery (13), is
probably inflated by a notice repeated across issues; not yet confirmed. Labels are each node's most central description, provisional.

**Embedding instruction switched to event level (user, 2026-11-06).** New instruction: "Represent this event from a 1925 Hongkong
newspaper so that descriptions of the same event are close, and different events are far apart, even if they share a topic." This
supersedes the topic wording and the "nodes lean toward topics" decision. Topic results are kept as `nodes_topic.json`, `edges_topic.json`
and `embed_qwen_topic.npy`. Direction test, 6 + 6 hand-picked pairs: opposites 0.59 (0.48–0.70), same-topic 0.73 (0.64–0.78), gap 0.14
against 0.11 for the topic wording. Distances shifted, so thresholds were compared again:

| Threshold | Nodes | Groups | Singletons | Largest | Edges | Edges with 2+ claims | Self-loops |
|---|---|---|---|---|---|---|---|
| 0.30 | 585 | 259 | 326 | 35 | 426 | 34 | 105 |
| 0.35 | 413 | 235 | 178 | 54 | 380 | 35 | 144 |

Saved: 0.35 (Claude's choice, not yet confirmed by the user). At that threshold the Hongkong and Shanghai strikes fall into separate groups with no
place tags, and Bolshevik, intimidation and financial groups are clearer. Compared by reading the largest groups only.

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
| `EXTRACTION_PLAN.md` | Plan for Qwen extraction over June–July 1925 (supersedes parts of `KG_PLAN.md`) |
| `extraction_probe/` | 2026-11-06 article-builder and Qwen probe scripts, raw model output |
| `annotation_study.md` | The user's rulings on what counts as a causal claim: quiz, responses, test results |
| `extraction_prompts.md` | Exact extraction and check prompts, settings, worked examples, earlier versions |
| `STAGE2_PLAN.md` | Plan for normalisation, embedding and clustering, with draft normalisation prompt |
| `kg/build_corpus.py`, `kg/extract.py`, `kg/out/` | Article selection, extraction run and its output |
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
