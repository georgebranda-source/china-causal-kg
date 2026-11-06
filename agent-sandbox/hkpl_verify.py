"""Compare downloaded page images against metadata totalPages for each issue folder."""
import glob
import json
import os
import sys

root = sys.argv[1]
issues = sorted(glob.glob(os.path.join(root, "*", "")))
bad = []
for d in issues:
    with open(os.path.join(d, "metadata.json"), encoding="utf-8") as f:
        total = int(json.load(f)["metadata"]["totalPages"])
    pages = [p for p in glob.glob(os.path.join(d, "page_*")) if os.path.getsize(p) > 0]
    if len(pages) != total:
        bad.append((os.path.basename(os.path.normpath(d)), total, len(pages)))
print(f"issues {len(issues)}, mismatches {len(bad)}")
for b in bad:
    print(b)
