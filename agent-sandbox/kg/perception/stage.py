"""Run a v1 pipeline stage (kg/extract.py or kg/normalise.py) unchanged, with output redirected to the perception folder.

Usage: .venv-kg/Scripts/python kg/perception/stage.py extract|normalise [--limit N]
The v1 modules read their output folder from extract.OUT and their stop file from extract.STOP; both are repointed here, so
the prompts, schemas, options and few-shot examples are exactly v1's (same prompt hashes).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

sys.path.insert(0, str(C.KG))
import extract as x  # noqa: E402

x.OUT, x.STOP = C.OUT, C.STOP
C.cap_json_retries(x)

# Articles whose extraction fails with invalid JSON (the model loops) are deterministic failures (temperature 0, seed 1):
# record them once in extract_skip.txt and leave them out of later passes, instead of re-running them for ~2 min each.
SKIP = C.OUT / "extract_skip.txt"
_load, _process = x.load, x.process


def load(name, folder=None):
    rows = _load(name, folder)
    if name == "articles_selected.jsonl" and folder is None and SKIP.exists():
        skip = set(SKIP.read_text(encoding="utf-8").split())
        rows = [r for r in rows if r["article_id"] not in skip]
    return rows


def process(a, shots):
    try:
        return _process(a, shots)
    except RuntimeError as e:
        if "invalid JSON" in str(e):
            with open(SKIP, "a", encoding="utf-8") as fh:
                fh.write(a["article_id"] + "\n")
        raise


x.load, x.process = load, process
stage = sys.argv.pop(1)
if stage == "extract":
    x.main()
elif stage == "normalise":
    import normalise
    normalise.main()
else:
    raise SystemExit(f"unknown stage {stage}")
