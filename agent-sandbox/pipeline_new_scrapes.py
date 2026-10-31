"""Unattended OCR pipeline for newly scraped China Mail pages: fast OCR -> strike score -> VL OCR (score >= 8).

Keeps up with a scrape that is still running (scrape_hkpl.py / hkpl_queue.py), one cycle at a time:

1. wait until no other ocr_vl.py run is using the GPU
2. fast-OCR (ocr_fast.py) every edition the scraper has finished (no file written for SETTLE_S)
3. rescore all pages (strike_screen_batch.py: same scoring as the June–July selection)
4. VL-OCR (ocr_vl.py) the next VL_CHUNK pages with score >= CUTOFF that have no VL output, highest score first
5. repeat; when the scraper has stopped and nothing is left to do, exit

Failures: a fast-OCR batch that fails is retried edition by edition; a page that fails twice (in either
step) is listed in pipeline_failed.txt and skipped. Create agent-sandbox/pipeline.stop to stop cleanly.

Usage (from the repo root):
    agent-sandbox/.venv-kg/Scripts/python -u agent-sandbox/pipeline_new_scrapes.py
"""

import csv
import glob
import json
import os
import subprocess
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SB = REPO / "agent-sandbox"
PADDLE_PY = str(REPO / ".venv" / "Scripts" / "python.exe")  # paddleocr lives in the project venv
KG_PY = sys.executable  # rapidfuzz lives here (.venv-kg)
FAST_DIR = SB / "ocr_fast_out"
VL_DIR = SB / "ocr_vl_out"
SCORES = SB / "strike_screen_batch.csv"
LOG = SB / "pipeline_new_scrapes.log"
FAILED = SB / "pipeline_failed.txt"
STOP = SB / "pipeline.stop"
VL_LIST = SB / "vl_pages_batch_current.txt"

CUTOFF = 8
SETTLE_S = 600  # an edition folder untouched this long is complete
VL_CHUNK = 20  # VL pages per cycle (~1 h), so fast OCR keeps up with the scraper in between
FAST_BATCH = 25  # editions per fast-OCR run
IDLE_SLEEP_S = 600

ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}
fail_count = Counter()


def log(msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def failed_pages():
    return set(FAILED.read_text(encoding="utf-8").split()) if FAILED.exists() else set()


def mark_failed(page, why):
    with open(FAILED, "a", encoding="utf-8") as fh:
        fh.write(page + "\n")
    log(f"FAILED twice, skipping: {page} ({why})")


def running(pattern):
    """True if another process's command line contains pattern (PowerShell CIM query)."""
    cmd = ["powershell", "-NoProfile", "-Command",
           "Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | "
           "ForEach-Object { $_.ProcessId.ToString() + ' ' + $_.CommandLine }"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout
    except Exception:
        return False
    me = str(os.getpid())
    return any(pattern in line and not line.startswith(me + " ") and "pipeline_new_scrapes" not in line
               for line in out.splitlines())


def scraper_running():
    return running("scrape_hkpl.py") or running("hkpl_queue.py")


def run(args, logfile):
    with open(SB / logfile, "a", encoding="utf-8") as fh:
        fh.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} {' '.join(args)[:300]}\n")
        fh.flush()
        return subprocess.run(args, cwd=REPO, stdout=fh, stderr=subprocess.STDOUT, env=ENV).returncode


def pending_fast_editions():
    """Edition folders (outside June–July) with pages lacking fast-OCR text, that the scraper has finished."""
    now, scraping, eds = time.time(), scraper_running(), []
    bad = failed_pages()
    for d in sorted(glob.glob(str(REPO / "data/raw/hkpl/*/NPCM*"))):
        pages = [p for p in glob.glob(os.path.join(d, "page_*.png"))
                 if not (FAST_DIR / (Path(p).stem + ".txt")).exists() and Path(p).stem not in bad]
        if not pages:
            continue
        newest = max(os.path.getmtime(f) for f in glob.glob(os.path.join(d, "*")))
        if scraping and now - newest < SETTLE_S:
            continue  # still being written
        eds.append((d, pages))
    return eds


def fast_ocr(eds):
    for i in range(0, len(eds), FAST_BATCH):
        batch = eds[i:i + FAST_BATCH]
        log(f"fast OCR: {len(batch)} editions, {sum(len(p) for _, p in batch)} pages")
        rc = run([PADDLE_PY, "-u", "agent-sandbox/ocr_fast.py"] + [os.path.join(d, "page_*.png") for d, _ in batch],
                 "ocr_fast_batch.log")
        if rc == 0:
            continue
        log(f"fast OCR batch exit {rc}; retrying page by page")
        for d, pages in batch:
            for p in pages:
                if (FAST_DIR / (Path(p).stem + ".txt")).exists():
                    continue
                for _ in range(2):
                    if run([PADDLE_PY, "-u", "agent-sandbox/ocr_fast.py", p], "ocr_fast_batch.log") == 0:
                        break
                else:
                    mark_failed(Path(p).stem, "fast OCR")


def rescore():
    rc = run([KG_PY, "agent-sandbox/strike_screen_batch.py"], "strike_screen_batch.log")
    if rc != 0:
        raise RuntimeError(f"strike_screen_batch.py exit {rc}")


def vl_backlog():
    if not SCORES.exists():
        return []
    images = {Path(p).stem: p for p in glob.glob(str(REPO / "data/raw/hkpl/*/NPCM*/page_*.png"))}
    bad = failed_pages()
    rows = [r for r in csv.DictReader(open(SCORES, encoding="utf-8"))
            if int(r["score"]) >= CUTOFF and r["page"] in images and r["page"] not in bad
            and not (VL_DIR / f"{r['page']}_blocks.json").exists()]
    rows.sort(key=lambda r: (-int(r["score"]), r["page"]))
    return [images[r["page"]] for r in rows]


def vl_ocr(paths):
    chunk = paths[:VL_CHUNK]
    VL_LIST.write_text("\n".join(os.path.relpath(p, REPO).replace(os.sep, "/") for p in chunk) + "\n", encoding="utf-8")
    log(f"VL OCR: {len(chunk)} pages (backlog {len(paths)})")
    rc = run([PADDLE_PY, "-u", "agent-sandbox/ocr_vl.py", f"@{os.path.relpath(VL_LIST, REPO)}"], "ocr_vl_batch.log")
    if rc == 0:
        return
    # the first page without output is the one it died on
    stuck = next((Path(p).stem for p in chunk if not (VL_DIR / f"{Path(p).stem}_blocks.json").exists()), None)
    log(f"VL OCR exit {rc}; stopped at {stuck}")
    if stuck:
        fail_count[stuck] += 1
        if fail_count[stuck] >= 2:
            mark_failed(stuck, f"VL OCR exit {rc}")
        else:
            time.sleep(60)  # e.g. GPU memory held by something else; give it a minute


def main():
    log(f"pipeline start (pid {os.getpid()})")
    while running("ocr_vl.py"):
        if STOP.exists():
            return log("stop file found; exiting")
        time.sleep(120)
    log("no other VL run active; starting cycles")
    errors = 0
    while True:
        if STOP.exists():
            return log("stop file found; exiting")
        try:
            eds = pending_fast_editions()
            if eds:
                fast_ocr(eds)
                rescore()
            elif not SCORES.exists():
                rescore()
            backlog = vl_backlog()
            if backlog:
                vl_ocr(backlog)
            elif not eds:
                if scraper_running():
                    time.sleep(IDLE_SLEEP_S)
                else:
                    # one last sweep for editions finished since the check above
                    if not pending_fast_editions() and not vl_backlog():
                        n = sum(1 for _ in VL_DIR.glob("page_*_blocks.json"))
                        return log(f"done: scraper stopped, nothing left. VL pages on disk: {n}; "
                                   f"failed: {len(failed_pages())}")
            errors = 0
        except Exception:
            errors += 1
            log(f"cycle error {errors}:\n{traceback.format_exc()}")
            if errors >= 5:
                return log("5 consecutive cycle errors; exiting")
            time.sleep(300)


if __name__ == "__main__":
    main()
