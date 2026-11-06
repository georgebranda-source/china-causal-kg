"""Extract causal claims from the selected articles: full article, then a check on each claim.

Usage (from agent-sandbox/, after kg/build_corpus.py):
    .venv-kg/Scripts/python kg/extract.py [--limit N]

kg/out/progress.jsonl holds one complete record per finished article, so a stopped run resumes where it left off.
The other files are rebuilt from it at the end of every run:
    relations.jsonl    claims that passed every step: page, date, headline, extraction
    raw_claims.jsonl   every claim with its article_id and outcome, including those the check dropped
    rejected.jsonl     claims dropped by the quote check, the cause/effect check or the second-pass check
    run_manifest.json  model, prompts, options, counts
"""
import argparse
import ast
import hashlib
import json
import re
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

from rapidfuzz import fuzz

KG = Path(__file__).resolve().parent
PROBE = KG.parent / "extraction_probe"
OUT = KG / "out"
sys.path.insert(0, str(PROBE))
from prompt_v1 import EXAMPLES, SYSTEM

sys.stdout.reconfigure(encoding="utf-8")
MODEL, DIGEST, URL = "qwen3.5:9b-q8_0", "a8ee95bc3592", "http://localhost:11434/api/chat"
FIELDS = ("reasoning", "quote", "cause", "effect")
ITEM = {"type": "object", "properties": {k: {"type": "string"} for k in FIELDS}, "required": list(FIELDS)}
EXTRACT_SCHEMA = {"type": "object", "properties": {"relations": {"type": "array", "items": ITEM}}, "required": ["relations"]}
EXTRACT_OPTIONS = {"temperature": 0, "seed": 1, "num_ctx": 12288, "num_predict": 3000}
CHECK_OPTIONS = {"temperature": 0, "seed": 1, "num_ctx": 4096, "num_predict": 300}


def source_constant(name):
    for node in ast.parse((PROBE / "verify_test.py").read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == name:
            return ast.literal_eval(node.value)
    raise KeyError(name)


VERIFY, CHECK_SCHEMA = source_constant("VERIFY"), source_constant("SCHEMA")
PROMPT_HASH = hashlib.sha256(json.dumps([SYSTEM, EXAMPLES, VERIFY], ensure_ascii=False).encode()).hexdigest()[:12]


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def load(name):
    return [json.loads(line) for line in open(OUT / name, encoding="utf-8")]


def user(headline, text):
    return {"role": "user", "content": f"Headline: {headline}\n\nText:\n{text}"}


def head_of(a):
    return a["headline"] or a["parent_headline"]


def build_shots(articles):
    shots = []
    for pattern, answer in EXAMPLES:
        a = next(r for r in articles if r["headline"] and re.search(pattern, r["headline"]))
        for x in answer:
            assert norm(x["quote"]) in norm(a["text"]), x["quote"]
        shots += [user(a["headline"], a["text"]),
                  {"role": "assistant", "content": json.dumps({"relations": answer}, ensure_ascii=False)}]
    return shots


def chat(messages, schema, options):
    body = {"model": MODEL, "stream": False, "think": False, "format": schema, "keep_alive": "30m",
            "options": options, "messages": messages}
    last = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
            reply = json.load(urllib.request.urlopen(req, timeout=600))
            return json.loads(reply["message"]["content"]), reply.get("done_reason")
        except json.JSONDecodeError as e:  # usually output cut off at the token limit
            last = e
            body["options"] = dict(options, num_predict=options["num_predict"] * 2)
        except OSError as e:
            last = e
            time.sleep(15 * (attempt + 1))
    raise RuntimeError(f"model call failed: {last}")


def fix_quote(quote, text):
    """Return (quote from the article, how it matched), or (None, 'not_found')."""
    q = norm(quote)
    if q and q in text:
        return q, "verbatim"
    if q:
        hit = fuzz.partial_ratio_alignment(q, text)
        if hit is not None and hit.score >= 95:
            return text[hit.dest_start:hit.dest_end], "fuzzy"
    return None, "not_found"


def process(a, shots):
    text = norm(a["text"])
    head = head_of(a) or "(none)"
    answer, _ = chat([{"role": "system", "content": SYSTEM}] + shots + [user(head, a["text"])], EXTRACT_SCHEMA, EXTRACT_OPTIONS)
    claims, seen = [], set()
    for c in answer["relations"]:
        c = {k: c[k] for k in FIELDS}
        quote, match = fix_quote(c["quote"], text)
        key = (quote, norm(c["cause"]).lower(), norm(c["effect"]).lower())
        status, check = "kept", None
        if quote is None:
            status = "quote_not_found"
        elif not key[1] or not key[2] or key[1] == key[2]:
            status = "bad_cause_or_effect"
        elif key in seen:
            status = "duplicate"
        else:
            seen.add(key)
            c["quote"] = quote
            msg = f"Quote: {c['quote']}\nCause: {c['cause']}\nEffect: {c['effect']}"
            check, _ = chat([{"role": "system", "content": VERIFY}, {"role": "user", "content": msg}], CHECK_SCHEMA, CHECK_OPTIONS)
            if not check["keep"]:
                status = "dropped_by_check"
        claims.append({"extraction": c, "quote_match": match, "status": status, "check": check})
    return claims


def finalize(articles, records):
    by_id = {a["article_id"]: a for a in articles}
    counts = Counter()
    with open(OUT / "relations.jsonl", "w", encoding="utf-8") as rel, \
            open(OUT / "raw_claims.jsonl", "w", encoding="utf-8") as raw, \
            open(OUT / "rejected.jsonl", "w", encoding="utf-8") as rej:
        for rec in records:
            a = by_id[rec["article_id"]]
            base = {"page": a["page"], "date": a["date"], "headline": head_of(a)}
            for c in rec["claims"]:
                counts[c["status"]] += 1
                full = {"article_id": rec["article_id"], **base, **c}
                raw.write(json.dumps(full, ensure_ascii=False) + "\n")
                if c["status"] == "kept":
                    rel.write(json.dumps({**base, "extraction": c["extraction"]}, ensure_ascii=False) + "\n")
                else:
                    rej.write(json.dumps(full, ensure_ascii=False) + "\n")
    manifest = {"model": MODEL, "digest": DIGEST, "prompt_hash": PROMPT_HASH, "extract_options": EXTRACT_OPTIONS,
                "check_options": CHECK_OPTIONS, "setup": "full article + check", "articles_selected": len(articles),
                "articles_done": len(records), "articles_with_claims": sum(bool(r["claims"]) for r in records),
                "claims": dict(counts), "seconds_total": round(sum(r["seconds"] for r in records))}
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, help="stop after N articles in this run")
    args = ap.parse_args()
    articles = load("articles_selected.jsonl")
    shots = build_shots(load("articles_all.jsonl"))
    path = OUT / "progress.jsonl"
    records = [r for r in (load("progress.jsonl") if path.exists() else []) if r["prompt_hash"] == PROMPT_HASH]
    done = {r["article_id"] for r in records}
    todo = [a for a in articles if a["article_id"] not in done][:args.limit]
    print(f"{len(articles)} selected, {len(done)} done, {len(todo)} to run, prompts {PROMPT_HASH}", flush=True)
    failed = []
    with open(path, "a", encoding="utf-8") as f:
        for n, a in enumerate(todo, 1):
            t0 = time.time()
            try:
                claims = process(a, shots)
            except Exception as e:
                failed.append(a["article_id"])
                print(f"FAILED {a['article_id']}: {e}", flush=True)
                continue
            rec = {"article_id": a["article_id"], "prompt_hash": PROMPT_HASH, "seconds": round(time.time() - t0, 1), "claims": claims}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            records.append(rec)
            if n % 25 == 0 or n == len(todo):
                kept = sum(c["status"] == "kept" for r in records for c in r["claims"])
                print(f"{time.strftime('%H:%M:%S')} {len(records)}/{len(articles)} articles, {kept} claims kept", flush=True)
    print(json.dumps(finalize(articles, records), indent=2))
    print("failed articles:", failed)
    print("ALL DONE" if len(records) == len(articles) else "NOT COMPLETE: rerun to continue", flush=True)


if __name__ == "__main__":
    main()
