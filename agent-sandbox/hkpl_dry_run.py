"""Dry run: list the issues a HKPL search URL returns, without downloading anything."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from china_causal_kg.ingestion.hkpl_scraper import collect_search_results, init_browser

SEARCH_URL = (
    "https://sls.hkpl.gov.hk/digital-collection/en/searchresults.html?param=%7B%22asc%22%3Afalse%2C%22criteriaList%22%3A%5B%7B%22searchOptionId%22%3A%221634098806473621506%22%2C%22keyword%22%3A%22China%20Mail%22%2C%22type%22%3A1%7D%2C%7B%22searchOptionId%22%3A%221634098535802601473%22%2C%22keyword%22%3A%22%22%2C%22type%22%3A0%7D%2C%7B%22searchOptionId%22%3A%221634098535802601473%22%2C%22keyword%22%3A%22%22%2C%22type%22%3A0%7D%2C%7B%22searchOptionId%22%3A%221634098535802601473%22%2C%22keyword%22%3A%22%22%2C%22type%22%3A0%7D%5D%2C%22current%22%3A1%2C%22dateList%22%3A%5B%7B%22endTime%22%3A%221925-09-30%22%2C%22searchOptionId%22%3A%221646102458914615297%22%2C%22startTime%22%3A%221925-08-01%22%7D%5D%2C%22filterList%22%3A%5B%7B%22searchOptionId%22%3A%221646102849798582273%22%2C%22keyword%22%3A%5B2023130000000058%5D%2C%22fieldName%22%3A%22Collection%22%7D%5D%2C%22mediaType%22%3Anull%2C%22groupFilterSearch%22%3A%5B%5D%2C%22keyword%22%3A%22%22%2C%22languageEnum%22%3A%22EN%22%2C%22otherList%22%3A%5B%5D%2C%22size%22%3A10%2C%22sortType%22%3A1%2C%22trackTotalHits%22%3Atrue%2C%22customizationSearch%22%3A%5B%5D%2C%22isEnableViewData%22%3Afalse%7D&tab=0"
)

if __name__ == "__main__":
    driver = init_browser(headless=True)
    try:
        records = collect_search_results(SEARCH_URL, driver)
    finally:
        driver.quit()
    print(f"\n{len(records)} unique records")
    for r in sorted(records, key=lambda r: str(r.get("date"))):
        print(f"{r.get('date')}\t{r.get('bibNo')}\t{r.get('title')}\t{r['id']}")
