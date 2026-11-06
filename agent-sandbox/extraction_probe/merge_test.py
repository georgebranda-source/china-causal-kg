"""Compare dedup rules on the saved whole-article and chunk claims."""
import json, re, sys
from collections import defaultdict
from pathlib import Path
from rapidfuzz import fuzz

sys.stdout.reconfigure(encoding="utf-8")
log = json.load(open(Path(__file__).parent / "rulings_test_output.json", encoding="utf-8"))
norm = lambda s: re.sub(r"\s+", " ", s).strip().lower()
arts = defaultdict(list)
for run in ("whole", "chunks"):
    for a in log[run]:
        for q in a["rel"]:
            arts[str(a["head"])].append(dict(q, run=run))


def quote_overlap(a, b):
    return fuzz.partial_ratio(norm(a["quote"]), norm(b["quote"])) >= 90


def same_sides(a, b, t=60):
    return fuzz.token_set_ratio(norm(a["cause"]), norm(b["cause"])) >= t and fuzz.token_set_ratio(norm(a["effect"]), norm(b["effect"])) >= t


RULES = {"exact quote": lambda a, b: norm(a["quote"]) == norm(b["quote"]),
         "overlapping quote": quote_overlap,
         "overlapping quote + similar cause and effect": lambda a, b: quote_overlap(a, b) and same_sides(a, b)}
shown = []
for name, same in RULES.items():
    total = 0
    for head, cl in arts.items():
        kept = []
        for c in cl:
            d = next((k for k in kept if same(c, k)), None)
            if d is None:
                kept.append(c)
            elif name.startswith("overlapping quote +") is False and name == "overlapping quote" and not same_sides(c, d):
                shown.append((head, d, c))
        total += len(kept)
    print(f"{name}: {sum(map(len, arts.values()))} -> {total}")
print("\nMerged by overlap alone, but cause or effect differs:")
for h, a, b in shown:
    print(f"[{h[:18]}]\n  {a['cause'][:50]} -> {a['effect'][:50]}\n  {b['cause'][:50]} -> {b['effect'][:50]}")
