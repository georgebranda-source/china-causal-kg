# agent-sandbox

Agent-authored code for this project (see `../AGENTS.md`).

## HKPL newspaper scraper

Downloads scanned newspaper issues from the Hong Kong Public Libraries Multimedia Information System
(`sls.hkpl.gov.hk/digital-collection`): full-resolution page images, the library's indexed OCR text,
metadata, and a compiled PDF per issue.

- Runner: `agent-sandbox/scrape_hkpl.py`
- Code: `agent-sandbox/src/china_causal_kg/ingestion/hkpl_scraper.py`

### Setup

Requires Python 3.10+, Google Chrome (Microsoft Edge is used as a fallback), and:

```
pip install selenium pillow
```

Selenium downloads a matching browser driver automatically.

### Scrape every issue from a search

1. Run a search on the HKPL digital collection site (e.g. Advanced Search → keyword "China Mail",
   a date range, Collection = Old HK Newspapers).
2. Copy the URL of the results page. It looks like
   `https://sls.hkpl.gov.hk/digital-collection/en/searchresults.html?param=...&tab=0`.
3. Run, from the repo root, with the URL in quotes:

```
python agent-sandbox/scrape_hkpl.py --search-url "https://sls.hkpl.gov.hk/digital-collection/en/searchresults.html?param=..."
```

All result pages are fetched automatically, so the "results per page" setting on the site doesn't matter.

Try it on a couple of issues first with `--limit`:

```
python agent-sandbox/scrape_hkpl.py --search-url "<url>" --limit 2
```

### Scrape a single issue

Pass the issue's cover page URL (or just its `catalogueId`):

```
python agent-sandbox/scrape_hkpl.py --url "https://sls.hkpl.gov.hk/digital-collection/en/contentcoverpage.html?catalogueId=189cbe0b9cb711ef9c2"
python agent-sandbox/scrape_hkpl.py --url 189cbe0b9cb711ef9c2
```

### Options

| Option | Description |
| --- | --- |
| `-s`, `--search-url URL` | Scrape every issue in a search results page. Takes priority over `--url`. |
| `-u`, `--url URL_OR_ID` | Scrape one issue by cover page URL or `catalogueId`. |
| `--limit N` | With `--search-url`: only the first N results (in the search's sort order). |
| `--force` | With `--search-url`: re-check issues that already look complete (see below). |
| `-o`, `--output-dir DIR` | Where to save. Default: `data/raw/hkpl/` in the repo root. |
| `--no-pdf` | Don't compile a PDF (and don't require one when deciding if an issue is complete). |
| `--headful` | Show the browser window instead of running headless (useful for debugging). |

`python agent-sandbox/scrape_hkpl.py --help` prints the same list.

### Output

One folder per issue, named `<bibNo>_<title>`:

```
data/raw/hkpl/
└── NPCM19250801_The_China_Mail_1925-08-01/
    ├── metadata.json               # catalogue metadata, page manifest, raw OCR records
    ├── library_indexed_ocr.txt     # the library's OCR / headline index (when available)
    ├── page_001_NPCM19250801_01_0001.png
    ├── ...
    └── The_China_Mail_1925-08-01.pdf
```

A China Mail issue is usually 8–10 pages, about 5 MB of PNGs and a ~40 MB PDF. `data/raw/` is gitignored.

### Deduplication and re-running

You can run the same command again at any time:

- **Within a search**, an issue listed more than once (same `catalogueId` or same bib number) is only scraped once.
- **Already-complete issues are skipped** without being opened. Complete means the folder has `metadata.json`,
  every page image, and the PDF (unless `--no-pdf`). This also applies across different searches that overlap.
- **Partially downloaded issues resume**: only missing page images are downloaded, and the PDF is rebuilt.
- Failed issues are listed at the end of a run. Run the same command again to retry them.

`--force` reopens issues that look complete and refreshes `metadata.json` and the OCR text, but still reuses the
page images on disk. To download an issue again from scratch, delete its folder and re-run.

### Troubleshooting

- **"Timed out waiting for page scripts to initialize" / search response timeout**: the site's queue page
  (Queue-it) may be active, or the site is slow. Re-run, or use `--headful` to watch what the browser sees.
- **Chrome fails to start**: the scraper tries Edge automatically. Make sure one of them is installed and up to date.
- **Non-ASCII output errors on Windows** (`UnicodeEncodeError`): run `set PYTHONIOENCODING=utf-8`
  (cmd) or `$env:PYTHONIOENCODING="utf-8"` (PowerShell) first.
