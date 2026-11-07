"""Write a self-contained description of each cause and effect, for embedding.

Usage (from agent-sandbox/, after extraction and any re-check):
    .venv-kg/Scripts/python kg/normalise.py --sample 50     # random claims, leaving out the prompt's example claims
    .venv-kg/Scripts/python kg/normalise.py                 # every kept claim

Reads raw_claims.jsonl (status "kept") and the article files. Writes kg/out/normalised.jsonl, or
normalised_sample.jsonl with --sample. Original cause, effect and quote are kept beside the descriptions.
A stopped run resumes where it left off.
"""
import argparse
import hashlib
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract as x
import normalise_prompt as n

ITEM_SCHEMA = {"type": "object", "properties": {k: {"type": "string"} for k in n.FIELDS}, "required": list(n.FIELDS)}
OPTIONS = {"temperature": 0, "seed": 1, "num_ctx": 12288, "num_predict": 600}
PROMPT_HASH = hashlib.sha256(json.dumps([n.SYSTEM, n.EXAMPLES], ensure_ascii=False).encode()).hexdigest()[:12]


def claim_key(c):
    e = c["extraction"]
    return hashlib.sha256(json.dumps([c["article_id"], e["quote"], e["cause"], e["effect"]], ensure_ascii=False).encode()).hexdigest()[:16]


def message(a, e):
    return {"role": "user", "content": n.user_message(x.head_of(a), a.get("source"), a.get("dateline"), a["text"], e["quote"], e["cause"], e["effect"])}


def build_shots(claims, articles):
    shots, used = [], set()
    for article_id, words, answer in n.EXAMPLES:
        c = next(c for c in claims if c["article_id"] == article_id and words in c["extraction"]["quote"])
        used.add(claim_key(c))
        shots += [message(articles[article_id], c["extraction"]),
                  {"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)}]
    return shots, used


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int)
    args = ap.parse_args()
    articles = {a["article_id"]: a for a in x.load("articles_selected.jsonl")}
    claims = x.load("raw_claims.jsonl")
    base_articles = {a["article_id"]: a for a in x.load("articles_selected.jsonl", x.BASE)}
    shots, example_keys = build_shots(x.load("raw_claims.jsonl", x.BASE), base_articles)
    todo = [c for c in claims if c["status"] == "kept"]
    name = "normalised.jsonl"
    if args.sample:
        name = "normalised_sample.jsonl"
        pool = [c for c in todo if claim_key(c) not in example_keys]
        todo = random.Random(1).sample(pool, args.sample)
    todo.sort(key=lambda c: c["article_id"])  # same article back to back, so Ollama can reuse it
    path = x.OUT / name
    done = {r["key"] for r in x.load(name) if r["prompt_hash"] == PROMPT_HASH} if path.exists() else set()
    print(f"{len(todo)} claims, {len(done)} done, prompt {PROMPT_HASH}", flush=True)
    t0, finished, failed = time.time(), 0, []
    with open(path, "a", encoding="utf-8") as f:
        for c in todo:
            if x.STOP.exists():
                print("stop file found", flush=True)
                break
            key = claim_key(c)
            if key in done:
                continue
            e, a = c["extraction"], articles[c["article_id"]]
            try:
                answer, _ = x.chat([{"role": "system", "content": n.SYSTEM}] + shots + [message(a, e)], ITEM_SCHEMA, OPTIONS)
            except RuntimeError as err:
                failed.append(c["article_id"])
                print(f"FAILED {c['article_id']}: {err}", flush=True)
                continue
            row = {"key": key, "prompt_hash": PROMPT_HASH, "article_id": c["article_id"], "page": c["page"], "date": c["date"],
                   "headline": c["headline"], "quote": e["quote"], "cause": e["cause"], "effect": e["effect"],
                   **{k: answer[k] for k in n.FIELDS}}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            finished += 1
            if finished % 50 == 0:
                print(f"{time.strftime('%H:%M:%S')} {finished} done, {(time.time() - t0) / finished:.1f} s each", flush=True)
    print(f"finished {finished}, failed {len(failed)}: {failed}, {(time.time() - t0) / max(finished, 1):.1f} s each", flush=True)
    print("ALL DONE" if not failed else "NOT COMPLETE: rerun to continue", flush=True)


if __name__ == "__main__":
    main()
