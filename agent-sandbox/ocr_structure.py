"""Layout-aware OCR for multi-column news strips using PP-StructureV3.

Unlike plain PaddleOCR, PP-StructureV3 first detects layout blocks (titles,
text columns, etc.) and their reading order, then OCRs each block, so text
from adjacent columns is not interleaved.

Usage (from repo root):
    .venv\\Scripts\\python.exe agent-sandbox\\ocr_structure.py [image ...]
"""

import json
import sys
from pathlib import Path

import truststore

# Norton re-signs HTTPS traffic with its own root cert, which Python's bundled
# CA list rejects; use the Windows cert store so model downloads work.
truststore.inject_into_ssl()

from paddleocr import PPStructureV3  # noqa: E402

OUT_DIR = Path("agent-sandbox/ocr_structure_out")

pipeline = PPStructureV3(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    # Not needed for news strips; disabling skips those model downloads.
    use_table_recognition=False,
    use_formula_recognition=False,
    use_seal_recognition=False,
    use_chart_recognition=False,
    engine="paddle",
    device="gpu",  # Remove this if not running on GISCOMPUTER
)

images = sys.argv[1:] or ["data/raw/test.png"]
OUT_DIR.mkdir(parents=True, exist_ok=True)

for image in images:
    for res in pipeline.predict(image):
        res.save_to_json(OUT_DIR)
        res.save_to_markdown(OUT_DIR)
        res.save_to_img(OUT_DIR)  # layout boxes + reading order overlay

        # Compact per-block summary, in reading order.
        blocks = [
            {"label": b["block_label"], "text": b["block_content"]}
            for b in res.json["res"]["parsing_res_list"]
        ]
        summary = OUT_DIR / f"{Path(image).stem}_blocks.json"
        summary.write_text(
            json.dumps(blocks, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"{image}: {len(blocks)} blocks -> {summary}")
