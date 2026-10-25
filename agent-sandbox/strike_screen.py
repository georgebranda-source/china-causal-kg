"""Score pages for worker-strike relevance from fast-OCR text (+ library headlines).

Built for noisy OCR. Tokens are matched to concept term lists with an edit-distance
tolerance of ~20% of word length, and adjacent tokens are also joined so a word split
by the OCR ("str ike") still matches. A concept counts once however many of its variants
appear. Tokens that are ordinary words in the (much cleaner) PaddleOCR-VL text, such as
"onions" or "wales", are never treated as OCR errors of a term; real misreadings like
"gtrikes" don't occur there, so they still match.

    CORE   direct strike vocabulary; one concept is enough to flag a page
    BROAD  labour / unrest vocabulary; needs two distinct concepts
    score = 3 * CORE concepts + BROAD concepts   (higher = more likely relevant)

Writes agent-sandbox/strike_screen.csv, ranked by score.

Usage (python with rapidfuzz, from repo root):
    <python> agent-sandbox/strike_screen.py
"""

import csv
import glob
import json
import re
from collections import Counter
from pathlib import Path

from rapidfuzz import process
from rapidfuzz.distance import Levenshtein

FAST_DIR = Path("agent-sandbox/ocr_fast_out")
VL_DIR = Path("agent-sandbox/ocr_vl_out")
EDITIONS = "data/raw/hkpl/china_mail_june_july_1925/NPCM*"
OUT_CSV = Path("agent-sandbox/strike_screen.csv")
VOCAB_MIN_COUNT = 3  # a token seen this often in VL text is a real word
# Known one-edit neighbours of CORE terms (cricket season!) that the VL vocabulary misses.
BENIGN = {"wicket", "wickets", "ticket", "tickets", "picked", "pocket", "pockets", "pocketing",
          "packet", "packets", "stroke", "strokes", "stripe", "stripes", "strife", "strive", "stride"}

CORE = {
    "strike": ["strike", "strikes", "striker", "strikers", "striking"],
    "walkout": ["walkout", "walkouts"],
    "boycott": ["boycott", "boycotts", "boycotted"],
    "picket": ["picket", "pickets", "picketing"],
    "lockout": ["lockout"],
    "stoppage": ["stoppage"],
    "downed tools": ["downedtools"],
}
BROAD = {
    "labour": ["labour", "labor"],
    "worker": ["worker", "workers", "workmen", "workman"],
    "coolie": ["coolie", "coolies"],
    "union": ["union", "unions", "unionist"],
    "wage": ["wages", "wage"],
    "employ": ["employees", "employers"],
    "agitation": ["agitator", "agitators", "agitation"],
    "riot": ["rioter", "rioters", "riot", "riots"],
    "demonstration": ["demonstration", "demonstrators"],
    "mob": ["mob"],
    "disorder": ["disorder", "disorders"],
    "unrest": ["unrest"],
    "dispute": ["dispute", "disputes"],
    "negotiation": ["negotiations", "arbitration"],
    "sympathy": ["sympathy"],
    "trades": ["seamen", "dockers", "compositors", "printers", "tramway"],
    "mill": ["mill", "mills"],
    "factory": ["factory", "factories"],
    "student": ["students"],
    "communist": ["communist", "communists", "bolshevik", "bolshevism", "soviet"],
    "extremist": ["extremists"],
    "propaganda": ["propaganda"],
    "anti-foreign": ["antiforeign"],
    "shameen": ["shameen", "shakee"],
    "martial": ["martial"],
    "casualties": ["casualties", "massacre", "assassination"],
    "tsingtao": ["tsingtao"],
    "grievance": ["grievances", "demands", "protest", "massmeeting"],
}


def tol(word):
    return 0 if len(word) <= 4 else max(1, len(word) // 5)


def load_vocab():
    counts = Counter()
    for f in VL_DIR.glob("page_*NPCM*.md"):
        counts.update(re.findall(r"[a-z]+", f.read_text(encoding="utf-8").lower()))
    return {w for w, c in counts.items() if c >= VOCAB_MIN_COUNT}


def matches(cands, concepts, real_words):
    found = set()
    for concept, variants in concepts.items():
        for v in variants:
            k = tol(v)
            pool = [c for c in cands if abs(len(c) - len(v)) <= k]
            if k == 0:
                hit = v in pool
            else:
                hit = any(
                    Levenshtein.distance(v, c) <= k and (c in variants or (c not in real_words and c not in BENIGN))
                    for c in pool
                )
            if hit:
                found.add(concept)
                break
    return found


def main():
    real_words = load_vocab()
    lib = {}
    for d in glob.glob(EDITIONS):
        ed = Path(d).name[:12]
        meta = json.load(open(Path(d) / "metadata.json", encoding="utf-8"))
        for p in meta["ocrList"]:
            lib[(ed, p["sequence"])] = p["ocrContent"] or ""

    rows = []
    for f in sorted(FAST_DIR.glob("page_*.txt")):
        _, pg, ed, *_ = f.stem.split("_")
        text = f.read_text(encoding="utf-8") + "\n" + lib.get((ed, int(pg)), "")
        text = text.lower().replace("-", "").translate(str.maketrans("01", "ol"))
        tokens = re.findall(r"[a-z]+", text)
        cands = set(tokens) | {a + b for a, b in zip(tokens, tokens[1:])}
        cands = {c for c in cands if 3 <= len(c) <= 22}
        core, broad = matches(cands, CORE, real_words), matches(cands, BROAD, real_words)
        rows.append({
            "page": f.stem, "edition": ed, "seq": int(pg),
            "score": 3 * len(core) + len(broad),
            "flag": bool(core) or len(broad) >= 2,
            "core": ";".join(sorted(core)), "broad": ";".join(sorted(broad)),
        })
    rows.sort(key=lambda r: -r["score"])
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} pages scored; flagged {sum(r['flag'] for r in rows)} "
          f"(core: {sum(bool(r['core']) for r in rows)}); vocab {len(real_words)} words")


if __name__ == "__main__":
    main()
