"""Speaker pass: for each kept claim, who the article presents as making it (PLAN.md section 3).

One Qwen call per article that has kept claims, with the article text and its numbered claims. Same model and settings
style as v1 extraction (qwen3.5:9b-q8_0, temperature 0, seed 1, no thinking, JSON schema). Resumable: OUT/speakers.jsonl
holds one record per finished article.

Usage: .venv-kg/Scripts/python kg/perception/speaker.py [--limit N]
"""
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

sys.path.insert(0, str(C.KG))
import extract as x  # noqa: E402

C.cap_json_retries(x)

TYPES = ["PAPER", "BRITISH_OFFICIAL", "BRITISH_OTHER", "CHINESE", "CANTON_GOVT", "OTHER_FOREIGN", "UNKNOWN"]
SYSTEM = """You read an article from the China Mail, a British newspaper in Hongkong, in 1925. OCR errors are expected.
You are given the article and a numbered list of causal claims taken from it. For each claim, say who the article presents as making that claim.

How to decide:
- Look at the sentences around the quote. Words such as "said", "stated", "declared", "according to", "in his speech", "the resolution", "the telegram reads", quotation marks, or a heading such as "THE GOVERNOR'S SPEECH" mean the claim belongs to that speaker, even when the attribution is several sentences or paragraphs before the quote.
- If an article prints a speech, resolution, notice, manifesto, report or letter, every claim inside it belongs to its author, not to the paper.
- If an article reprints another newspaper ("the North-China Daily News says", "a Canton paper states"), the speaker is that newspaper.
- A letter to the Editor belongs to its writer, named as signed (a pseudonym is fine).
- Only if the paper states the claim in its own words, in news reporting or editorial comment, with no other source, is the speaker "the paper". Press agency telegrams (Reuter) with no other named source also count as "the paper".

speaker: the speaker's name or description as printed, short, such as "the Governor", "Sir Shouson Chow", "the Strike Committee", "North-China Daily News", or "the paper".

speaker_type, exactly one of:
PAPER: the China Mail's own reporting or editorial, and unattributed agency telegrams.
BRITISH_OFFICIAL: British or Hongkong Government officials, governors, ministers, Members of Parliament, consuls, police, British naval or military officers.
BRITISH_OTHER: British residents, merchants, firms, public meetings, chambers of commerce, British clergy, British newspapers in China or Britain.
CHINESE: Chinese individuals, merchants, guilds, unions, strikers, students, Chinese newspapers, and Chinese officials of Peking or other provinces.
CANTON_GOVT: the Canton Government and its officials, the Kuomintang, the Strike Committee, Whampoa cadets.
OTHER_FOREIGN: non-British foreigners, their governments, consuls, residents and newspapers.
UNKNOWN: the article does not make it clear, including letter writers whose nationality is not clear.

Return one item per claim, in the same order, with its number."""
ITEM = {"type": "object", "properties": {"n": {"type": "integer"}, "reasoning": {"type": "string"}, "speaker": {"type": "string"},
                                         "speaker_type": {"type": "string", "enum": TYPES}},
        "required": ["n", "reasoning", "speaker", "speaker_type"]}
SCHEMA = {"type": "object", "properties": {"claims": {"type": "array", "items": ITEM}}, "required": ["claims"]}
OPTIONS = {"temperature": 0, "seed": 1, "num_ctx": 12288, "num_predict": 2500}
PROMPT_HASH = hashlib.sha256(json.dumps([SYSTEM, SCHEMA], ensure_ascii=False).encode()).hexdigest()[:12]


def message(a, claims):
    lines = [f"{i}. Quote: {c['extraction']['quote']}\n   Cause: {c['extraction']['cause']}\n   Effect: {c['extraction']['effect']}"
             for i, c in enumerate(claims, 1)]
    head = x.head_of(a) or "(none)"
    return {"role": "user", "content": f"Headline: {head}\n\nText:\n{a['text']}\n\nClaims:\n" + "\n".join(lines)}


def main():
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    articles = {a["article_id"]: a for a in C.load_jsonl(C.OUT / "articles_selected.jsonl")}
    by_art = {}
    for c in C.load_jsonl(C.OUT / "raw_claims.jsonl"):
        if c["status"] == "kept":
            by_art.setdefault(c["article_id"], []).append(c)
    path = C.OUT / "speakers.jsonl"
    done = {r["article_id"] for r in C.load_jsonl(path) if r["prompt_hash"] == PROMPT_HASH}
    todo = [k for k in sorted(by_art) if k not in done][:limit]
    print(f"{len(by_art)} articles with claims, {len(done)} done, {len(todo)} to run, prompt {PROMPT_HASH}", flush=True)
    failed = []
    with open(path, "a", encoding="utf-8") as f:
        for i, aid in enumerate(todo, 1):
            if C.STOP.exists():
                print("stop file found", flush=True)
                break
            claims, t0 = by_art[aid], time.time()
            try:
                ans, _ = x.chat([{"role": "system", "content": SYSTEM}, message(articles[aid], claims)], SCHEMA, OPTIONS)
                items = {it["n"]: it for it in ans["claims"]}
            except Exception as e:
                failed.append(aid)
                print(f"FAILED {aid}: {e}", flush=True)
                continue
            out = []
            for n, c in enumerate(claims, 1):
                it = items.get(n) or {"speaker": "", "speaker_type": "UNKNOWN", "reasoning": "MISSING from model output"}
                e = c["extraction"]
                out.append({"quote": e["quote"], "cause": e["cause"], "effect": e["effect"], "speaker": it["speaker"],
                            "speaker_type": it["speaker_type"], "reasoning": it["reasoning"], "missing": n not in items})
            f.write(json.dumps({"article_id": aid, "prompt_hash": PROMPT_HASH, "seconds": round(time.time() - t0, 1),
                                "claims": out}, ensure_ascii=False) + "\n")
            f.flush()
            if i % 25 == 0:
                print(f"{time.strftime('%H:%M:%S')} {i}/{len(todo)}", flush=True)
    print(f"failed {len(failed)}: {failed}", flush=True)
    print("ALL DONE" if not failed else "NOT COMPLETE: rerun to continue", flush=True)


if __name__ == "__main__":
    main()
