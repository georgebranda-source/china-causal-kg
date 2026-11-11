import sys, os, re
sys.argv, ids = sys.argv[:1], sys.argv[1:]
exec(open("context.py", encoding="utf-8").read().split("W = int")[0])
N = int(os.environ.get("N", 600))
for p in ids:
    row = c[c.id.str.startswith(p)].iloc[0]; a = arts[fa[row.id]]
    print(f"=== {p} {row.date} {a['headline']} | parent {a['parent_headline']}\n  " + re.sub(r"\s+", " ", a["text"][:N]))
