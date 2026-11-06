"""Re-run the second-pass check on saved claims, without extracting again.

Claims that reached the check are judged again with the current check prompt, so every claim is judged by one prompt.
The previous progress file is kept as progress_before_recheck_<hash>.jsonl. Usage (from agent-sandbox/):
    .venv-kg/Scripts/python kg/recheck.py
"""
import json
import shutil
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract as x

path = x.OUT / "progress.jsonl"
records = x.load("progress.jsonl")
old_hash = records[0]["prompt_hash"]
if old_hash == x.PROMPT_HASH:
    sys.exit("check prompt has not changed")
shutil.copy(path, x.OUT / f"progress_before_recheck_{old_hash}.jsonl")

changes = Counter()
tmp = x.OUT / "progress_recheck.tmp"
t0 = time.time()
with open(tmp, "w", encoding="utf-8") as f:
    for n, rec in enumerate(records, 1):
        for c in rec["claims"]:
            if c["status"] not in ("kept", "dropped_by_check"):
                continue
            e = c["extraction"]
            msg = f"Quote: {e['quote']}\nCause: {e['cause']}\nEffect: {e['effect']}"
            try:
                check, _ = x.chat([{"role": "system", "content": x.VERIFY}, {"role": "user", "content": msg}], x.CHECK_SCHEMA, x.CHECK_OPTIONS)
            except RuntimeError as err:  # keep the earlier decision for this claim, and report it
                changes["check failed, earlier decision kept"] += 1
                print(f"FAILED {rec['article_id']}: {err}", flush=True)
                continue
            new = "kept" if check["keep"] else "dropped_by_check"
            changes[f"{c['status']} -> {new}"] += 1
            c["status"], c["check"] = new, check
        rec["prompt_hash"] = x.PROMPT_HASH
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if n % 100 == 0:
            print(f"{time.strftime('%H:%M:%S')} {n}/{len(records)} {dict(changes)}", flush=True)
tmp.replace(path)
manifest = x.finalize(x.load("articles_selected.jsonl"), records)
print(json.dumps({"changes": dict(changes), "minutes": round((time.time() - t0) / 60, 1), "claims": manifest["claims"]}, indent=2), flush=True)
print("ALL DONE", flush=True)
