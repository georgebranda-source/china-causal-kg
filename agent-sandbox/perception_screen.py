"""Perception-vocabulary scores for May-July 1925 pages (dictionary approved by the user 2026-11-16).

Adds a PERCEPTION concept set aimed at the literature's three explanations of the Hongkong strike
(Communist conspiracy, Canton government support, nationalism / anti-foreign feeling), and combines it
with the existing strike score from strike_screen_batch.csv. Matching code is reused unchanged from
strike_screen.py (fuzzy, frozen real-word vocabulary from strike_screen_batch.py).

    perception = number of PERCEPTION concepts found on the page
    combined   = strike score + perception

Writes agent-sandbox/perception_screen.csv and prints pages / hours per cutoff for pages without VL OCR.

Usage (from the repo root):
    agent-sandbox/.venv-kg/Scripts/python agent-sandbox/perception_screen.py
"""

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import strike_screen as S  # noqa: E402
import strike_screen_batch as B  # noqa: E402

MONTHS = ("192505", "192506", "192507")
OUT_CSV = Path("agent-sandbox/perception_screen.csv")
VL_MIN_PER_PAGE = 3

PERCEPTION = {
    # 1. Communist conspiracy
    "bolshevik": ["bolshevik", "bolsheviks", "bolshevism", "bolshevist", "bolshevists"],
    "communist": ["communist", "communists", "communism", "communistic"],
    "reds": ["reds"],
    "soviet": ["soviet", "soviets", "borodin", "moscow"],  # "russian(s)" dropped: general Russia news
    "agitator": ["agitator", "agitators", "instigated", "instigation", "instigators", "ringleaders"],
    "intimidation": ["intimidation", "intimidated", "terrorism", "terrorised", "coercion"],
    # 2. Canton government support
    "canton govt": ["kuomintang", "whampoa", "cantonese"],
    # bare "canton" dropped: on 299 of 572 un-OCRed pages, mostly shipping lists
    # 3. Nationalism / anti-foreign sentiment / triggers
    "nationalism": ["nationalist", "nationalists", "nationalism", "nationalistic"],
    "patriotism": ["patriotic", "patriotism", "patriots", "patriot"],
    "anti-foreign": ["antiforeign", "antibritish", "xenophobia", "xenophobic"],
    "shootings": ["shakee", "shaji", "shameen", "massacre", "massacres", "shooting"],
    "privilege": ["extraterritoriality", "extraterritorial", "imperialism", "imperialist",
                  "imperialists", "unequal", "concessions"],
    "students": ["students", "student"],
}


LATE_VL = {f"page_{n:03d}_NPCM19250602_01_{n:04d}.md" for n in range(11, 15)}  # VL-OCRed 2026-11-02


def frozen_vocab():
    """B.frozen_vocab() minus the four 2 June pages transcribed after the calibration (its assert now fails)."""
    from collections import Counter
    files = [f for f in sorted(B.VL_DIR.glob(B.VOCAB_PAGES)) if f.name not in LATE_VL]
    assert len(files) == 24, len(files)
    counts = Counter()
    for f in files:
        counts.update(re.findall(r"[a-z]+", f.read_text(encoding="utf-8").lower()))
    return {w for w, c in counts.items() if c >= S.VOCAB_MIN_COUNT}


def main():
    real_words = frozen_vocab()
    lib, _ = B.library_ocr()
    strike = {r["page"]: r for r in csv.DictReader(open("agent-sandbox/strike_screen_batch.csv", encoding="utf-8"))}
    vl = {p.name[:-9] for p in B.VL_DIR.glob("page_*_res.json")}
    rows = []
    for f in sorted(B.FAST_DIR.glob("page_*.txt")):
        _, pg, ed, *_ = f.stem.split("_")
        if ed[4:10] not in MONTHS:
            continue
        text = f.read_text(encoding="utf-8") + "\n" + lib.get((ed, int(pg)), "")
        text = text.lower().replace("-", "").translate(str.maketrans("01", "ol"))
        tokens = re.findall(r"[a-z]+", text)
        cands = {c for c in set(tokens) | {a + b for a, b in zip(tokens, tokens[1:])} if 3 <= len(c) <= 22}
        perc = S.matches(cands, PERCEPTION, real_words)
        s = int(strike[f.stem]["score"])
        rows.append({"page": f.stem, "edition": ed, "strike": s, "perception": len(perc),
                     "combined": s + len(perc), "has_vl": f.stem in vl, "perc_concepts": ";".join(sorted(perc))})
    rows.sort(key=lambda r: (-r["combined"], r["page"]))
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    todo = [r for r in rows if not r["has_vl"]]
    print(f"{len(rows)} May-July pages, {len(todo)} without VL OCR")
    print("cutoff | combined>=c: pages to OCR (hours) | perception>=c: pages (hours)")
    for c in (20, 16, 14, 12, 10, 8, 6, 5, 4, 3):
        a = sum(r["combined"] >= c for r in todo)
        b = sum(r["perception"] >= c for r in todo)
        print(f"{c:>6} | {a:>4} ({a * VL_MIN_PER_PAGE / 60:4.1f} h) | {b:>4} ({b * VL_MIN_PER_PAGE / 60:4.1f} h)")
    by_month = {m: sum(r["edition"][4:10] == m and r["combined"] >= 8 for r in todo) for m in MONTHS}
    print("un-OCRed pages with combined >= 8, by month:", by_month)


if __name__ == "__main__":
    main()
