"""Remove claims repeated only because a printed page was filmed twice.

Only the pairs in PAIRS are compared, so items the paper itself printed more than once are left alone. Each claim on the fainter image
can cancel one claim on the clearer image, using the agreed merge rule: overlapping quote (partial ratio >= 90) and similar cause and
effect (token set >= 60). Claims found on only one image stay. The source files are not changed.
"""
from rapidfuzz import fuzz

PAIRS = [("page_006_NPCM19250727_01_0006", "page_005_NPCM19250727_01_0005"),  # (clearer image, fainter image), both printed page 5
         ("page_001_NPCM19251019_01_0001", "page_002_NPCM19251019_01_0002"),  # both printed page 1
         ("page_006_NPCM19251015_01_0006", "page_007_NPCM19251015_01_0007"),  # both printed page 6
         ("page_001_NPCM19250903_01_0001", "page_001_NPCM19250904_01_0001"),  # 3 September front page, second film filed under 4 September
         ("page_007_NPCM19260209_01_0007", "page_009_NPCM19260209_01_0009"),  # both printed page 7; equally legible, the image in page order kept
         ("page_001_NPCM19260630_01_0001", "page_003_NPCM19260630_01_0003")]  # both the front page; equally legible, the image in page order kept
REDATE = {"page_001_NPCM19250904_01_0001": "1925-09-03"}  # claims left on a misfiled image take the date printed on the page


def same_claim(a, b):
    return (fuzz.partial_ratio(a["quote"], b["quote"]) >= 90 and fuzz.token_set_ratio(a["cause"], b["cause"]) >= 60
            and fuzz.token_set_ratio(a["effect"], b["effect"]) >= 60)


def remove_repeats(rows):
    """Return (rows to keep, list of (removed row, matching row))."""
    removed = []
    for clear, faint in PAIRS:
        free = [r for r in rows if r["article_id"].split("#")[0] == clear]
        for r in (r for r in rows if r["article_id"].split("#")[0] == faint):
            match = next((c for c in free if same_claim(r, c)), None)
            if match:
                free.remove(match)
                removed.append((r, match))
    gone = {id(r) for r, _ in removed}
    kept = [r for r in rows if id(r) not in gone]
    return [{**r, "date": REDATE.get(r["article_id"].split("#")[0], r["date"])} for r in kept], removed
