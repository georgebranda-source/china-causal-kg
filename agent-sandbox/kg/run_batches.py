"""Run batches in order: articles, extraction + check, normalisation, combined graph.

Create kg/out/batches.stop to stop cleanly. Finished articles are kept, so running this again resumes where it stopped.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

KG = Path(__file__).resolve().parent
STOP = KG / "out" / "batches.stop"
# Done earlier, in this order: 1925-08-09, 1925-04-05, 1925-10-11
BATCHES = [("1925-12_1926-01", ["192512", "192601"]), ("1926-02-03", ["192602", "192603"]), ("1926-04-05", ["192604", "192605"]),
           ("1926-06-07", ["192606", "192607"]), ("1926-08-09", ["192608", "192609"]), ("1926-10-11", ["192610", "192611"])]


def step(args, batch=None):
    print(time.strftime("%H:%M:%S"), " ".join(map(str, args)), flush=True)
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", **({"KG_BATCH": batch} if batch else {})}
    return subprocess.run([sys.executable, *map(str, args)], env=env).returncode


for name, months in BATCHES:
    if STOP.exists():
        break
    if step([KG / "build_batch.py", name, *months]):
        print("article build failed:", name, flush=True)
        break
    for _ in (1, 2):  # the second pass retries any failed articles
        step([KG / "extract.py"], name)
    for _ in (1, 2):
        step([KG / "normalise.py"], name)
    if not STOP.exists():
        step([KG / "combine.py"])
        print(time.strftime("%H:%M:%S"), "BATCH DONE", name, flush=True)
print(time.strftime("%H:%M:%S"), "stopped by stop file" if STOP.exists() else "ALL BATCHES DONE", flush=True)
