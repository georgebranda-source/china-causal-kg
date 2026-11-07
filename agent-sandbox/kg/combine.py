"""Merge June-July with every finished batch, embed with both instructions, and build the pages in kg/viewer_combined/."""
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np

KG = Path(__file__).resolve().parent
OUT = KG / "out" / "combined"
OUT.mkdir(exist_ok=True)
INSTRUCTIONS = {
    "event": "Represent this event from a 1925 Hongkong newspaper so that descriptions of the same event are close, and different events are far apart, even if they share a topic.",
    "topic": "Represent this event from a 1925-1926 Hongkong newspaper so that events of the same topic are close, and events of different topics are far apart.",
}
files = [KG / "out" / "normalised.jsonl"] + sorted((KG / "out" / "batches").glob("*/normalised.jsonl"))
rows = [json.loads(line) for f in files for line in open(f, encoding="utf-8")]
(OUT / "normalised.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
texts = sorted({r[k] for r in rows for k in ("cause_description", "effect_description")})
(OUT / "embed_texts.json").write_text(json.dumps(texts, ensure_ascii=False, indent=0), encoding="utf-8")
print(len(files), "sets,", len(rows), "claims,", len(texts), "descriptions", flush=True)
for name, instruction in INSTRUCTIONS.items():
    t0, vectors = time.time(), []
    inputs = [f"Instruct: {instruction}\nQuery:{t}" for t in texts]
    for i in range(0, len(inputs), 32):
        body = {"model": "qwen3-embedding:8b", "input": inputs[i:i + 32], "keep_alive": "2m"}
        req = urllib.request.Request("http://localhost:11434/api/embed", json.dumps(body).encode(), {"Content-Type": "application/json"})
        vectors += json.load(urllib.request.urlopen(req, timeout=600))["embeddings"]
    m = np.array(vectors, dtype=np.float32)
    np.save(OUT / f"embed_qwen_{name}.npy", m / np.linalg.norm(m, axis=1, keepdims=True))
    print(name, f"{time.time() - t0:.0f} s", flush=True)
subprocess.run([sys.executable, str(KG / "build_viewers.py")], check=True, env={**os.environ, "KG_COMBINED": "1"})
subprocess.run([sys.executable, str(KG / "export_neo4j.py")], check=True)
