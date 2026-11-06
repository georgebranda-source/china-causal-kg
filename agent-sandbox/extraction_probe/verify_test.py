"""Second-pass check of saved v1 claims against the rulings. Scoring is strict: the ruling's marker text must be in the quote."""
import json, re, sys, time, urllib.request
from pathlib import Path

HERE = Path(__file__).parent
sys.stdout.reconfigure(encoding="utf-8")
norm = lambda s: re.sub(r"\s+", " ", s).strip().lower()

VERIFY = """You check one causal claim taken from a 1925 newspaper. Decide whether the quote itself directly and clearly states that the cause brought about the effect.

KEEP if the quote has any of these:
- a stated reason or result (because, due to, owing to, in view of, since, as a result of, in consequence of, the cause of)
- a named cause with a causal verb (forced)
- a protest, reply, appeal or demand about the cause. No causal word is needed: "protested regarding the firing" and "appealed to the Government to abolish the tax" both count, and the thing it is about is the cause.
- an action taken against a named threat
- a reason a speaker gives to justify an action
- "had X happened, Y would have followed" about real past events
Hedges such as "it is said" are fine. "This" is fine if the quote also names what it refers to.

REJECT if any of these apply:
- sequence only: the only link is "after this", "then", "when"
- the two events are only placed side by side
- a causal verb with no cause named in the quote: "were prevented", "was compelled"
- a prediction or conditional about the future: "will probably lead to", "if these measures were adopted"
- the quote denies the link: "no connection", "nothing to do with", "not the cause of"
- the cause or effect is not actually what the quote says

reasoning comes first: name the words that link cause and effect, and say which rule applies. Then give keep as true or false."""
SCHEMA = {"type": "object", "properties": {"reasoning": {"type": "string"}, "keep": {"type": "boolean"}}, "required": ["reasoning", "keep"]}
MUST = ["due to low wages", "indian soldiers have been sent", "forced, the chairman", "co-operated with the defence",
        "cause of his death", "too heavily loaded", "exploit the local strike", "in consequence of this",
        "protested to the british consul", "most necessary", "threatening letters", "stayedores"]
SKIP = ["hesitators opened", "all chinese have left shameen", "mobbed and prevented", "compelled to supplement",
        "tung wah hospital will probably", "if these measures were adopted", "no connection whatever", "hardly operative"]


def check(q):
    msg = f"Quote: {q['quote']}\nCause: {q['cause']}\nEffect: {q['effect']}"
    body = {"model": "qwen3.5:9b-q8_0", "stream": False, "think": False, "format": SCHEMA, "keep_alive": "10m",
            "options": {"temperature": 0, "seed": 1, "num_ctx": 4096, "num_predict": 300},
            "messages": [{"role": "system", "content": VERIFY}, {"role": "user", "content": msg}]}
    req = urllib.request.Request("http://localhost:11434/api/chat", json.dumps(body).encode(), {"Content-Type": "application/json"})
    return json.loads(json.load(urllib.request.urlopen(req, timeout=120))["message"]["content"])


def score(claims):
    qs = [norm(q["quote"]) for q in claims]
    return sum(any(m in x for x in qs) for m in MUST), sum(not any(m in x for x in qs) for m in SKIP)


log = json.load(open(HERE / "rulings_test_output.json", encoding="utf-8"))
out = {}
for name in ("whole", "chunks"):
    claims = [q for a in log[name] for q in a["rel"]]
    t0 = time.time()
    for q in claims:
        q["check"] = check(q)
    kept = [q for q in claims if q["check"]["keep"]]
    a, b = score(claims); c, d = score(kept)
    print(f"=== {name}: {len(claims)} claims -> {len(kept)} kept, {(time.time() - t0) / len(claims):.1f}s per claim")
    print(f"  before check: extract {a}/{len(MUST)}, skip {b}/{len(SKIP)}, total {a + b}/20")
    print(f"  after check:  extract {c}/{len(MUST)}, skip {d}/{len(SKIP)}, total {c + d}/20")
    qs = [norm(q["quote"]) for q in kept]
    print("  missing:", [m for m in MUST if not any(m in x for x in qs)])
    print("  wrongly kept:", [m for m in SKIP if any(m in x for x in qs)])
    out[name] = claims
json.dump(out, open(HERE / "verify_test_output.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("=== chunks: all decisions")
for q in out["chunks"]:
    print(f"{'KEEP' if q['check']['keep'] else 'DROP'} {q['cause'][:44]} -> {q['effect'][:44]}\n     Q: {q['quote'][:120]}")
