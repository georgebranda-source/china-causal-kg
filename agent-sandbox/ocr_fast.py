"""Fast PP-OCR text dump for page screening (recall matters, accuracy doesn't).

Writes one plain-text file per page to agent-sandbox/ocr_fast_out/<stem>.txt.
Resumable. Args may be paths or quoted glob patterns.

Usage (from repo root):
    .venv\Scripts\python.exe -u agent-sandbox\ocr_fast.py 'data/raw/hkpl/**/page_*.png'
"""

import glob
import sys
import time
from pathlib import Path

import truststore

truststore.inject_into_ssl()

from paddleocr import PaddleOCR  # noqa: E402

OUT_DIR = Path("agent-sandbox/ocr_fast_out")

ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    text_detection_model_name="PP-OCRv5_mobile_det",
    text_recognition_model_name="PP-OCRv5_mobile_rec",
    device="gpu",  # Remove this if not running on GISCOMPUTER
)

images = [p for arg in sys.argv[1:] for p in (sorted(glob.glob(arg, recursive=True)) or [arg])]
OUT_DIR.mkdir(parents=True, exist_ok=True)

for image in images:
    out = OUT_DIR / f"{Path(image).stem}.txt"
    if out.exists():
        continue
    t0 = time.time()
    lines = []
    for res in ocr.predict(image):
        lines += res["rec_texts"]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"{Path(image).stem}: {len(lines)} lines, {time.time() - t0:.1f}s", flush=True)
