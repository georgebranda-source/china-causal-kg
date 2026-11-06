"""Do opposite events sit farther apart than same-topic events? Pairs are real descriptions, matched by their start."""
import json, sys, time, urllib.request
from pathlib import Path
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
OUT = Path(__file__).resolve().parent / "out"
T = json.load(open(OUT / "embed_texts.json", encoding="utf-8"))
find = lambda s: next(i for i, t in enumerate(T) if t.startswith(s))
OPP = [("Chinese banks and shipping hongs at Shanghai are closed", "A decision is made to re-open the banks"),
       ("Prices of pork rise", "Chinese retailers are forced to bring prices down"),
       ("Food prices shoot up in Macao", "Chinese retailers are forced to bring prices down"),
       ("Cafe Wiseman's office staff go on strike", "The strikers desire to resume work"),
       ("Employees at the Aquarius", "Many Kowloon Dock employees accept the option to return"),
       ("Frenchtown succumbs to the agitators after shops close", "Chinese shops at Nanking Road do not close")]
SAME = [("U.S. marines land from", "Several hundreds of marines and blue-jackets land"),
        ("Cafe Wiseman's office staff go on strike", "Employees at the Aquarius"),
        ("Prices of pork rise", "Food prices shoot up in Macao"),
        ("The launches cease running from Nam Tau", "No trams run in Hongkong yesterday"),
        ("The launches cease running from Nam Tau", "The s.s. Fatshan does not sail for Canton"),
        ("The Commissioner for Foreign Affairs protests", "The Peking Government and Shanghai Foreign Commissioner make demands")]
for name in ("qwen_instruct", "qwen_plain", "bge"):
    m = np.load(OUT / f"embed_{name}.npy")
    sim = lambda p: float(m[find(p[0])] @ m[find(p[1])])
    o = [sim(p) for p in OPP]; s = [sim(p) for p in SAME]
    print(f"{name}: opposites {np.mean(o):.2f} ({min(o):.2f}-{max(o):.2f}); same-topic {np.mean(s):.2f} ({min(s):.2f}-{max(s):.2f})")
    print("   opposites:", [round(x, 2) for x in o], " same-topic:", [round(x, 2) for x in s])
t0 = time.time()
body = {"model": "qwen3-embedding:8b", "input": T[:200], "keep_alive": "2m"}
urllib.request.urlopen(urllib.request.Request("http://localhost:11434/api/embed", json.dumps(body).encode(), {"Content-Type": "application/json"}), timeout=300).read()
print(f"qwen embedding: {(time.time() - t0) / 200:.3f} s per description")
