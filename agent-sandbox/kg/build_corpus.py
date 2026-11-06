"""Build the article files for extraction, without changing build_articles.py's own outputs.

Writes kg/out/:
    articles_all.jsonl        news units from every June-July page with VL text (worked examples are looked up here)
    articles_selected.jsonl   news units on pages scoring >= 8 with a CORE or BROAD term, letters removed
    corpus_report.json        counts, and pages that could not be processed
"""
import ast
import csv
import glob
import json
import os
import re
import sys
from pathlib import Path

KG = Path(__file__).resolve().parent
SANDBOX = KG.parent
sys.path.insert(0, str(SANDBOX))
import build_articles as b

OUT = KG / "out"
OUT.mkdir(exist_ok=True)
(OUT / "articles_build").mkdir(exist_ok=True)
b.OUT_DIR = OUT / "articles_build"
b.render_overlay = lambda *a, **k: None
b.print = lambda *a, **k: None

CUTOFF = 8
LETTER_RE = re.compile(r"CORRESPONDENCE|to the editor", re.I)

terms = {}
for node in ast.parse((SANDBOX / "strike_screen.py").read_text(encoding="utf-8")).body:
    if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") in ("CORE", "BROAD"):
        terms[node.targets[0].id] = ast.literal_eval(node.value)
TERMS = {t for group in terms.values() for variants in group.values() for t in variants}

scores = {r["page"]: int(r["score"]) for r in csv.DictReader(open(SANDBOX / "strike_screen.csv", encoding="utf-8"))}
pages = sorted(os.path.basename(p)[:-9] for p in glob.glob(str(SANDBOX / "ocr_vl_out" / "page_*NPCM19250[67]*_res.json")))

rows, failed = [], []
for page in pages:
    try:
        rows += b.process(page)
    except Exception as e:
        failed.append({"page": page, "score": scores.get(page), "error": f"{type(e).__name__}: {e}"})

news = [r for r in rows if not r["is_ad"]]
for r in news:
    r["article_id"] = f"{r['page']}#{r['article']}"


def all_text(r):
    return " ".join(x for x in (r["headline"], r["parent_headline"], r["text"]) if x)


on_pages = [r for r in news if scores.get(r["page"], 0) >= CUTOFF]
with_term = [r for r in on_pages if set(re.findall(r"[a-z]+", all_text(r).lower())) & TERMS]
letters = [r for r in with_term if LETTER_RE.search(" ".join(x for x in (r["headline"], r["parent_headline"]) if x))]
letter_ids = {r["article_id"] for r in letters}
selected = [r for r in with_term if r["article_id"] not in letter_ids]

for name, data in (("articles_all.jsonl", news), ("articles_selected.jsonl", selected)):
    with open(OUT / name, "w", encoding="utf-8") as f:
        for r in data:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

report = {"pages_with_vl": len(pages), "pages_failed": failed, "pages_score_8": sum(s >= CUTOFF for s in scores.values()),
          "pages_score_8_built": len({r["page"] for r in on_pages}), "news_on_those_pages": len(on_pages),
          "with_term": len(with_term), "letters_removed": len(letters), "selected": len(selected),
          "selected_words": sum(len(r["text"].split()) for r in selected)}
(OUT / "corpus_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
