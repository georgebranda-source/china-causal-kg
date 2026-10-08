"""
Hong Kong Public Libraries (HKPL) Smart Library System / MMIS Newspaper Scraper

Automates:
1. Passing Queue-it bot challenge via headless Chrome/Edge.
2. Interacting with the internal DRM / API using the session token and AES-CBC encrypted handshake.
3. Extracting metadata (title, bib ID, publication date, headlines, existing library OCR text).
4. Downloading all full-resolution page scans (e.g. 3595x4665 PNGs).
5. Assembling pages into a high-res PDF and saving structured metadata.json.
6. Batch mode: collecting every issue from a search results page and scraping each in turn.
"""

import os
import sys
import time
import json
import base64
import argparse
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from PIL import Image
from selenium import webdriver

# Repo root: <repo>/agent-sandbox/src/china_causal_kg/ingestion/hkpl_scraper.py
REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "raw" / "hkpl"

SEARCH_API_PATH = "/api/drmapi/client-api/mmissearch/advanceQuery"
# Performance logging lets us read the search API's JSON response via CDP
PERFORMANCE_LOGGING = {"performance": "ALL"}


def parse_catalogue_id(url_or_id: str) -> str:
    """Extract catalogueId from a full URL or return it directly if already an ID."""
    if "catalogueId=" in url_or_id:
        parsed = urlparse(url_or_id)
        params = parse_qs(parsed.query)
        cat_id = params.get("catalogueId", [None])[0]
        if cat_id:
            return cat_id
    return url_or_id.strip()


def init_browser(headless: bool = True):
    """Initialize a Chrome (or fallback Edge) webdriver configured for Queue-it and DRM bypass."""
    try:
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        options.set_capability("goog:loggingPrefs", PERFORMANCE_LOGGING)
        return webdriver.Chrome(options=options)
    except Exception as e:
        print(f"[!] Chrome initialization failed: {e}. Trying Edge fallback...")
        options = webdriver.EdgeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        options.set_capability("ms:loggingPrefs", PERFORMANCE_LOGGING)
        return webdriver.Edge(options=options)


def scrape_document(
    url_or_id: str,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    create_pdf: bool = True,
    headless: bool = True,
    delay_between_pages: float = 0.5,
    driver=None,
) -> Path:
    """
    Scrapes all pages and metadata for a given HKPL newspaper issue.
    
    Args:
        url_or_id: The full HKPL contentcoverpage URL or raw catalogueId.
        output_dir: Base directory where scraped documents are saved.
        create_pdf: Whether to compile downloaded page images into a multi-page PDF.
        headless: Whether to run the browser headlessly.
        delay_between_pages: Gentle pause between page downloads.
        driver: Existing webdriver to reuse (batch mode). If None, one is created and closed here.
    
    Returns:
        Path to the directory containing downloaded assets.
    """
    catalogue_id = parse_catalogue_id(url_or_id)
    if url_or_id.startswith("http"):
        target_url = url_or_id
    else:
        target_url = f"https://sls.hkpl.gov.hk/digital-collection/en/contentcoverpage.html?catalogueId={catalogue_id}"

    print(f"[*] Target Catalogue ID: {catalogue_id}")
    print(f"[*] Navigating to: {target_url}")

    own_driver = driver is None
    if own_driver:
        driver = init_browser(headless=headless)
    try:
        driver.get(target_url)
        print("[*] Waiting for Queue-it authentication and initial page hydration...")
        
        # Poll until axios and somefilePicview are loaded
        max_wait = 30
        start_time = time.time()
        ready = False
        while time.time() - start_time < max_wait:
            is_ready = driver.execute_script(
                "return typeof axios !== 'undefined' && typeof somefilePicview !== 'undefined';"
            )
            if is_ready:
                ready = True
                break
            time.sleep(1)

        if not ready:
            raise TimeoutError("Timed out waiting for page scripts to initialize.")

        print("[*] Page initialized. Fetching document metadata and page manifests...")

        # Execute extraction inside browser context to utilize session cookies & crypto
        manifest_script = f"""
        const callback = arguments[arguments.length - 1];
        async function fetchManifest() {{
            try {{
                const catId = '{catalogue_id}';
                
                // 1. Fetch main catalogue details (traceId & content objects)
                const detailRes = await axios.get('/api/drmapi/client-api/mmis/catalogueDetail/catalogueDetailNew', {{
                    params: {{
                        catalogueRecordId: catId,
                        languageEnum: 'EN'
                    }},
                    headers: {{
                        catalogueId: catId,
                        languageType: 1
                    }}
                }});
                
                // 2. Fetch OCR & headline data if available
                let ocrData = null;
                try {{
                    const ocrRes = await axios.get('/api/drmapi/client-api/mmis/catalogueDetail/catalogueDetailInformation', {{
                        params: {{
                            catalogueRecordId: catId,
                            languageEnum: 'EN'
                        }},
                        headers: {{
                            catalogueId: catId,
                            languageType: 1
                        }}
                    }});
                    ocrData = ocrRes.data?.data?.ocrList || [];
                }} catch (e) {{
                    console.warn('OCR fetch warning:', e);
                }}

                const traceId = detailRes.data?.traceId;
                const d = detailRes.data?.data || {{}};
                const contentList = d.contentList?.ortherContent || [];
                
                // Filter to actual page images (contentObjectType === "1")
                const pageItems = contentList
                    .filter(x => x.contentObjectType === '1')
                    .map((item, idx) => ({{
                        pageNumber: idx + 1,
                        id: item.id,
                        fileName: item.fileName,
                        contentVol: item.contentVol,
                        contentDispSeqNo: item.contentDispSeqNo,
                        location: item.locationProd || item.location
                    }}));

                callback({{
                    success: true,
                    traceId: traceId,
                    metadata: {{
                        catalogueId: catId,
                        bibId: d.bibNoStr,
                        accNo: d.accNoStr,
                        title: d.titleStr,
                        publisher: d.publisherStr || 'Hong Kong : China Mail Ltd.',
                        date: d.dateCreatedPublished || '',
                        totalPages: pageItems.length,
                        collection: d.collectionStr
                    }},
                    pages: pageItems,
                    ocrList: ocrData
                }});
            }} catch (err) {{
                callback({{ success: false, error: err.toString(), stack: err.stack }});
            }}
        }}
        fetchManifest();
        """

        manifest = driver.execute_async_script(manifest_script)
        if not manifest.get("success"):
            raise RuntimeError(f"Failed to fetch manifest: {manifest.get('error')}")

        meta = manifest["metadata"]
        pages = manifest["pages"]
        ocr_list = manifest.get("ocrList", [])

        title_slug = (meta.get("title") or f"issue_{catalogue_id}").replace(" ", "_").replace(",", "").replace(":", "")
        doc_dir = Path(output_dir) / f"{meta.get('bibId', catalogue_id)}_{title_slug}"
        doc_dir.mkdir(parents=True, exist_ok=True)

        print(f"[+] Found: {meta.get('title')}")
        print(f"[+] Total Pages: {len(pages)}")
        print(f"[+] Output Directory: {doc_dir}")

        # Save metadata and library OCR
        with open(doc_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        if ocr_list:
            ocr_file = doc_dir / "library_indexed_ocr.txt"
            with open(ocr_file, "w", encoding="utf-8") as f:
                for item in ocr_list:
                    vol = item.get("volume", "")
                    seq = item.get("sequence", "")
                    content = item.get("ocrContent", "")
                    f.write(f"--- Page / Sequence {seq} (Volume {vol}) ---\n")
                    f.write(content.strip() + "\n\n")
            print(f"[+] Saved library indexed OCR text ({len(ocr_list)} records) to {ocr_file.name}")

        trace_id = manifest["traceId"]
        downloaded_image_paths = []
        new_downloads = 0

        # Download each page image
        for page in pages:
            page_num = page["pageNumber"]
            page_id = page["id"]
            page_filename = page["fileName"]
            out_img_path = doc_dir / f"page_{page_num:03d}_{page_filename}"

            if out_img_path.exists() and out_img_path.stat().st_size > 0:
                print(f"[=] Page {page_num}/{len(pages)} already downloaded, skipping.")
                downloaded_image_paths.append(out_img_path)
                continue

            print(f"[*] Downloading Page {page_num}/{len(pages)} (ID: {page_id}, {page_filename})...", end="", flush=True)

            download_script = f"""
            const callback = arguments[arguments.length - 1];
            async function downloadPage() {{
                try {{
                    const blobUrl = await somefilePicview({{ id: '{page_id}' }}, '{trace_id}');
                    const resp = await fetch(blobUrl);
                    const blob = await resp.blob();
                    const reader = new FileReader();
                    reader.readAsDataURL(blob);
                    reader.onloadend = function() {{
                        callback({{ success: true, base64: reader.result, size: blob.size }});
                    }};
                }} catch (e) {{
                    callback({{ success: false, error: e.toString() }});
                }}
            }}
            downloadPage();
            """

            page_result = driver.execute_async_script(download_script)
            if not page_result.get("success"):
                print(f" [FAILED: {page_result.get('error')}]")
                continue

            b64_data = page_result["base64"]
            if "," in b64_data:
                _, raw_data = b64_data.split(",", 1)
                img_bytes = base64.b64decode(raw_data)
                with open(out_img_path, "wb") as f:
                    f.write(img_bytes)
                downloaded_image_paths.append(out_img_path)
                new_downloads += 1
                print(f" [DONE: {len(img_bytes) / 1024:.1f} KB]")
            else:
                print(" [FAILED: Invalid Base64 payload]")

            if delay_between_pages > 0:
                time.sleep(delay_between_pages)

        # Assemble PDF if requested (skipped when it exists and no new pages arrived)
        pdf_path = doc_dir / f"{title_slug}.pdf"
        if create_pdf and pdf_path.exists() and new_downloads == 0:
            print(f"[=] PDF already exists, skipping: {pdf_path.name}")
        elif create_pdf and downloaded_image_paths:
            print(f"[*] Compiling {len(downloaded_image_paths)} pages into high-res PDF...")

            pil_images = []
            for p in downloaded_image_paths:
                img = Image.open(p)
                if img.mode != "RGB":
                    img = img.convert("RGB")
                pil_images.append(img)

            first_img = pil_images[0]
            first_img.save(
                pdf_path,
                "PDF",
                resolution=300.0,
                save_all=True,
                append_images=pil_images[1:]
            )
            print(f"[+] Successfully generated PDF: {pdf_path} ({os.path.getsize(pdf_path) / (1024*1024):.2f} MB)")

        print(f"\n[SUCCESS] Document scraping complete! All assets saved to: {doc_dir}")
        return doc_dir

    finally:
        if own_driver:
            driver.quit()


def search_page_url(search_url: str, page: int) -> str:
    """Return the search results URL with its embedded `param` JSON pointed at the given page."""
    parsed = urlparse(search_url)
    query = parse_qs(parsed.query)
    if "param" not in query:
        raise ValueError("Search URL has no 'param' query parameter (expected a searchresults.html URL).")
    param = json.loads(query["param"][0])
    param["current"] = page
    query["param"] = [json.dumps(param, separators=(",", ":"))]
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))


def _capture_search_response(driver, max_wait: float = 45) -> dict:
    """Wait for the page's own search API call and return its JSON `data` payload."""
    driver.get_log("performance")  # drain anything buffered from earlier navigations
    return_value = None
    request_id = None
    start_time = time.time()
    while time.time() - start_time < max_wait:
        for entry in driver.get_log("performance"):
            message = json.loads(entry["message"])["message"]
            params = message.get("params", {})
            if (
                message["method"] == "Network.requestWillBeSent"
                and SEARCH_API_PATH in params.get("request", {}).get("url", "")
            ):
                request_id = params["requestId"]
            elif message["method"] == "Network.loadingFinished" and params.get("requestId") == request_id:
                body = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})["body"]
                return_value = json.loads(body)
                break
        if return_value is not None:
            break
        time.sleep(1)

    if return_value is None:
        raise TimeoutError("Timed out waiting for the search results API response.")
    if str(return_value.get("code")) != "200":
        raise RuntimeError(f"Search API returned an error: {return_value.get('desc')}")
    return return_value["data"]


def collect_search_results(search_url: str, driver) -> list[dict]:
    """
    Loads an HKPL searchresults.html URL (page by page) and returns every result record.

    Each record includes `id` (the catalogueId used by contentcoverpage.html), `bibNo`, `title` and `date`.
    """
    records = []
    seen_ids = set()
    page = 1
    while True:
        url = search_page_url(search_url, page)
        print(f"[*] Loading search results page {page}...")
        driver.get(url)
        data = _capture_search_response(driver)

        page_records = data.get("records") or []
        for record in page_records:
            if record["id"] not in seen_ids:
                seen_ids.add(record["id"])
                records.append(record)

        total = int(data.get("total") or 0)
        size = int(data.get("size") or len(page_records) or 1)
        print(f"[+] Page {page}: {len(page_records)} results ({len(records)}/{total} collected)")
        if not page_records or page * size >= total:
            break
        page += 1

    return records


def scrape_search_results(
    search_url: str,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    create_pdf: bool = True,
    headless: bool = True,
    limit: int | None = None,
    delay_between_docs: float = 2.0,
) -> list[Path]:
    """
    Scrapes every document listed on an HKPL search results page, reusing one browser session.

    Documents are saved exactly as `scrape_document` saves them (e.g. NPCM19250801_The_China_Mail_1925-08-01).
    Pages already on disk are skipped, so an interrupted batch can simply be re-run.

    Returns:
        Paths of the document directories that were scraped successfully.
    """
    driver = init_browser(headless=headless)
    try:
        records = collect_search_results(search_url, driver)
        if limit is not None:
            records = records[:limit]
        print(f"[*] Scraping {len(records)} documents from search results\n")

        doc_dirs = []
        failures = []
        for idx, record in enumerate(records, start=1):
            print(f"=== [{idx}/{len(records)}] {record.get('title')} ({record.get('bibNo')}) ===")
            try:
                doc_dirs.append(
                    scrape_document(
                        record["id"],
                        output_dir=output_dir,
                        create_pdf=create_pdf,
                        headless=headless,
                        driver=driver,
                    )
                )
            except Exception as e:
                print(f"[!] Failed to scrape {record.get('title')}: {e}")
                failures.append(record)
            if delay_between_docs > 0 and idx < len(records):
                time.sleep(delay_between_docs)
            print()

        print(f"[SUCCESS] Batch complete: {len(doc_dirs)}/{len(records)} documents scraped.")
        if failures:
            print("[!] Failed documents (re-run the same command to retry):")
            for record in failures:
                print(f"    - {record.get('title')} (catalogueId={record['id']})")
        return doc_dirs
    finally:
        driver.quit()


def main():
    parser = argparse.ArgumentParser(description="Scrape HKPL MMIS historical newspapers")
    parser.add_argument(
        "--url",
        "-u",
        default="https://sls.hkpl.gov.hk/digital-collection/en/contentcoverpage.html?currentPosition=11&searchId=9cf351140cc64b8485642bf169972160&catalogueId=188038369cb711ef9c2&mainKeyword=China+Mail+strike&isHKMP=",
        help="URL or catalogue ID of the newspaper issue"
    )
    parser.add_argument(
        "--search-url",
        "-s",
        help="searchresults.html URL; scrapes every document in the results (overrides --url)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="With --search-url, only scrape the first N results"
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Target output directory"
    )
    parser.add_argument(
        "--no-pdf",
        action="store_true",
        help="Do not compile pages into a PDF"
    )
    parser.add_argument(
        "--headful",
        action="store_true",
        help="Run browser with visible GUI instead of headless"
    )

    args = parser.parse_args()
    if args.search_url:
        scrape_search_results(
            search_url=args.search_url,
            output_dir=args.output_dir,
            create_pdf=not args.no_pdf,
            headless=not args.headful,
            limit=args.limit,
        )
        return

    scrape_document(
        url_or_id=args.url,
        output_dir=args.output_dir,
        create_pdf=not args.no_pdf,
        headless=not args.headful
    )


if __name__ == "__main__":
    main()
