"""Embed the unique cause and effect descriptions.

Usage (from agent-sandbox/, after kg/normalise.py):  .venv-kg/Scripts/python kg/embed.py

Writes to kg/out/: embed_texts.json, and one unit-length matrix per setup:
    embed_qwen_instruct.npy   qwen3-embedding:8b with the instruction
    embed_qwen_plain.npy      qwen3-embedding:8b without it
    embed_bge.npy             bge-small-en-v1.5, for comparison
"""
import json
import time
import urllib.request
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent / "out"
MODEL = "qwen3-embedding:8b"
INSTRUCTION = ("Represent this event from a 1925 Hongkong newspaper so that descriptions of the same event are close, "
               "and different events are far apart, even if they share a topic.")


def ollama_embed(texts, batch=32):
    vectors = []
    for i in range(0, len(texts), batch):
        body = {"model": MODEL, "input": texts[i:i + batch], "keep_alive": "10m"}
        req = urllib.request.Request("http://localhost:11434/api/embed", json.dumps(body).encode(), {"Content-Type": "application/json"})
        vectors += json.load(urllib.request.urlopen(req, timeout=600))["embeddings"]
    return np.array(vectors, dtype=np.float32)


def unit(m):
    return m / np.linalg.norm(m, axis=1, keepdims=True)


rows = [json.loads(line) for line in open(OUT / "normalised.jsonl", encoding="utf-8")]
texts = sorted({r[k] for r in rows for k in ("cause_description", "effect_description")})
(OUT / "embed_texts.json").write_text(json.dumps(texts, ensure_ascii=False, indent=0), encoding="utf-8")
print(len(texts), "unique descriptions", flush=True)

for name, inputs in (("qwen_instruct", [f"Instruct: {INSTRUCTION}\nQuery:{t}" for t in texts]), ("qwen_plain", texts)):
    t0 = time.time()
    m = unit(ollama_embed(inputs))
    np.save(OUT / f"embed_{name}.npy", m)
    print(name, m.shape, f"{time.time() - t0:.0f} s", flush=True)

import truststore
truststore.inject_into_ssl()
from fastembed import TextEmbedding

t0 = time.time()
m = unit(np.array(list(TextEmbedding("BAAI/bge-small-en-v1.5").embed(texts)), dtype=np.float32))
np.save(OUT / "embed_bge.npy", m)
print("bge", m.shape, f"{time.time() - t0:.0f} s", flush=True)
