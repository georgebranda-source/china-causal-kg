"""Recognize AmericanStories layout regions with PaddleOCR-VL, then group stories.

Layout comes from as_layout.py (agent-sandbox/as_layout_out/<stem>_regions.json).
PaddleOCR-VL's own layout stage is switched off, so each crop is read as one block.
Each headline is attached to the article box directly below it that it overlaps
horizontally; stacked headlines over the same article end up in one story.

Usage (from repo root):
    .venv\\Scripts\\python.exe agent-sandbox\\ocr_vl_crops.py IMAGE
"""

import json
import sys
import tempfile
from pathlib import Path

import cv2
import truststore

truststore.inject_into_ssl()

from paddleocr import PaddleOCRVL  # noqa: E402

LAYOUT_DIR = Path("agent-sandbox/as_layout_out")
OUT_DIR = Path("agent-sandbox/ocr_vl_crops_out")
PAD = 10
SKIP = {"photograph"}  # nothing to read; captions are their own class


def x_overlap_frac(a, b):
    """Fraction of a's width that b covers horizontally."""
    return max(0, min(a[2], b[2]) - max(a[0], b[0])) / max(1, a[2] - a[0])


def group_stories(regions):
    arts = [r for r in regions if r["class"] == "article"]
    heads = [r for r in regions if r["class"] == "headline"]
    for a in arts:
        a["headlines"] = []
    loose = []
    for h in heads:
        best, best_gap = None, None
        for a in arts:
            gap = a["box"][1] - h["box"][3]
            if gap < -40 or x_overlap_frac(a["box"], h["box"]) < 0.5:
                continue
            if best is None or gap < best_gap:
                best, best_gap = a, gap
        (best["headlines"] if best else loose).append(h)
    stories = []
    for a in arts:
        hs = sorted(a["headlines"], key=lambda h: h["box"][1])
        top = hs[0]["box"] if hs else a["box"]
        stories.append({
            "pos": [top[0], top[1]],
            "headline": " / ".join(h["text"] for h in hs),
            "body": a["text"],
            "headline_boxes": [h["box"] for h in hs],
            "body_box": a["box"],
        })
    for h in loose:
        stories.append({"pos": h["box"][:2], "headline": h["text"], "body": "",
                        "headline_boxes": [h["box"]], "body_box": None})
    return stories


def main(image):
    stem = Path(image).stem
    regions = json.loads((LAYOUT_DIR / f"{stem}_regions.json").read_text(encoding="utf-8"))
    img = cv2.imread(image)
    h, w = img.shape[:2]

    pipeline = PaddleOCRVL(
        use_layout_detection=False,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        vl_rec_backend="native",
        device="gpu",  # Remove this if not running on GISCOMPUTER
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for i, r in enumerate(regions):
            if r["class"] in SKIP:
                r["text"] = ""
                continue
            x0, y0, x1, y1 = r["box"]
            crop = img[max(0, y0 - PAD):min(h, y1 + PAD), max(0, x0 - PAD):min(w, x1 + PAD)]
            path = Path(tmp) / f"r{i}.png"
            cv2.imwrite(str(path), crop)
            parts = []
            for res in pipeline.predict(str(path), prompt_label="ocr"):
                parts += [b["block_content"] for b in res.json["res"]["parsing_res_list"]]
            r["text"] = "\n".join(p.strip() for p in parts if p.strip())
            print(f"{i + 1}/{len(regions)} {r['class']}: {r['text'][:60]!r}", flush=True)

    (OUT_DIR / f"{stem}_regions_text.json").write_text(
        json.dumps(regions, ensure_ascii=False, indent=1), encoding="utf-8")

    stories = group_stories(regions)
    X_TOL = max(int(w * 0.06), 100)
    stories.sort(key=lambda s: (s["pos"][0] // X_TOL, s["pos"][1]))
    (OUT_DIR / f"{stem}_stories.json").write_text(
        json.dumps(stories, ensure_ascii=False, indent=1), encoding="utf-8")
    md = [f"## {s['headline'] or '(no headline)'}\n\n{s['body']}\n" for s in stories]
    (OUT_DIR / f"{stem}_stories.md").write_text("\n".join(md), encoding="utf-8")
    other = [r for r in regions if r["class"] not in ("article", "headline", "photograph")]
    print(f"{len(stories)} stories; {len(other)} other regions (ads, captions, masthead...)")


if __name__ == "__main__":
    main(sys.argv[1])
