"""Rebuild articles for every May-July 1925 page with VL OCR and select those for extraction.

Selection (PLAN.md section 2, as approved): a non-ad article is selected if it contains a strike CORE term (strike_screen.py)
or a perception term (perception_screen.py PERCEPTION). Exact token match on the clean VL text, also with
hyphens removed ("anti-foreign" -> "antiforeign"). Letters are kept, with is_letter set by the v1 rule
(headline matches CORRESPONDENCE or "to the editor"). Dateline matching is the widened one from build_batch.py.

Writes OUT/articles_selected.jsonl, OUT/articles_all.jsonl, OUT/corpus_report.json.
Usage: .venv-kg/Scripts/python kg/perception/build.py [--pages N]   (--pages: first N pages only, for the test)
"""
import ast
import json
import re
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import common as C  # noqa: E402

sys.path.insert(0, str(C.SANDBOX))
import build_articles as b  # noqa: E402
import perception_screen as PS  # noqa: E402

(C.OUT / "build").mkdir(exist_ok=True)
b.OUT_DIR = C.OUT / "build"
b.render_overlay = lambda *a, **k: None
b.print = lambda *a, **k: None
b.DATELINE_RE = re.compile(r"^[A-Z][A-Za-z'.\- ]{2,30},\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Jue|J[uü]ly|Tura)[a-z]*\.?\s*\d{0,2}", re.I)

terms = {}
for node in ast.parse((C.SANDBOX / "strike_screen.py").read_text(encoding="utf-8")).body:
    if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "CORE":
        terms[node.targets[0].id] = ast.literal_eval(node.value)
CORE_TERMS = {t for g in terms.values() for v in g.values() for t in v}
PERC_TERMS = {t for v in PS.PERCEPTION.values() for t in v}
LETTER_RE = re.compile(r"CORRESPONDENCE|to the editor", re.I)


def heads(r):
    return " ".join(x for x in (r["headline"], r["parent_headline"]) if x)


def main():
    pages = C.corpus_pages()
    if "--pages" in sys.argv:
        pages = pages[:int(sys.argv[sys.argv.index("--pages") + 1])]
    if "--only" in sys.argv:  # comma-separated page names, for the test
        pages = sys.argv[sys.argv.index("--only") + 1].split(",")
    articles, failed = [], []
    for p in pages:
        try:
            articles += b.process(p)
        except Exception as e:
            failed.append({"page": p, "error": f"{type(e).__name__}: {e}"})
    news = [r for r in articles if not r["is_ad"]]
    sel = []
    for r in news:
        r["article_id"] = f"{r['page']}#{r['article']}"
        text = (heads(r) + " " + r["text"]).lower()
        toks = set(re.findall(r"[a-z]+", text)) | set(re.findall(r"[a-z]+", text.replace("-", "")))
        r["core_term"], r["perception_term"] = bool(toks & CORE_TERMS), bool(toks & PERC_TERMS)
        r["is_letter"] = bool(LETTER_RE.search(heads(r)))
        if r["core_term"] or r["perception_term"]:
            sel.append(r)
    for name, rows in (("articles_all.jsonl", articles), ("articles_selected.jsonl", sel)):
        with open(C.OUT / name, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    report = {"pages": len(pages), "failed": failed, "news": len(news), "selected": len(sel),
              "core_term_only": sum(r["core_term"] and not r["perception_term"] for r in sel),
              "perception_term_only": sum(r["perception_term"] and not r["core_term"] for r in sel),
              "letters": sum(r["is_letter"] for r in sel), "words": sum(len(r["text"].split()) for r in sel),
              "by_month": {m: sum(r["page"].split("NPCM")[1][:6] == m for r in sel) for m in C.MONTHS + C.EXTRA_MONTHS}}
    (C.OUT / "corpus_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
