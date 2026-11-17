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

## 5g. Further months: Aug-Sep 1925 result (2026-11-06)

Same rules as June-July, run by `kg/run_batches.py`. 815 articles selected, 813 done, 301 with claims. 661 claims extracted:
516 kept, 98 dropped by the check, 42 quote not found, 4 duplicates, 1 bad cause or effect. August 299, September 217.
Two articles failed both passes with output cut off: `page_001_NPCM19250914_01_0001#14`, `page_005_NPCM19250818_01_0005#1`.

Combined June-September (`kg/viewer_combined/`), 1,106 claims, 2,149 descriptions:

| Version | Groups | Singletons | Arrows | Multi-claim arrows | Self-loops |
| --- | --- | --- | --- | --- | --- |
| Event 0.30 | 1,057 | 593 | 826 | 52 | 193 |
| Event 0.35 | 741 | 314 | 738 | 67 | 259 |
| Topic 0.30 | 866 | 405 | 763 | 60 | 244 |
| Topic 0.35 | 559 | 185 | 662 | 65 | 320 |

Apr-May 1925 finished at 20:17: 46 pages, 224 articles selected, 224 done, 69 with claims. Claims: {'quote_not_found': 13, 'kept': 100, 'dropped_by_check': 25, 'duplicate': 1}.

Combined April-September, 1,206 claims, 2,349 descriptions:

| Version | Groups | Singletons | Arrows | Multi-claim arrows | Self-loops |
| --- | --- | --- | --- | --- | --- |
| Event 0.30 | 1,162 | 652 | 905 | 56 | 210 |
| Event 0.35 | 812 | 333 | 810 | 72 | 277 |
| Topic 0.30 | 956 | 441 | 829 | 62 | 273 |
| Topic 0.35 | 604 | 191 | 726 | 68 | 353 |

Oct-Nov 1925: 77 pages, 378 articles selected, started 20:17.

Oct-Nov 1925 finished at 21:34: 378 of 378 articles, 145 with claims. 349 claims extracted: 252 kept, 72 dropped by the check, 25 quote not found. October 186, November 66.

Final combined April-November 1925 (`kg/viewer_combined/`): 2,330 of 2,333 articles done, 1,458 claims, 2,846 descriptions; 14 claims removed as re-filmed repeats, so 1,444 on the pages.
Kept claims by month: Apr 58, May 42, Jun 280, Jul 310, Aug 299, Sep 217, Oct 186, Nov 66. All three batches ran to the end with no stop file.

| Version | Groups | Singletons | Arrows | Multi-claim arrows | Self-loops |
| --- | --- | --- | --- | --- | --- |
| Event 0.30 | 1,391 | 760 | 1,091 | 62 | 252 |
| Event 0.35 | 961 | 375 | 989 | 83 | 326 |
| Topic 0.30 | 1,136 | 532 | 1,017 | 81 | 306 |
| Topic 0.35 | 717 | 217 | 892 | 82 | 400 |

Pages now have search, degree and date filters, and show/hide of causes and effects (`kg/build_viewers.py`). `kg/node_degree.py` ranks nodes by degree. Open: arrow weight by distinct
articles (at April-September, about half of multi-claim arrows had two claims from one page), and adding the 3/4 September pair to `kg/refilmed.py`.

Remaining months (user, 2026-11-06): all pages scoring >= 8 that were scraped. 736 pages, Dec 1925 to Nov 1926, already VL-OCRed, run in six two-month batches by `kg/run_batches.py`
from 21:38, same rules and prompts. The log continues in `kg/out/batches.log`. New months still need the check for re-filmed pages. The event instruction still says "1925" for 1926 items, kept unchanged so the versions stay comparable.

Dec 1925-Nov 1926 finished at 08:57 on 2026-11-07, all six batches, no stop file. 3,811 articles done; failed: `page_011_NPCM19260309_01_0011#5`, `#7`,
`page_001_NPCM19260806_01_0001#12`.

| Batch | Articles | With claims | Kept | Dropped by check | Quote not found |
| --- | --- | --- | --- | --- | --- |
| Dec 1925-Jan 1926 | 318 | 103 | 144 | 39 | 16 |
| Feb-Mar 1926 | 378 | 128 | 230 | 37 | 16 |
| Apr-May 1926 | 686 | 211 | 351 | 73 | 31 |
| Jun-Jul 1926 | 845 | 332 | 513 | 139 | 54 |
| Aug-Sep 1926 | 822 | 262 | 428 | 96 | 59 |
| Oct-Nov 1926 | 762 | 238 | 374 | 90 | 45 |

Full graph v1, April 1925-November 1926: 3,498 claims, 19 removed as re-filmed, so 3,479 on the pages, from 1,964 articles. Kept claims by month (before
removal): 1925 Apr 58, May 42, Jun 280, Jul 310, Aug 299, Sep 217, Oct 186, Nov 66, Dec 67; 1926 Jan 77, Feb 105, Mar 125, Apr 99, May 252, Jun 292,
Jul 221, Aug 214, Sep 214, Oct 214, Nov 160. CSVs in `kg/out/graph_v1/<version>/` (refreshed by `kg/combine.py` and `kg/export_neo4j.py`).

| Version | Groups | Singletons | Arrows | Multi-claim | Multi-article | Self-loop claims |
| --- | --- | --- | --- | --- | --- | --- |
| Event 0.30 | 3,092 | 1,630 | 2,711 | 145 | 85 | 559 |
| Event 0.35 | 2,090 | 805 | 2,498 | 190 | 125 | 702 |
| Topic 0.30 | 2,457 | 1,068 | 2,558 | 177 | 103 | 669 |
| Topic 0.35 | 1,515 | 457 | 2,273 | 208 | 150 | 852 |

Top degree at Event 0.35: "A strike is taken" 104 (75 out, 29 in), "A crisis exists in Hongkong" 47, "A boycott is under way" 44, "Recent
disturbances occur in Shanghai" 43, "Trade is at a standstill" 37. 1926 brings in other strikes. "A coal strike exists" (25; 28 claims, 26 from
1926) is mostly the British coal stoppage but also holds the American anthracite strike and the Ruhr. "A strike is taken" (190 claims, 88 from 1926) mixes
strikes of every place: 109 have place unknown, 33 Hongkong, 7 London. Expected, since the instruction has no place separation.

### Re-filmed pages (found by the user, 2026-11-06)

Some printed pages were filmed twice, so one page appears as two different image files. File hashes differ, and later image numbers run one ahead of
the printed page number. Confirmed from the page headers: 1925-07-27 images 5 and 6 (both printed page 5; image 7 is printed page 6), 1925-10-19 images 1
and 2, 1925-10-15 images 6 and 7. Found by comparing text within each issue among the 553 built pages (ratio >= 65, first 8,000 characters), so pages
not built and fainter repeats are unchecked. On 1925-07-27, 4 claims have the same quote on both images (8 and 10 claims on the images), so those are
counted twice. The October claims are not yet counted.

Fix (user approved, 2026-11-06): `kg/refilmed.py` compares only the images in these pairs, one-to-one, using the agreed merge rule, and keeps the
clearer image's version. `kg/build_viewers.py` applies it, so `kg/viewer/` and `kg/viewer_combined/` both leave those claims out, while `normalised.jsonl`
files stay unchanged. Removed claims are listed in `refilmed_removed.jsonl` beside each `normalised.jsonl`. Claims found on one image only stay.

Comparing across dates as well (8-word runs shared between any two of the 553 built pages; the first check only compared pages within an issue):

- 1925-09-04 image 1 is a second film of the 3 September front page: its header reads Thursday, September 3, No. 19,588. It sits in the 4 September
  issue, whose images 2 and 3 do show 4 September; the 5 September front page is No. 19,590, so the real 4 September front page (No. 19,589) appears to be missing. 60% of runs shared; 2 and 3 claims, 2 repeated. Added to `kg/refilmed.py` (user, 2026-11-06), and the remaining claim is dated 3 September on the pages.
- 1925-07-27 image 6 and 1925-07-28 page 5 (user's report) are different pages, with their own dates and layouts. They share 15% of runs; the two shared
  claims look like text from the meeting's resolutions, printed on both days (not read in full). Treated as a genuine repeat, so not removed.
- Other pairs at 10-36% were not read; many are page 3 of different issues, likely repeated advertisements.

Dec 1925-Nov 1926 (same comparison over all 1,289 built pages, 2026-11-07): two more pairs, both confirmed from the page headers and added to
`kg/refilmed.py`: 1926-02-09 images 7 and 9 (both printed page 7, 76% of runs shared, 1 claim each, repeated) and 1926-06-30 images 1 and 3 (both the
front page, 71%, 5 claims each, 2 repeated). Both images equally legible, so the image in page order is kept. All other pairs involving the new months were
at 22% or below, mostly page 3 or page 8 of consecutive days (likely repeated advertisements and notices), and were not read.


## 5h. Analysis of graph_v1 (from 2026-11-06)

**Working version (user, 2026-11-06): `event-035` by default, `event-030` as the check.** Claude had first suggested `event-035` by carrying over the earlier choice in these notes, without comparing versions; the user asked why, so the four were compared on the full April-November graph (1,442 claims):

| Version | Nodes | Self-loop claims | Edges in 2+ articles | Nodes with >= 2 Hongkong and >= 2 Shanghai descriptions | Nodes holding Bolshevik mentions (106 keyword hits) | Largest share in one node |
|---|---|---|---|---|---|---|
| event-030 | 1,390 | 252 | 30 | 0 | 64 | 9% |
| event-035 | 960 | 326 | 44 | 3 | 50 | 19% |
| topic-030 | 1,135 | 306 | 43 | 4 | 54 | 11% |
| topic-035 | 716 | 399 | 50 | 9 | 45 | 21% |

Reasoning: event wording keeps separate happenings apart (topic-035's largest node, "A strike is under way", has 182 descriptions tagged across Hongkong, Shanghai and Canton), and topic wording gathers themes little better. 0.35 gives more recurring edges; 0.30 gives cleaner groups, so it is the stricter check. topic-035 was rejected as the check because it could create links by merging different strikes. Place counts undercount mixing, since many descriptions are tagged "unknown"; the keyword figures are rough.

**Correction to section 5f.** The note that Hongkong and Shanghai strikes separate at event 0.35 was based on June-July. On the full corpus it is mostly but not fully true: "Intimidation is used against workers" has 4 Hongkong and 5 Shanghai descriptions, and "A strike affects Hongkong" has 27 Hongkong and 4 Shanghai.


**`graph_v1` is not fixed (found 2026-11-06).** `run_batches.py` re-exports `kg/out/graph_v1/` after each batch. It was overwritten at 22:32 during this analysis (1,586 claims, to 1926-01-30) and will change again. The 1,442-claim graph is commit `c63a9cfa`, whose message says April-September although the data runs to 30 November. The table above was measured on that commit. Analysis uses a frozen copy, `kg/analysis/explanations/snapshot_v1_c63a9cfa/`; `snapshot_1586_to_1926-01/` is kept for a later extension. Claim ids are stable (all 1,442 survive in the newer export); node ids are not, so anything keyed on nodes must name its snapshot.

**Competing explanations of the unrest: method.** Question: did the paper's explanation move from Shanghai events and labour grievances to Bolshevism and intimidation? 649 of the 1,442 claims were selected by a wide keyword filter on cause or effect and read by Claude (701 in the newer export, with December and January). A second keyword pass over the other 793 surfaced 100 for reading at cause-and-effect level, adding 2. The remaining 693 were not read. 122 claims explaining the unrest in China or Hongkong were coded by hand in `codes.txt`, after reading article context: frame, voice, stance, level (origin of the movement, or why people took part), place. Foreign strikes, incident-level chains and effects of the strike were excluded. Counting unit: one statement x one explanation family, 109 units from 88 statements, so repeated resolutions count once. Single coder, no reliability check, so all figures are indicative. Coding is at claim level and does not depend on the clustering, so the planned `event-030` check does not apply here. December and January claims are not coded.

Families: ORCH (Bolshevik, Canton or unnamed agitators), INTIM, TRIGGER (Shanghai, police action), LABOUR, NAT, DISORDER (weak government, militarists), CN_AUTH, WEAK (foreign softness).

| Period | ORCH | INTIM | TRIGGER | LABOUR | NAT | DISORDER | CN_AUTH | WEAK | Total |
|---|---|---|---|---|---|---|---|---|---|
| Before 30 May | 1 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 3 |
| 30 May-21 Jun | 10 | 2 | 8 | 2 | 2 | 2 | 2 | 0 | 28 |
| 22 Jun-31 Jul | 15 | 7 | 4 | 2 | 1 | 2 | 0 | 2 | 33 |
| Aug-Sep | 14 | 12 | 3 | 1 | 3 | 2 | 1 | 0 | 36 |
| Oct-Nov | 2 | 3 | 2 | 0 | 0 | 0 | 1 | 1 | 9 |

**Results.** (1) Bolshevism was present from the start (leader of 2 June), so the hypothesis of a late turn to it is not supported. (2) What changed: TRIGGER fell from 8 of 28 to 3 of 36, INTIM rose from 2 of 28 to 12 of 36, and within ORCH Bolshevik naming rose relative to unnamed agitators. (3) Place may explain much of this. Origin explanations after 30 May: Hongkong ORCH 14, TRIGGER 3, asserted LABOUR 0; Shanghai TRIGGER 10, ORCH 8, LABOUR 2. (4) Voice: 34 of 109 units are in the paper's own voice, and only 5 of 32 statements with Bolshevik blame. Reprints, officials and meetings carry the rest. After 30 May the paper never gives LABOUR in its own voice; it comes from home critics, Chinese strikers and a reprint. LABOUR was explicitly rejected twice (McNeill, 12 June; Hongkong public meeting, 27-28 July).

Limits: own voice is uncertain in both directions. Only 1 confirmed leader was found and 3 pieces are likely but unconfirmed; unattributed cables count as PAPER_NEWS. Choosing what to reprint is itself editorial, so reprints still show what the paper circulated. Claims show explicit causal statements only, as extracted, on pages selected by strike score.
**Consequence for theme questions.** No version gathers an explanation theme into one node, so questions about explanations are coded at claim level and do not depend on the clustering version.
## 5i. Temporal buckets of graph_v1 (2026-11-11)

**Question (user).** Can the graph be cut into time buckets for quantitative comparison? Analyses run at the user's request: node share per bucket (as cause and as effect), in- and out-degree of top nodes, similarity between buckets, all four versions, at one-month, two-month and calendar-quarter sizes.

**Data.** Frozen snapshot `kg/analysis/temporal/snapshot_v1_ceb6e08a/`, copied from `kg/out/graph_v1` as committed in `ceb6e08a` (3,479 claims, 1 April 1925 to 30 November 1926). A claim's date is the issue date; the edge takes the claim's date. Monthly graphs are rebuilt from claims (`has_cause`, `has_effect`), not from `causes.csv`, which pools all dates. Two-month buckets follow the batch pairs (Apr-May 1925 ... Oct-Nov 1926).

**Method.** Share = claims with the node as cause or effect / claims in the bucket (a self-loop counts once). 95% intervals come from 1,000 resamples of articles within each bucket. Degree counts claims and leaves self-loops out (reported separately). Similarity: node-set Jaccard, size-matched by subsampling every bucket to the smallest bucket's claim count (42 per month, 100 per two months, 306 per quarter; 200 draws), plus raw Jaccard, claim-weighted cosine and edge Jaccard. Cross-version check: each top event-035 node is matched to the node in each other version holding most of its (claim, role) slots, then the monthly share series are correlated.

**Results (event-035 unless stated).**
- Coverage: pages per month range from 16 to 75 (thin: Apr-May 1925, Nov 1925-Apr 1926), and claims follow pages. Compare shares only.
- Clear moves (intervals don't overlap): "Recent disturbances occur in Shanghai" is 8% of Q2 1925 claims and 1% or less in each later quarter. China Mail delivery appears only Jun-Sep 1925. "A strike is taken" falls from 8% (Q3 1925) to 2% (Q3 1926). The boycott (about 1% in 1925 quarters, 1-3% in 1926, 6% in Nov 1926) is suggestive only.
- **May 1926 strike spike (12%) mixes in the British General Strike** (London printers, coal, government spending). The strike node does not keep strikes in different places apart, so place has to be checked before reading strike trends.
- The strike is mostly a cause in every period (about 3-5 cause claims per effect claim). As an effect it peaks in Jun-Jul 1925 (39 cause / 11 effect) and Jun-Jul 1926 (15 / 7). It never shifts from effect to cause.
- Size-matched monthly Jaccard is 0.03-0.07. Lag 1 averages 0.049, against about 0.041 at lags 2-16, so there is no gradual drift: a small recurring core of hubs plus one-off incidents. The drop at lags 17-19 only reflects Apr-May 1925 pairs. The lowest adjacent pair in every version is Nov to Dec 1925, and December 1925 is unlike all other months. Edge Jaccard is 0-0.017.
- Robustness: across versions, monthly share series of the top 12 nodes correlate at Spearman 0.63-0.97 (weakest: "Trade is at a standstill" against event-030, 0.65; "parties have not come to any agreement" against topic-035, 0.63). Consecutive-similarity series correlate 0.78-0.95 monthly and 0.55-0.85 two-monthly. Quarterly similarity varies too little (0.135-0.151) to rank, and its cross-version correlations range from -0.37 to 0.83, so quarters are too coarse for similarity.

Limits: claims come only from pages selected by strike score, so shares measure what the selected coverage said, not the whole paper. Matching across versions by claim slots is many-to-one (topic-035 matches are up to 2x larger).

## 5j. Causes of the Hongkong-Canton strike (2026-11-11)

**Why this was done.** The user asked what the graph shows about the causes of the strike, after agreeing that node-level monthly comparison (5i) taught little. It is coded at claim level, like the explanations study, on `temporal/snapshot_v1_ceb6e08a`. Full write-up: `kg/analysis/strike_causes/FINDINGS.md`.

**Method.** All 356 claims with a strike-related effect were read, plus 254 claims from December 1925 onward that mention strike, boycott or pickets anywhere. Claims explaining the Hongkong-Canton strike or boycott were coded in `codes_hk.txt` under four questions: why it started (O), why people joined (J), why it lasted (P), why it weakened or ended (E). Each was also coded for explanation family and voice, with voice checked in article context. The 1925 Hongkong rows from `explanations/codes.txt` were merged in. This gives 93 statement units (repeats of one statement count once). Single coder, indicative only.

**Results.**
- Origin: 17 of 20 statements in Jun-Sep 1925 say it was engineered (Bolshevik, Canton, intimidation). No claim gives labour grievances for Hongkong. The shootings as cause come only from Chinese voices: the strikers' notice of 22 June 1925, and in 1926 the Chinese delegation, the Canton Gazette and the Strike Committee. The paper reports these but never adopts them.
- Joining: 11 of 15 statements cite intimidation.
- Why it lasted: in 1925, pickets holding strikers in Canton. In winter 1925-26, Canton connivance or weakness (8 of 15; leaders, Clementi and Amery agree). In September 1926, Chiang's support. On 16 November 1926 the leader reverses ("sincerely trying", pickets too strong). Canton's counter-explanation, Hongkong's food and silver embargo, is never answered.
- Ending: 1925 returns are explained by dissent, police raids, deportation and inducements. 1926 explanations are the Northern Expedition (strikers drafted, Chiang wants a settlement), revenue, and British force. Canton's October manifesto also cites the advance to the Yangtze, so the war is the one ending explanation both sides share.

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
| `kg/analysis/explanations/` | Competing-explanations study: frozen snapshots, `codes.txt` (hand coding), `analyse.py`, `coded_claims.csv` |
| `kg/analysis/temporal/` | Monthly, two-month and quarterly buckets: `snapshot_v1_ceb6e08a/`, `temporal.py` (writes `out/*.csv`), `make_report.py` (writes `report.html`) |
| `kg/analysis/strike_causes/` | Causes of the Hongkong-Canton strike: `candidates.csv`, `wider_1926.txt`, `codes_hk.txt` (hand coding), `analyse.py`, `coded_claims.csv`, `FINDINGS.md`, `context.py` (article context for a claim id) |

## 5k. Plan: British perceptions in the China Mail, May-July 1925 (2026-11-16, not started)

**Question (user).** To what extent does the China Mail graph show the accuracies and inaccuracies in British perception that the literature describes: Communist conspiracy (agitators, accurate; strikers Red, inaccurate), Canton support (accurate), not nationalism (inaccurate)?

**Decisions (user).** No labelling by Claude: measures come from a Qwen re-extraction (v1 prompt plus `speaker`/`speaker_type`; `is_letter` deterministic) and from embedding-anchor categories. Denials are inferred from absence, and ruling 2.3 stays. Scope is May-July 1925, causes of the strike only. Letters are included and tagged. Everything in scope is re-extracted, and v1 is untouched. Pages: the 301 with VL OCR plus un-OCRed pages with strike + perception score ≥ 7 (76 pages, about 3.8 h). Bare "canton" and "russian" were dropped from the dictionary as noise. The gold sample comes after the deadline. The run is autonomous overnight. The user approved the anchors, the schema and the 0.65/0.02 threshold, but asked not to start yet. Full plan: `kg/analysis/perception/PLAN.md`; scorer: `perception_screen.py` → `perception_screen.csv`.

**Found.** `strike_screen_batch.frozen_vocab()` now fails its assert (28 calibration files, not 24), because pages 11-14 of 2 June 1925 were VL-OCRed on 2026-11-02. `perception_screen.py` excludes them to reproduce the original vocabulary. `strike_screen_batch.py` itself has not been fixed.
**Graph and network design (user, 2026-11-16).** A layered property graph: evidence (articles, claims), events (v1-style clusters), concepts (anchors plus the HK Strike node; every event mapped) and speakers. Nationalism is split into 3T (shootings as trigger) and 3M (patriotic or anti-foreign motive). Analyses: discourse network (speakers × concepts), upstream paths to the strike within 3 hops, with asserted (within one article) and composed (across articles) paths labelled separately, voice-split graphs, and fortnightly snapshots. Not done: centrality or community detection on the event layer. The viewer is local HTML. By 11:00: data plus counts; viewer and network analysis afterwards. See PLAN.md §5.

## 5l. Perception run: code and test (2026-11-16, 00:50-01:40)

**Code** (`kg/perception/`, output `kg/out/perception/`, test output `kg/out/perception_test/`; v1 folders untouched):
- `common.py`: paths, log, status. `cap_json_retries` ends v1's chat retry after 2 invalid-JSON replies instead of 4. A model looping to the token limit (the 664-word "TO-DAY'S MEETING." of 27 July in the test) cost about 70 s per try. Prompts and options are unchanged.
- `build.py`: rebuilds articles for every May-July VL page. An article is selected if it has a strike CORE term or a perception term (as approved), and `is_letter` uses the v1 rule. On the 301 existing pages: 4,190 news articles, 828 selected (63 May / 403 Jun / 362 Jul), 8 letters. Two pages fail in the article builder (`page_008_NPCM19250602`, `page_012_NPCM19250603`: "no median for empty data").
- `stage.py`: runs v1 `extract.py` and `normalise.py` unchanged (same prompt hashes), with output redirected.
- `speaker.py`: a separate Qwen call per article with kept claims, returning speaker and speaker_type, prompt hash `e5d22b17bce5`. A separate pass was chosen, instead of new schema fields, so that the v1 extraction prompt stays byte-identical.
- `graph.py`: embeddings (v1 event instruction), event clusters (0.35), anchor concepts (0.65 / 0.02, sensitivity 0.60 and 0.70), layered `graph.json` and CSVs, and `counts.md`.
- `run.py`: orchestrator. Phase 1 covers the existing pages, from build and smoke gate to extract, speaker, normalise and graph. Phase 2 OCRs new pages (score ≥ 7) until `--ocr-until` (default 09:00), then rebuilds and extracts only new articles. The order was changed from the plan so that a complete graph exists before the OCR expansion.

**Scope change found in the test.** The normaliser often gives `effect_place` "unknown" for a strike that is plainly Hongkong's ("A strike takes place", strike similarity 0.86). Under the plan's place rule (Hongkong or Canton named), 4 of 7 strike-cause claims were lost. `graph.py` now reports both a **strict** scope (as planned) and a **broad** scope (Hongkong, Canton or no place given; other named places still excluded). Broad is the default column in `claims.csv`. The user needs to choose which one leads.

**Test** (6 pages with voices known from the earlier coding, 30 articles): 33 kept claims, 1 article failed (looping). Speaker pass 85 s for 16 articles, all types valid. Plausible: the Governor (Stubbs), public-meeting speakers, the Chinese Chamber of Commerce, a Christian Science Monitor reprint. Debatable: Holyoak (unofficial Legislative Council member, at a public meeting) as BRITISH_OFFICIAL; the 22 June tramway strike notice as CANTON_GOVT "the Strike Committee". Normalise 3.4 s per claim. Graph 12 s.
**Launch (user approved, 2026-11-16 01:41).** `kg/perception/run.py --ocr-until 09:00` was started through WMI (`Win32_Process.Create`, PID 23516, Python PID 11416), so it doesn't depend on the Claude session. Phase 1 corpus: 302 pages (page 7 of 15 May was OCRed in the test), 829 articles, 8 letters. Smoke gate passed at 01:42 (5 articles, 3 claims, speaker types PAPER 2, CHINESE 1). Fix before launch: `stage.py` records articles that fail with invalid JSON in `extract_skip.txt` and leaves them out of later passes. The extraction prompt hash is `7d2d2e20792f`, the same as v1.
**Restart (2026-11-16 ~01:50).** The user restarted the computer by accident, which ended the run at 55 of 829 articles. `progress.jsonl` (55 records) and `speakers.jsonl` were checked: every line is valid JSON. The run was relaunched at 01:54 with the same command (WMI, PID 16276). The orchestrator started Ollama itself, and extraction resumed from article 56, passing the smoke gate again on the next 5 articles. Rate before the restart: about 6.5 s per article.

### 5m. Perception run finished (2026-11-16 08:01)
- Phase 1 graph at 04:47. OCR of all 76 new pages finished at 07:31, with no OCR failures. Phase 2 graph at 08:01. Status: ALL DONE.
- Corpus: 377 pages; 995 articles selected (171 May / 430 Jun / 394 Jul); 12 letters. 994 extracted; 1 skipped for looping JSON (page_009_NPCM19250608_01_0009#7).
- Graph: 636 claims, 1,238 descriptions, 468 events. In-scope strike causes at 0.65: 29 claims (broad scope) and 15 (strict). At 0.60: 46; at 0.70: 18. In the broad scope at 0.65, "other" holds 17 of the 29.
- The counts are small and unvalidated. They are in kg/out/perception/graph/counts.md.
- v1 cross-check (kg/perception/v1_months.py, written to kg/out/perception/v1_months.md): the same anchors and broad scope applied to all 3,479 v1 claims (Apr 1925 – Nov 1926), with no speaker split.
  - Threshold 0.65: 134 claims in scope; 50 of them get a named category. By category: Canton support 19, intimidation 10, labour 8, 1a 4, 3T 4, 3M 4, 1b 1. The rest fall into "other".
  - May–July 1925 gives 24 claims in scope in v1, against 29 in the perception run. Outside May–July, v1 adds about 110 claims in scope but only about 38 categorised.

### 5n. Month-by-month extension, Aug 1925 – Apr 1926 (launched 2026-11-16 09:11)
- User decision: option A, pages with existing VL OCR only (429 pages, no new OCR); end at April 1926 with no article-level place filter. The cut-off avoids the British General Strike (May 1926) but leaves out the strike's last six months.
- The new months are sampled more thinly than May–July, which had 76 extra OCRed pages, so monthly counts are not strictly comparable.
- `kg/perception/months.py` runs each month in turn: build → extract → speaker → normalise → graph. It saves a snapshot to `kg/out/perception/snapshots/through_YYYY-MM/`, and the May–July graph is frozen at `snapshots/1925-05_07`.
- `common.py` reads extra months from `PERCEPTION_EXTRA_MONTHS`.
- Verified that rebuilding with August added leaves the 995 May–July articles identical. August adds 334 articles.
- `counts.md` gains tables by month for British and Chinese voices.
- Estimated about 6 h for the full run.

### 5o. Git history rewrite for the GitHub push (2026-11-16, user-approved)
- Local `main` was 12 commits ahead of GitHub (nothing pushed since d6221836), about 7 GB. `kg/out/combined/embed_qwen_{event,topic}.npy` (113 MB each) exceed GitHub's 100 MB limit.
- With the user's approval, these two files were removed from every unpushed commit with `git filter-branch`, run in a bare clone so the live run's working files were untouched. Verified that every rewritten commit differs from the original only by those two files.
- The files stay on disk and are untracked, through a new `agent-sandbox/.gitignore` that also covers `ollama_serve.log`. They can be regenerated with `kg/combine.py`.
- New commit ids: "april-september 1925 in v1" c63a9cfa → **c18feaf2**; init analysis → b2acd5ce; full v1 complete → c44424b9; office hours → 6653ac96; perception commit → 56c9b8ad. The old history is on branch `backup/pre-npy-rewrite`. References to `c63a9cfa` above, such as `snapshot_v1_c63a9cfa/`, mean the same data.
- Pushed to GitHub one commit at a time.
- Second rewrite (user-approved, 2026-11-16): the first commit alone was 5.9 GB, and GitHub's server returned HTTP 500.
  - Removed from the unpushed commits: the new `ocr_vl_out/*_layout_det_res.png` (PaddleOCR layout debug images, 5.1 GB, read by no script) and `ocr_vl_out/imgs/*.jpg` (cropped figures, 0.7 GB, linked only from the page `.md` files). The 473 such images already on GitHub stay tracked.
  - Verified that no other file changed in any commit. All images stay on disk and are ignored in `agent-sandbox/.gitignore`.
  - Push size fell from about 7 GB to 615 MB. The pre-rewrite history is on branches `backup/pre-npy-rewrite` and `backup/pre-png-rewrite`. Commit ids changed again, so see `git log` for the current ones; "april-september 1925 in v1" is identified by its message.

### 5p. Perception viewer (2026-11-16)
- `kg/perception/viewer.py` and `viewer_template.html` write a self-contained `viewer.html` into each graph folder (live graph and all snapshots: `viewer.py --all`). `graph.py` now writes it automatically, wrapped in try/except so it can never fail the graph stage.
- Three views:
  - **Concepts → HK strike**, optionally with links between concepts and an "other" node.
  - **Event chains**: 1–3 steps upstream of strike-effect events. A chain is "asserted" when the upstream claim comes from the same article as the downstream link, and "composed" (dashed) otherwise.
  - **Speakers × concepts**: the discourse network.
- Filters: voice, month range, threshold (0.60/0.65/0.70), broad or strict scope, letters. Every arrow opens its quotes with speaker, type, date, headline and page.
- Tested in headless Edge: all three views, clicks on edges and nodes, and the filter changes, with no JavaScript errors.
- Viewer restyled to match `demo_kg/causal_kg_demo_local.html` (user request): Times New Roman, black on white, one blue for categories, black for the strike node, grey arrows, plain instructions. The fit zoom is capped at 1 so small graphs don't blow up. Retested all views in headless Edge with no errors.
- Viewer redesigned after `graph_style_guide/` (user, 2026-11-16), as black-and-white scientific figures. Shape encodes node type (□ strike, ◇ cause category, ○ event). Fill encodes voice (● British, ○ Chinese, grey other) or category match. Solid lines are asserted and dashed lines composed. Labels use n = counts and B/C/O voice codes, with lettered panels A/B/C and a θ, t annotation block. Each quote shows its cos similarity to the assigned anchor. The template was rewritten more simply (about 300 lines, down from 430). Tested in headless Edge with no errors.

### 5q. Anchors v2: working conditions as item 4 (2026-11-16 evening)
- The extension run finished at 16:04 (May 1925 – April 1926: 1,578 claims, 1,015 events). The v1-anchor graph is frozen as `snapshots/through_1926-04`.
- Anchors v2 are as in PLAN.md (Update 2026-11-16 evening). Results are in `snapshots/through_1926-04_anchors_v2` and the live `graph/`. `anchors.json` now records `"version": "v2"`. The viewer reads its categories from each graph's `anchors.json`, so v1 snapshots still display.
- v1 → v2 at θ = 0.65, broad scope: 72 → 73 claims in scope. Only 5 in-scope claims changed. Working conditions gets B2/C0/O0, but both are false positives: "Agitators cause unrest among the dock company's Chinese staff, a labour dispute" (really agitators) and a Mozambique Company strike (not Hongkong). Intimidation goes from B5 to B6. The other categories are unchanged.
- **Finding:** across all claims, 32 have a working-conditions cause (26 British). Their effects are phrased as "disturbances", "troubles" or "social unrest", not as a strike, so the scope rule excludes them. The clearest case is the meeting of European residents in Hongkong, 1925-07-28: "troubles here and in China are due to bad labour conditions in the Far East". Others: the TUC General Council (1925-06-26, "disgraceful working conditions in Chinese mills are the immediate cause of the present disturbance in China") and the Bishop of St Albans (1925-06-09).
  - So item 4 is partly contradicted: some British voices did cite conditions, but metropolitan and labour voices more than the colonial government. They did so for "unrest" in general, not the strike by name.
  - This is a scope-recall limitation of the strike anchors, which cover only strike, exodus and boycott.
- **CORRECTION (same evening).** The 1925-07-28 European-residents quote is a *denial*: "protests strongly against mis-representation in many Home papers, that troubles here and in China are due to bad labour conditions … the workers had no grievance" (page_005_NPCM19250728_01_0005, headline mis-segmented as "LANE, CRAWFORD LTD / BOLS LIQUEURS").
  - Extraction took out the rebutted claim and attributed it to the rebutters. Ruling 2.3 missed the denial because it is carried by reported speech ("Home papers say X; we protest").
  - The finding is therefore reversed. Colonial British voices explicitly deny that conditions caused the strike, which *supports* literature item 4. Metropolitan voices (the "Home papers", the TUC, the Bishop of St Albans) assert conditions, but about China generally.
  - None of the other 25 British working-conditions claims is a colonial voice attributing the Hongkong strike to conditions (they concern Shanghai, Scotland, Burma, rents, shipbuilding).
  - The method infers denials from absence, so it cannot see explicit denials like this one, the kind item 4 concerns. This is a known recall gap. The quote is qualitative evidence for the paper.
