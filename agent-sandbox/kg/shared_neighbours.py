"""Missing-edge candidates from shared neighbours. If causes A and B share k or more effects, each effect of A that B lacks is a
candidate for B, and the reverse. The same is run for effects sharing causes. Counts distinct arrows, not claims."""
import json, re, sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
V = Path(__file__).resolve().parent / "viewer"
for slug in ("event-030", "event-035", "topic-030", "topic-035"):
    html = (V / f"{slug}.html").read_text(encoding="utf-8")
    raw = re.search(r'<script id="graph-data" type="application/json">(.*?)</script>', html, re.S)[1].replace(chr(92) + "/", "/")
    g = json.loads(raw)
    L = {n["id"]: n["label"] for n in g["nodes"]}
    eff, cau = defaultdict(set), defaultdict(set)
    for e in g["edges"]:
        eff[e["source"]].add(e["target"]); cau[e["target"]].add(e["source"])
    print(f"\n{slug}: {len(eff)} causes; with 2+ effects {sum(len(v) >= 2 for v in eff.values())}, 3+ {sum(len(v) >= 3 for v in eff.values())}, 4+ {sum(len(v) >= 4 for v in eff.values())}")
    for name, side in (("causes sharing effects", eff), ("effects sharing causes", cau)):
        pairs = [(a, b, side[a] & side[b]) for a, b in combinations(side, 2)]
        for k in (1, 2, 3):
            hits = [p for p in pairs if len(p[2]) >= k]
            cand = sum(len(side[a] - side[b]) + len(side[b] - side[a]) for a, b, _ in hits)
            print(f"  {name}: pairs sharing {k}+: {len(hits)}, candidates {cand}")
        if slug in ("event-035", "topic-035"):
            for a, b, s in sorted((p for p in pairs if len(p[2]) >= 2), key=lambda p: -len(p[2]) / len(side[p[0]] | side[p[1]]))[:6]:
                print(f"    [{len(s)} shared, sizes {len(side[a])}/{len(side[b])}] {L[a][:44]}  &  {L[b][:44]}")
                print(f"       shared: {'; '.join(L[x][:38] for x in list(s)[:3])}")
                for x in list(side[a] - side[b])[:2]: print(f"       only 1st: {L[x][:60]}")
                for x in list(side[b] - side[a])[:2]: print(f"       only 2nd: {L[x][:60]}")
