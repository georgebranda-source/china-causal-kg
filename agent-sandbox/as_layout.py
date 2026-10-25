"""AmericanStories YOLOv8 layout detection (the model used by LoC ndnp-open-ocr).

Detection only, no OCR. Numpy/cv2 port of the letterbox + NMS in ndnp-open-ocr's
segmenter.py so it runs without torch. Writes per-page JSON + a box overlay PNG.

Usage:
    <python with onnxruntime,cv2> agent-sandbox\\as_layout.py MODEL.onnx [--conf 0.25] image ...
"""

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

OUT_DIR = Path("agent-sandbox/as_layout_out")
SIZE = 1280
NAMES = [
    "article", "author", "cartoon_or_advertisement", "headline", "image_caption",
    "masthead", "newspaper_header", "page_number", "photograph", "table",
]
COLORS = [
    (0, 160, 0), (200, 0, 200), (0, 140, 255), (0, 0, 255), (255, 120, 0),
    (120, 0, 120), (0, 200, 200), (128, 128, 128), (255, 0, 0), (0, 100, 160),
]


def letterbox(im, size=SIZE, color=(114, 114, 114)):
    h, w = im.shape[:2]
    r = min(size / h, size / w)
    nw, nh = int(round(w * r)), int(round(h * r))
    dw, dh = (size - nw) / 2, (size - nh) / 2
    im = cv2.resize(im, (nw, nh), interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    im = cv2.copyMakeBorder(im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    return im, r, left, top


def detect(sess, img, conf, iou):
    im, r, left, top = letterbox(img)
    x = im[:, :, ::-1].transpose(2, 0, 1)[None].astype(np.float32) / 255.0
    pred = sess.run(None, {sess.get_inputs()[0].name: x})[0][0].T  # (N, 4+nc)
    scores_all = pred[:, 4:]
    cls = scores_all.argmax(1)
    scores = scores_all.max(1)
    keep = scores > conf
    pred, cls, scores = pred[keep], cls[keep], scores[keep]
    # xywh (center) -> xyxy in letterboxed space
    xyxy = np.stack(
        [pred[:, 0] - pred[:, 2] / 2, pred[:, 1] - pred[:, 3] / 2,
         pred[:, 0] + pred[:, 2] / 2, pred[:, 1] + pred[:, 3] / 2], 1)
    # class-agnostic NMS, as in the LoC pipeline (iou 0.10)
    wh = np.stack([xyxy[:, 0], xyxy[:, 1], xyxy[:, 2] - xyxy[:, 0], xyxy[:, 3] - xyxy[:, 1]], 1)
    idx = cv2.dnn.NMSBoxes(wh.tolist(), scores.tolist(), conf, iou)
    idx = np.array(idx).reshape(-1).astype(int)
    h, w = img.shape[:2]
    out = []
    for i in idx:
        x0, y0, x1, y1 = xyxy[i]
        b = [int(max(0, (x0 - left) / r)), int(max(0, (y0 - top) / r)),
             int(min(w, (x1 - left) / r)), int(min(h, (y1 - top) / r))]
        if b[2] > b[0] and b[3] > b[1]:
            out.append({"box": b, "class": NAMES[cls[i]], "conf": round(float(scores[i]), 3)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("images", nargs="+")
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--iou", type=float, default=0.10)
    a = ap.parse_args()

    sess = ort.InferenceSession(a.model, providers=["CPUExecutionProvider"])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in a.images:
        img = cv2.imread(path)
        regions = detect(sess, img, a.conf, a.iou)
        stem = Path(path).stem
        (OUT_DIR / f"{stem}_regions.json").write_text(
            json.dumps(regions, indent=1), encoding="utf-8")
        vis = img.copy()
        for g in regions:
            c = COLORS[NAMES.index(g["class"])]
            x0, y0, x1, y1 = g["box"]
            cv2.rectangle(vis, (x0, y0), (x1, y1), c, 5)
            cv2.putText(vis, g["class"], (x0 + 6, y0 + 40), cv2.FONT_HERSHEY_SIMPLEX, 1.4, c, 3)
        cv2.imwrite(str(OUT_DIR / f"{stem}_layout.png"), cv2.resize(vis, None, fx=0.5, fy=0.5))
        counts = {}
        for g in regions:
            counts[g["class"]] = counts.get(g["class"], 0) + 1
        print(stem, len(regions), counts)


if __name__ == "__main__":
    main()
