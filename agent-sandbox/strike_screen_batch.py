"""Strike-relevance scores for pages from any scrape batch, under the same conditions as the
June–July 1925 selection.

Reuses the matching code in strike_screen.py unchanged. Two differences from running that script:

- The "real word" vocabulary is frozen to the 24 VL pages of 1925-06-01/02 that existed when the
  June–July scores in strike_screen.csv were made. strike_screen.py rebuilds it from every VL page on
  disk, so its scores drift as more pages are transcribed; freezing it keeps the score-8 cutoff
  meaning the same for every month.
- It scores every page that has fast-OCR text, for every collection under data/raw/hkpl/, and writes
  strike_screen_batch.csv, leaving strike_screen.csv (the record of the June–July run) untouched.

Usage (from the repo root, python with rapidfuzz):
    agent-sandbox/.venv-kg/Scripts/python agent-sandbox/strike_screen_batch.py
    agent-sandbox/.venv-kg/Scripts/python agent-sandbox/strike_screen_batch.py --check   # reproduce strike_screen.csv
"""

import csv
import glob
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import strike_screen as S  # noqa: E402

FAST_DIR = Path("agent-sandbox/ocr_fast_out")
VL_DIR = Path("agent-sandbox/ocr_vl_out")
EDITIONS = "data/raw/hkpl/*/NPCM*"
OUT_CSV = Path("agent-sandbox/strike_screen_batch.csv")
VOCAB_PAGES = "page_*NPCM1925060[12]*.md"  # the 24 calibration pages, as at the June–July scoring


def frozen_vocab():
    counts = Counter()
    files = sorted(VL_DIR.glob(VOCAB_PAGES))
    assert len(files) == 24, f"expected the 24 calibration pages, found {len(files)}"
    for f in files:
        counts.update(re.findall(r"[a-z]+", f.read_text(encoding="utf-8").lower()))
    return {w for w, c in counts.items() if c >= S.VOCAB_MIN_COUNT}


def library_ocr():
    lib, collection = {}, {}
    for d in glob.glob(EDITIONS):
        ed = Path(d).name[:12]
        collection[ed] = Path(d).parent.name
        meta_path = Path(d) / "metadata.json"
        if not meta_path.exists():
            continue
        meta = json.load(open(meta_path, encoding="utf-8"))
        for p in meta.get("ocrList") or []:
            lib[(ed, p["sequence"])] = p.get("ocrContent") or ""
    return lib, collection


def score_page(path, lib, real_words):
    _, pg, ed, *_ = path.stem.split("_")
    text = path.read_text(encoding="utf-8") + "\n" + lib.get((ed, int(pg)), "")
    text = text.lower().replace("-", "").translate(str.maketrans("01", "ol"))
    tokens = re.findall(r"[a-z]+", text)
    cands = set(tokens) | {a + b for a, b in zip(tokens, tokens[1:])}
    cands = {c for c in cands if 3 <= len(c) <= 22}
    core, broad = S.matches(cands, S.CORE, real_words), S.matches(cands, S.BROAD, real_words)
    return {
        "page": path.stem, "edition": ed, "seq": int(pg),
        "score": 3 * len(core) + len(broad),
        "flag": bool(core) or len(broad) >= 2,
        "core": ";".join(sorted(core)), "broad": ";".join(sorted(broad)),
    }


def main():
    real_words = frozen_vocab()
    lib, collection = library_ocr()
    rows = []
    for f in sorted(FAST_DIR.glob("page_*.txt")):
        r = score_page(f, lib, real_words)
        r["collection"] = collection.get(r["edition"], "")
        rows.append(r)

    if "--check" in sys.argv:
        old = {r["page"]: r for r in csv.DictReader(open("agent-sandbox/strike_screen.csv", encoding="utf-8"))}
        new = {r["page"]: r for r in rows if r["page"] in old}
        diff = [p for p in old if p not in new or str(new[p]["score"]) != old[p]["score"]]
        print(f"checked {len(old)} June–July pages against strike_screen.csv: {len(diff)} differ {diff[:5]}")
        return

    rows.sort(key=lambda r: (-r["score"], r["page"]))
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} pages scored; >= 8: {sum(r['score'] >= 8 for r in rows)}; vocab {len(real_words)} words")


if __name__ == "__main__":
    main()
