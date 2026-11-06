"""Queue HKPL scrapes of China Mail, one calendar month at a time, after the Aug–Sep batch finishes."""
import calendar
import json
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from china_causal_kg.ingestion.hkpl_scraper import scrape_search_results
from hkpl_dry_run import SEARCH_URL

SANDBOX_DIR = Path(__file__).resolve().parent
OUTPUT_ROOT = SANDBOX_DIR.parent / "data" / "raw" / "hkpl"
PREVIOUS_LOG = SANDBOX_DIR / "hkpl_aug_sep.log"

# June–July 1925 and Aug–Sep 1925 are already done or handled by their own runs.
MONTHS = [(1925, 4), (1925, 5), (1925, 10), (1925, 11), (1925, 12), (1926, 1), (1926, 2), (1926, 3)]

DELAY_BETWEEN_ISSUES = 30  # seconds
DELAY_BETWEEN_PAGES = 3  # seconds


def month_url(search_url: str, year: int, month: int) -> str:
    """Return the search URL with its date range set to one calendar month (end date inclusive)."""
    parsed = urlparse(search_url)
    query = parse_qs(parsed.query)
    param = json.loads(query["param"][0])
    last_day = calendar.monthrange(year, month)[1]
    param["dateList"] = [
        {
            **param["dateList"][0],
            "startTime": f"{year}-{month:02d}-01",
            "endTime": f"{year}-{month:02d}-{last_day:02d}",
        }
    ]
    param["current"] = 1
    query["param"] = [json.dumps(param, separators=(",", ":"))]
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))


def wait_for_previous_batch() -> None:
    """Block until the Aug–Sep batch has printed its completion line or a traceback."""
    while True:
        text = PREVIOUS_LOG.read_text(encoding="utf-8", errors="ignore") if PREVIOUS_LOG.exists() else ""
        if "[SUCCESS] Batch complete" in text or "Traceback" in text:
            print("[*] Previous Aug–Sep batch has finished; starting queue.", flush=True)
            return
        time.sleep(60)


def main() -> None:
    wait_for_previous_batch()
    for year, month in MONTHS:
        name = f"china_mail_{calendar.month_abbr[month].lower()}_{year}"
        print(f"\n########## {name} ##########", flush=True)
        try:
            scrape_search_results(
                month_url(SEARCH_URL, year, month),
                output_dir=OUTPUT_ROOT / name,
                create_pdf=False,
                headless=True,
                delay_between_docs=DELAY_BETWEEN_ISSUES,
                delay_between_pages=DELAY_BETWEEN_PAGES,
            )
        except Exception as e:
            print(f"[!] {name} failed: {e}", flush=True)


if __name__ == "__main__":
    main()
