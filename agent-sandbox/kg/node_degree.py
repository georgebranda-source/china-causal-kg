"""Rank the nodes of each combined graph page by degree. Writes kg/out/combined/node_degree_<version>.csv.

degree = arrows touching the node, in + out (each arrow once, however many claims it has). Self-loops are not counted.
claims = claims on those arrows. pages = distinct pages those claims come from.
"""
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

KG = Path(__file__).resolve().parent
for v in ["event-030", "event-035", "topic-030", "topic-035"]:
    s = (KG / "viewer_combined" / f"{v}.html").read_text(encoding="utf-8")
    g = json.loads(re.search(r'<script id="graph-data" type="application/json">(.*?)</script>', s, re.S)[1].replace("<" + chr(92) + "/", "</"))
    out, inn, claims, pages = Counter(), Counter(), Counter(), defaultdict(set)
    for e in g["edges"]:
        out[e["source"]] += 1
        inn[e["target"]] += 1
        for n in (e["source"], e["target"]):
            claims[n] += len(e["evidence"])
            pages[n] |= {x["page"] for x in e["evidence"]}
    rows = [{"degree": out[n["id"]] + inn[n["id"]], "out": out[n["id"]], "in": inn[n["id"]], "claims": claims[n["id"]],
             "pages": len(pages[n["id"]]), "self_loops": len(n["loops"]), "label": n["label"]} for n in g["nodes"]]
    rows.sort(key=lambda r: (-r["degree"], -r["claims"]))
    with open(KG / "out" / "combined" / f"node_degree_{v}.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    d = Counter(r["degree"] for r in rows)
    print("==", v, len(rows), "nodes; degree 1:", d[1], "degree 2:", d[2], "degree 10+:", sum(r["degree"] >= 10 for r in rows))
    for r in rows[:25 if v == "event-035" else 8]:
        print(r["degree"], r["out"], r["in"], r["claims"], r["pages"], r["self_loops"], r["label"][:80])
