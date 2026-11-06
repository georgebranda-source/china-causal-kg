"""Test the v1 prompt against the user's 20 rulings. Usage: python rulings_test.py <folder holding articles_probe/rows.json>"""
import json, re, sys, time, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from prompt_v1 import SYSTEM, EXAMPLES

S = Path(sys.argv[1])
sys.stdout.reconfigure(encoding="utf-8")
news = [r for r in json.load(open(S / "articles_probe" / "rows.json", encoding="utf-8")) if not r["is_ad"]]
norm = lambda s: re.sub(r"\s+", " ", s).strip()

# (expected, marker text, date of the article the ruling came from)
CASES = [
    (True, "due to low wages", "1925-06-16"), (True, "Indian soldiers have been sent", "1925-06-30"),
    (True, "forced, the Chairman", "1925-06-02"), (True, "co-operated with the defence", "1925-06-16"),
    (True, "cause of his death beyond", "1925-07-06"), (True, "too heavily loaded", "1925-06-20"),
    (True, "exploit the local strike", "1925-07-10"), (True, "In consequence of this and in order", "1925-07-09"),
    (True, "has protested to the British Consul", "1925-06-16"), (True, "most necessary in view", "1925-06-16"),
    (True, "threatening letters", "1925-07-03"), (True, "stayedores", "1925-07-03"),
    (False, "hesitators opened", "1925-06-27"), (False, "all Chinese have left Shameen", "1925-06-30"),
    (False, "mobbed and prevented", "1925-06-12"), (False, "compelled to supplement", "1925-06-23"),
    (False, "Tung Wah hospital will probably", "1925-06-27"), (False, "If these measures were adopted", "1925-07-10"),
    (False, "no connection whatever", "1925-07-06"), (False, "hardly operative", "1925-06-12"),
]
item = {"type": "object", "properties": {k: {"type": "string"} for k in ("reasoning", "quote", "cause", "effect")},
        "required": ["reasoning", "quote", "cause", "effect"]}
SCHEMA = {"type": "object", "properties": {"relations": {"type": "array", "items": item}}, "required": ["relations"]}


def user(h, t):
    return {"role": "user", "content": f"Headline: {h}\n\nText:\n{t}"}


SHOTS = []
for pat, ans in EXAMPLES:
    a = next(r for r in news if r["headline"] and re.search(pat, r["headline"]))
    for x in ans:
        assert norm(x["quote"]) in norm(a["text"]), x["quote"]
    SHOTS += [user(a["headline"], a["text"]),
              {"role": "assistant", "content": json.dumps({"relations": ans}, ensure_ascii=False)}]


def chat(h, t):
    body = {"model": "qwen3.5:9b-q8_0", "stream": False, "think": False, "format": SCHEMA, "keep_alive": "10m",
            "options": {"temperature": 0, "seed": 1, "num_ctx": 12288, "num_predict": 3000},
            "messages": [{"role": "system", "content": SYSTEM}] + SHOTS + [user(h, t)]}
    req = urllib.request.Request("http://localhost:11434/api/chat", json.dumps(body).encode(), {"Content-Type": "application/json"})
    x = json.load(urllib.request.urlopen(req, timeout=300))
    return json.loads(x["message"]["content"])["relations"]


def chunks(t, n=150):
    units = []
    for p in t.split("\n\n"):
        units += re.split(r"(?<=[.!?])\s+", p) if len(p.split()) > n else [p]
    out, cur = [], []
    for u in units:
        if cur and sum(len(c.split()) for c in cur) + len(u.split()) > n:
            out.append(" ".join(cur)); cur = []
        cur.append(u)
    return out + ([" ".join(cur)] if cur else [])


arts = {}
for exp, mark, date in CASES:
    a = next(r for r in news if r["date"] == date and mark in norm(r["text"]))
    arts[(a["page"], a["article"])] = a


def overlaps(text, mark, quote):
    """Does the quote cover the sentence holding the marker?"""
    i = text.find(mark); q = text.find(quote)
    if q < 0:
        return mark[:12].lower() in quote.lower()
    s = max(text.rfind(". ", 0, i), 0); e = text.find(". ", i); e = len(text) if e < 0 else e
    return min(q + len(quote), e) - max(q, s) > 0


log = {}
for name, split in (("whole", False), ("chunks", True)):
    t0 = time.time(); got = {}
    for k, a in arts.items():
        h = a["headline"] or "(none)"
        got[k] = [q for c in (chunks(a["text"]) if split else [a["text"]]) for q in chat(h, c)]
    dt = time.time() - t0; ok = 0
    print(f"=== {name}: {dt:.0f}s for {len(arts)} articles, {sum(map(len, got.values()))} claims, "
          f"verbatim {sum(norm(q['quote']) in norm(arts[k]['text']) for k, v in got.items() for q in v)}")
    for exp, mark, date in CASES:
        k, a = next((k, a) for k, a in arts.items() if a["date"] == date and mark in norm(a["text"]))
        hit = [q for q in got[k] if overlaps(norm(a["text"]), mark, norm(q["quote"]))]
        ok += bool(hit) == exp
        print(f"  {'PASS' if bool(hit) == exp else 'FAIL'} {'extract' if exp else 'skip   '} {mark[:36]:36} " +
              (f"{hit[0]['cause'][:40]} -> {hit[0]['effect'][:40]}" if hit else ""))
    print(f"  score {ok}/{len(CASES)}", flush=True)
    log[name] = [dict(head=arts[k]["headline"], rel=v) for k, v in got.items()]
json.dump(log, open(Path(__file__).parent / "rulings_test_output.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
