"""Print article context for claims: python context.py <id-prefix> ..."""
import json, sys, re
import pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
c = pd.read_csv(ROOT / "analysis/temporal/snapshot_v1_ceb6e08a/event-035/claims.csv")
fa = pd.read_csv(ROOT / "analysis/temporal/snapshot_v1_ceb6e08a/event-035/from_article.csv").set_index("claim").article
arts = {}
for f in [ROOT / "out/articles_all.jsonl", *sorted((ROOT / "out/batches").glob("*/articles_selected.jsonl"))]:
  for line in open(f, encoding="utf-8"):
    r = json.loads(line)
    arts[r.get("article_id") or f'{r["page"]}#{r["article"]}'] = r
W = int(__import__("os").environ.get("W", 500))
for p in sys.argv[1:]:
    row = c[c.id.str.startswith(p)].iloc[0]
    a = arts.get(fa[row.id])
    print(f"=== {row.id[:7]} {row.date} | {row.cause} => {row.effect}")
    if a is None:
        print("  (article not found)"); continue
    print(f"  HEADLINE: {a['headline']} | parent: {a['parent_headline']} | source: {a['source']} | dateline: {a['dateline']} | len {len(a['text'])}")
    t = a["text"]; q = str(row.quote)[:40]
    i = t.find(q[:25])
    s = t[:W] if i < 0 else t[max(0, i - W):i + W]
    print("  " + re.sub(r"\s+", " ", s))
