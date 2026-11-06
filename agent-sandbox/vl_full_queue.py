"""VL-OCR every page (all scores) of each collection group in turn, after the June–July 1925 full run.

Order set by the user (2026-11-02): Aug–Sep 1925, Apr–May 1925, Oct–Nov 1925, Dec 1925–Jan 1926, then
the following months in pairs to Nov 1926. Each group is one run of
`pipeline_new_scrapes.py --only <collections> --tiers 0` (all pages of the group, in date order), which
exits when the group has no pages left without VL text.

Waits while another pipeline run is active. Create agent-sandbox/pipeline.stop to stop: the current
pipeline run stops after its batch, and no further group is started.

Usage (from the repo root):
    agent-sandbox/.venv-kg/Scripts/python -u agent-sandbox/vl_full_queue.py
"""

import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline_new_scrapes import KG_PY, REPO, STOP, log  # noqa: E402

GROUPS = [
    ["china_mail_aug_sep_1925"],
    ["china_mail_apr_1925", "china_mail_may_1925"],
    ["china_mail_oct_1925", "china_mail_nov_1925"],
    ["china_mail_dec_1925", "china_mail_jan_1926"],
    ["china_mail_feb_1926", "china_mail_mar_1926"],
    ["china_mail_apr_1926", "china_mail_may_1926"],
    ["china_mail_jun_1926", "china_mail_jul_1926"],
    ["china_mail_aug_1926", "china_mail_sep_1926"],
    ["china_mail_oct_1926", "china_mail_nov_1926"],
]


def pipeline_running():
    """True if a pipeline_new_scrapes.py process is running (its own running() skips pipeline processes)."""
    cmd = ["powershell", "-NoProfile", "-Command",
           "Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | ForEach-Object { $_.CommandLine }"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout
    except Exception:
        return True  # unsure: keep waiting rather than start a second VL run
    return "pipeline_new_scrapes.py" in out


def main():
    log("full-VL queue start; waiting for the current pipeline run")
    while pipeline_running():
        if STOP.exists():
            return log("full-VL queue: stop file found; exiting")
        time.sleep(120)
    for group in GROUPS:
        if STOP.exists():
            return log("full-VL queue: stop file found; exiting")
        log(f"full-VL queue: starting {','.join(group)}")
        rc = subprocess.run([KG_PY, "-u", "agent-sandbox/pipeline_new_scrapes.py", "--only", ",".join(group),
                             "--tiers", "0"], cwd=REPO).returncode
        log(f"full-VL queue: {','.join(group)} finished (exit {rc})")
    log("full-VL queue: all groups done")


if __name__ == "__main__":
    main()
