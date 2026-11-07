"""Build coder input from the frozen v1 snapshot. Read-only on all source data. Six chronological batches kept whole by article, plus 120 claims double coded."""
import csv, glob, json, random, re
rd = lambda p: list(csv.DictReader(open(p, encoding="utf-8")))
B = "../explanations/snapshot_v1_c63a9cfa/event-035/"
cl = rd(B + "claims.csv"); fa = {r["claim"]: r["article"] for r in rd(B + "from_article.csv")}; art = {r["id"]: r for r in rd(B + "articles.csv")}
text = {}
for p in ["../../out/articles_all.jsonl"] + glob.glob("../../out/batches/*/*.jsonl"):
    for l in open(p, encoding="utf-8"):
        try:
            d = json.loads(l)
            if "article_id" in d and "text" in d: text.setdefault(d["article_id"], d["text"])
        except ValueError: pass
n = lambda s: re.sub(r"\s+", " ", s or "")
def row(c):
    a = fa[c["id"]]; t = n(text.get(a, "")); k = t.find(n(c["quote"])[:60])
    return {"id": c["id"], "date": c["date"], "page": a.split("_")[1], "headline": art[a]["headline"][:90], "cause": c["cause"], "effect": c["effect"], "quote": c["quote"],
            "article_start": t[:130], "before_quote": t[max(0, k - 260):k] if k >= 0 else "", "_a": a}
rows = [row(c) for c in sorted(cl, key=lambda c: (c["date"], fa[c["id"]]))]
print("no text", sum(1 for r in rows if not r["article_start"]))
size = len(rows) / 6; batches = [[] for _ in range(6)]; i = 0
for r in rows:
    if batches[i] and len(batches[i]) >= size and r["_a"] != batches[i][-1]["_a"] and i < 5: i += 1
    batches[i].append(r)
rng = random.Random(1925)
extra = [[] for _ in range(6)]; overlap = {}
for b in range(6):
    arts = sorted({r["_a"] for r in batches[b]}); rng.shuffle(arts); got = []
    for a in arts:
        if len(got) >= 20: break
        got += [r for r in batches[b] if r["_a"] == a]
    extra[(b + 3) % 6] += got
    for r in got: overlap[r["id"]] = (b, (b + 3) % 6)
for b in range(6):
    allr = batches[b] + extra[b]; rng.shuffle(allr)
    with open(f"tags/input/batch_{b}.jsonl", "w", encoding="utf-8") as f:
        for r in allr:
            f.write(json.dumps({k: v for k, v in r.items() if k != "_a"}, ensure_ascii=False) + "\n")
    print(b, len(batches[b]), len(extra[b]), batches[b][0]["date"], batches[b][-1]["date"])
json.dump(overlap, open("tags/overlap.json", "w")); print("double coded", len(overlap))
