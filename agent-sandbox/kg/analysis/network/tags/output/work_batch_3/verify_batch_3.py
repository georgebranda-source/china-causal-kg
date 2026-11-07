import collections, csv, filecmp, hashlib, json, re, shutil
net = "C:/Users/georg/documents/projects/china-causal-kg/agent-sandbox/kg/analysis/network/"
out = net + "tags/output/batch_3.csv"
work = net + "tags/output/work_batch_3/batch_3_staged.csv"
mine = ("C:/Users/georg/AppData/Local/Temp/claude/adc478a5405a97a5/"
        "b246f2ff-742f-4b11-868c-8d9354e6424d/scratchpad/batch3_private_coder/batch_3_final.csv")

print("output identical to the file I authored:", filecmp.cmp(out, mine, shallow=False))
shutil.copyfile(mine, work)
shutil.copyfile(work, out)
print("output identical to staged copy:", filecmp.cmp(out, work, shallow=False))
print("sha256", hashlib.sha256(open(out, "rb").read()).hexdigest())

cb = open(net + "CODEBOOK.md", encoding="utf-8").read()
def sect(h):
    m = re.search(r"^## " + h + r"\n(.*?)(?=^## |\Z)", cb, re.S | re.M)
    return set(re.findall(r"`([A-Z_]+)`", m.group(1)))
valid = {"relevance": sect("relevance"), "cause_type": sect("cause_type, effect_type"),
         "cause_actor": sect("cause_actor, effect_actor"), "effect_mode": sect("effect_mode"),
         "cause_place": sect("cause_place, effect_place"), "voice": sect("voice"), "stance": sect("stance")}
valid["effect_type"] = valid["cause_type"]
valid["effect_actor"] = valid["cause_actor"]
valid["effect_place"] = valid["cause_place"]
valid["confidence"] = {"high", "low"}
print({k: len(v) for k, v in valid.items()})

ids = [json.loads(l)["id"] for l in open(net + "tags/input/batch_3.jsonl", encoding="utf-8") if l.strip()]
rows = list(csv.DictReader(open(out, encoding="utf-8", newline="")))
got = [r["id"] for r in rows]
print("input", len(ids), "rows", len(rows), "unique", len(set(got)))
print("missing", sorted(set(ids) - set(got)), "extra", sorted(set(got) - set(ids)))
print("dupes", [k for k, v in collections.Counter(got).items() if v > 1])
print("invalid", [(r["id"], k, r[k]) for r in rows for k in valid if r[k] not in valid[k]])
print("cols", list(rows[0].keys()))
print(collections.Counter(r["confidence"] for r in rows))
