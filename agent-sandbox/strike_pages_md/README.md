# How these 40 pages were chosen

The 40 `.md` files here are PaddleOCR-VL transcriptions of China Mail pages (June–July 1925)
picked as the most likely to cover **worker strikes**, so the VL model, which takes about 3 minutes
a page, only ran on a small fraction of the 496 pages in `data/raw/hkpl/china_mail_june_july_1925/`.
They are copies of `agent-sandbox/ocr_vl_out/<page>.md`; image links inside them point to
`ocr_vl_out/imgs/` and do not resolve from this folder.

## Pipeline

1. **Fast OCR of every page** (`agent-sandbox/ocr_fast.py`, text in `agent-sandbox/ocr_fast_out/`).
   PP-OCRv5 mobile det + rec models (`PP-OCRv5_mobile_det` / `PP-OCRv5_mobile_rec`), GPU,
   about 2 s per page. Accuracy is poor on this print; it was used only for screening.
2. **Fuzzy keyword scoring** (`agent-sandbox/strike_screen.py` -> `agent-sandbox/strike_screen.csv`).
   Page text = fast-OCR text + the library's own headline OCR for that page where it exists
   (`metadata.json` -> `ocrList`; covers only 193 of 496 pages, headlines only).
3. **Cutoff**: score >= 15, excluding pages that already had VL output (the 24 pages of
   1925-06-01 and 06-02). That gives 40 pages from 32 editions (06-03 to 07-30), 21 of them front pages.
   The list is `agent-sandbox/vl_selected_pages.txt`.
4. **VL OCR** (`agent-sandbox/ocr_vl.py @agent-sandbox/vl_selected_pages.txt`).

## Scoring

`score = 3 x (CORE concepts found) + (BROAD concepts found)`. A concept counts once however many of
its variants appear. A page is "flagged" if it has any CORE concept or at least 2 BROAD concepts
(not used for this selection; the selection is purely score >= 15).

**CORE concepts** (variants matched):
- strike: strike, strikes, striker, strikers, striking
- walkout: walkout, walkouts
- boycott: boycott, boycotts, boycotted
- picket: picket, pickets, picketing
- lockout: lockout
- stoppage: stoppage
- downed tools: downedtools (the matcher joins adjacent tokens)

**BROAD concepts** (variants matched):
- labour: labour, labor
- worker: worker, workers, workmen, workman
- coolie: coolie, coolies
- union: union, unions, unionist
- wage: wages, wage
- employ: employees, employers
- agitation: agitator, agitators, agitation
- riot: rioter, rioters, riot, riots
- demonstration: demonstration, demonstrators
- mob: mob
- disorder: disorder, disorders
- unrest: unrest
- dispute: dispute, disputes
- negotiation: negotiations, arbitration
- sympathy: sympathy
- trades: seamen, dockers, compositors, printers, tramway
- mill: mill, mills
- factory: factory, factories
- student: students
- communist: communist, communists, bolshevik, bolshevism, soviet
- extremist: extremists
- propaganda: propaganda
- anti-foreign: antiforeign
- shameen: shameen, shakee
- martial: martial
- casualties: casualties, massacre, assassination
- tsingtao: tsingtao
- grievance: grievances, demands, protest, massmeeting

## Matching rules (built for OCR errors)

- Text is lower-cased, hyphens removed, digits `0`/`1` mapped to `o`/`l`, then split into letter tokens.
  Adjacent tokens are also joined, so a word split by the OCR ("str ike") can still match.
- Edit-distance tolerance by term length: <= 4 letters exact; otherwise `max(1, len // 5)` edits.
  This catches errors like `gtrikes`, `unton`.
- A token is **not** accepted as a misread of a term if it is an ordinary word in the VL text
  (seen >= 3 times across the VL-transcribed pages; 2,911-word vocabulary at scoring time), e.g.
  `onions`, `wales`, `aviator`. Real OCR errors do not occur there, so they still match.
- Hard skip list for neighbours of CORE terms the vocabulary missed (cricket season):
  wicket(s), ticket(s), picked, pocket(s), pocketing, packet(s), stroke(s), stripe(s), strife, strive, stride.

## Checks and limits

- Calibration against VL text on the 24 pages that had both (strike-regex in VL text as truth):
  all pages with a strike mention that was actually on topic were flagged. One miss was a boxing
  "strike" (not relevant). About 7 of 17 pages without strike terms were also flagged (broad words only).
- Full run: 496 pages scored, 328 flagged, 217 with a CORE hit. Cutoff 15 keeps only the densest 40;
  roughly 180 pages with a CORE hit are NOT in this set, plus the pages flagged on broad terms only.
  Counts of pages left at other cutoffs (not yet VL'd): >=12: 74, >=10: 97, >=8: 132, >=5: 209, >=2: 315.
- A CORE hit can be off-topic (e.g. a London telegraph messenger boys' strike on 1925-06-01 p10, not
  in this set). A page can also cover a strike without these words and be missed.
- Re-running `strike_screen.py` now would use a slightly larger VL vocabulary (64 pages, not 24),
  so scores can shift a little. `strike_screen.csv` is the record of the scores used.
- `strike_screen.py` needs `rapidfuzz`; it was run from a separate venv, not the project `.venv`.

## Files

- `agent-sandbox/strike_screen.py`, `strike_screen.csv`: scoring code and per-page scores, terms hit
- `agent-sandbox/strike_eval.py`: comparison of flags against VL text
- `agent-sandbox/vl_selected_pages.txt`: the 40 image paths
- `agent-sandbox/ocr_fast.py`, `ocr_fast_out/`: fast OCR script and its text for all 496 pages
