"""Extend the perception run month by month, Aug 1925 - Apr 1926 (user, 2026-11-16, option A: existing VL pages only).

For each month in turn: add that month's VL pages to the corpus -> build -> extract -> speaker -> normalise -> graph, then
copy the cumulative graph to kg/out/perception/snapshots/through_YYYY-MM/. Every stage resumes from its own progress file,
so each month only processes its new articles, and a relaunch picks up where it stopped. Same instrument as May-July
(same prompts, anchors, rules); stop cleanly with kg/out/perception.stop.

Usage (from agent-sandbox/): .venv-kg/Scripts/python -u kg/perception/months.py
"""
import json
import os
import shutil
import sys
import time
from pathlib import Path

MONTHS = ["192508", "192509", "192510", "192511", "192512", "192601", "192602", "192603", "192604"]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import run as R  # noqa: E402

SNAP = C.OUT / "snapshots"


def snapshot(name):
    dst = SNAP / name
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(C.OUT / "graph", dst)
    C.log(f"snapshot -> {dst.relative_to(C.SANDBOX)}")


def main():
    C.log(f"=== month-by-month extension start (pid {os.getpid()}): {MONTHS[0]}..{MONTHS[-1]}")
    C.status(pid=os.getpid(), phase="months", started=time.strftime("%Y-%m-%d %H:%M:%S"), step="start")
    if not (SNAP / "1925-05_07").exists():
        snapshot("1925-05_07")  # the finished May-July graph, frozen before anything changes
    done = json.loads(C.STATUS.read_text(encoding="utf-8")).get("months_done", [])
    try:
        for i, m in enumerate(MONTHS):
            label = f"{m[:4]}-{m[4:]}"
            if label in done and (SNAP / f"through_{label}").exists():
                continue
            extra = ",".join(MONTHS[:i + 1])
            os.environ["PERCEPTION_EXTRA_MONTHS"] = extra
            R.ENV["PERCEPTION_EXTRA_MONTHS"] = extra
            C.status(month=label)
            C.log(f"--- month {label}")
            if not R.stage(f"build:{label}", ["build"], done_marker=None):
                C.log(f"build failed for {label}; stopping")
                C.status(step=f"stopped: build failed {label}")
                return
            rep = json.loads((C.OUT / "corpus_report.json").read_text(encoding="utf-8"))
            C.log(f"corpus: {rep['pages']} pages, {rep['selected']} selected; by month {rep['by_month']}")
            ok = R.stage(f"extract:{label}", ["extract"])
            ok = R.stage(f"speaker:{label}", ["speaker"]) and ok
            ok = R.stage(f"normalise:{label}", ["normalise"]) and ok
            if not ok:
                C.log(f"WARNING: a model stage did not complete for {label}; graph built from what finished")
            if R.stage(f"graph:{label}", ["graph"], done_marker=None):
                snapshot(f"through_{label}")
                done.append(label)
                C.status(months_done=done, last_month_done=time.strftime("%H:%M"))
            else:
                C.log(f"graph failed for {label}")
        C.status(step="MONTHS DONE")
        C.log("=== MONTHS DONE")
    except R.Stopped:
        C.status(step="stopped by stop file")
        C.log("stopped by stop file")
    except Exception:
        import traceback
        C.log("CRASH: " + traceback.format_exc())
        C.status(step="crashed")
        raise


if __name__ == "__main__":
    main()
