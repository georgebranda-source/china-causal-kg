"""Shared paths and helpers for the May-July 1925 perception run (plan: kg/analysis/perception/PLAN.md).

All output goes to kg/out/perception/ (or kg/out/perception_test/ with PERCEPTION_TEST=1). Nothing here writes to
kg/out/graph_v1, kg/out/batches or kg/out/combined, so v1 is untouched.
"""
import csv
import json
import os
import re
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
KG = HERE.parent
SANDBOX = KG.parent
REPO = SANDBOX.parent
OUT = KG / "out" / ("perception_test" if os.environ.get("PERCEPTION_TEST") else "perception")
OUT.mkdir(parents=True, exist_ok=True)
STOP = KG / "out" / "perception.stop"
LOG = OUT / "run.log"
STATUS = OUT / "status.json"
MONTHS = ("192505", "192506", "192507")
# Extension (user, 2026-11-16, option A): later months listed in PERCEPTION_EXTRA_MONTHS (comma-separated YYYYMM) add every
# page that already has VL OCR; no new OCR for them.
EXTRA_MONTHS = tuple(m for m in os.environ.get("PERCEPTION_EXTRA_MONTHS", "").split(",") if m)
CUTOFF = 7  # combined strike + perception score for new VL OCR (user, 2026-11-16)
VL_DIR = SANDBOX / "ocr_vl_out"


def log(msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def status(**kw):
    s = json.loads(STATUS.read_text(encoding="utf-8")) if STATUS.exists() else {}
    s.update(kw, updated=time.strftime("%Y-%m-%d %H:%M:%S"))
    STATUS.write_text(json.dumps(s, indent=1), encoding="utf-8")


def has_vl(page):
    return (VL_DIR / f"{page}_res.json").exists() and (VL_DIR / f"{page}_blocks.json").exists()


def screen_rows():
    return list(csv.DictReader(open(SANDBOX / "perception_screen.csv", encoding="utf-8")))


def new_ocr_pages():
    """May-July pages with no VL output at screening time and combined score >= CUTOFF, highest first."""
    return [r["page"] for r in screen_rows() if r["has_vl"] == "False" and int(r["combined"]) >= CUTOFF]


def corpus_pages():
    """Every May-July page that has VL output now (the 301 earlier ones plus whatever new OCR finished)."""
    pages = {r["page"] for r in screen_rows() if has_vl(r["page"])}
    for m in EXTRA_MONTHS:
        pages |= {f.name[:-9] for f in VL_DIR.glob(f"page_*_NPCM{m}*_res.json") if has_vl(f.name[:-9])}
    return sorted(pages)


def load_jsonl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8")] if Path(path).exists() else []


def cap_json_retries(x, attempts=2):
    """Replace extract.chat with the same function, but give up after `attempts` tries when the reply is not valid JSON
    (the model looping to the token limit). v1 tried 4 times, doubling the limit each time, which costs ~70 s per try.
    Network errors still get 4 tries. Prompts, schemas and options are unchanged."""
    import urllib.request as ur

    def chat(messages, schema, options):
        body = {"model": x.MODEL, "stream": False, "think": False, "format": schema, "keep_alive": "30m",
                "options": options, "messages": messages}
        last, bad_json = None, 0
        for attempt in range(4):
            try:
                req = ur.Request(x.URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
                reply = json.load(ur.urlopen(req, timeout=600))
                return json.loads(reply["message"]["content"]), reply.get("done_reason")
            except json.JSONDecodeError as e:
                last, bad_json = e, bad_json + 1
                if bad_json >= attempts:
                    raise RuntimeError(f"model call failed (invalid JSON): {e}")
                body["options"] = dict(options, num_predict=options["num_predict"] * 2)
            except OSError as e:
                last = e
                time.sleep(15 * (attempt + 1))
        raise RuntimeError(f"model call failed: {last}")

    x.chat = chat
