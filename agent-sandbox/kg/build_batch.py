"""Select articles for a batch of months. Usage: python kg/build_batch.py 1925-08-09 192508 192509

Same rules as kg/build_corpus.py: pages scoring >= 8 (strike_screen_batch.csv), CORE or BROAD term, letters removed. Dateline matching
is widened to all months here only; June-July stays frozen. Writes kg/out/batches/<name>/articles_selected.jsonl and corpus_report.json.
"""
import ast
import csv
import json
import re
import sys
from pathlib import Path

KG = Path(__file__).resolve().parent
SANDBOX = KG.parent
sys.path.insert(0, str(SANDBOX))
import build_articles as b

name, months = sys.argv[1], sys.argv[2:]
OUT = KG / "out" / "batches" / name
(OUT / "build").mkdir(parents=True, exist_ok=True)
b.OUT_DIR = OUT / "build"
b.render_overlay = lambda *a, **k: None
b.print = lambda *a, **k: None
b.DATELINE_RE = re.compile(r"^[A-Z][A-Za-z'.\- ]{2,30},\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Jue|J[uü]ly|Tura)[a-z]*\.?\s*\d{0,2}", re.I)

terms = {}
for node in ast.parse((SANDBOX / "strike_screen.py").read_text(encoding="utf-8")).body:
    if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") in ("CORE", "BROAD"):
        terms[node.targets[0].id] = ast.literal_eval(node.value)
TERMS = {t for g in terms.values() for v in g.values() for t in v}

rows = list(csv.DictReader(open(SANDBOX / "strike_screen_batch.csv", encoding="utf-8")))
pages = sorted(r["page"] for r in rows if int(r["score"]) >= 8 and re.search(r"NPCM(\d{6})", r["page"])[1] in months)
articles, failed = [], []
for p in pages:
    try:
        articles += b.process(p)
    except Exception as e:
        failed.append({"page": p, "error": f"{type(e).__name__}: {e}"})
news = [r for r in articles if not r["is_ad"]]
for r in news:
    r["article_id"] = f"{r['page']}#{r['article']}"


def heads(r):
    return " ".join(x for x in (r["headline"], r["parent_headline"]) if x)


term = [r for r in news if set(re.findall(r"[a-z]+", (heads(r) + " " + r["text"]).lower())) & TERMS]
selected = [r for r in term if not re.search(r"CORRESPONDENCE|to the editor", heads(r), re.I)]
with open(OUT / "articles_selected.jsonl", "w", encoding="utf-8") as f:
    for r in selected:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
report = {"pages": len(pages), "failed": failed, "news": len(news), "with_term": len(term), "selected": len(selected),
          "words": sum(len(r["text"].split()) for r in selected), "datelines": sum(bool(r["dateline"]) for r in selected),
          "sources": sum(bool(r["source"]) for r in selected)}
(OUT / "corpus_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report))
