"""Build the layered perception graph and the category counts (PLAN.md sections 4-6).

Inputs (OUT): normalised.jsonl, speakers.jsonl, articles_selected.jsonl.
Layers: evidence (articles, claims) -> events (agglomerative clusters, event instruction, 0.35, as v1 event-035)
        -> concepts (approved anchors, nearest-anchor rule) ; speakers (speaker pass).
Writes OUT/graph/: claims.csv, events.csv, event_edges.csv, concept_edges.csv, speakers.csv, speaker_concept.csv,
graph.json, counts.md, anchors.json.
Usage: .venv-kg/Scripts/python kg/perception/graph.py
"""
import csv
import json
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sklearn.cluster import AgglomerativeClustering

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

G = C.OUT / "graph"
G.mkdir(exist_ok=True)
INSTRUCTION = ("Represent this event from a 1925 Hongkong newspaper so that descriptions of the same event are close, "
               "and different events are far apart, even if they share a topic.")  # v1 event instruction (combine.py)
EVENT_THRESHOLD = 0.35
THRESHOLD, MARGIN, SENSITIVITY = 0.65, 0.02, (0.60, 0.65, 0.70)
STRIKE = ["Chinese workers in Hongkong go on strike, a general strike.",
          "Workers leave Hongkong for Canton, an exodus of labour.",
          "A boycott of British trade and shipping, a boycott."]
ANCHORS = {  # approved 2026-11-16; 3T second anchor added at the user's approval of the split
    "1a_red_agitators": ["Bolshevik agitators instigate the strike, a Communist conspiracy.",
                         "Soviet agents and Communist propaganda stir up labour unrest, a Bolshevik plot."],
    "1b_strikers_red": ["The striking workers are Communists, a Bolshevik labour movement.",
                        "Hongkong workers adopt Bolshevism, a Red labour movement."],
    "2_canton_support": ["The Canton Government orders and directs the strike, a political intervention.",
                         "Canton authorities pay, feed and house strikers who leave Hongkong, strike support.",
                         "Canton provides transport for workers leaving Hongkong, an organised evacuation.",
                         "Canton pickets prevent strikers returning to Hongkong, picket enforcement."],
    "3T_shootings": ["The shooting of Chinese demonstrators at Shakee in Canton, a massacre.",
                     "Police fire on Chinese students in Shanghai, a shooting."],
    "3M_patriotic_motive": ["Chinese patriotic anger at the shooting of students in Shanghai, a nationalist protest.",
                            "Chinese resentment of foreign privilege and unequal treaties, an anti-foreign movement.",
                            "Workers strike in sympathy with their compatriots in Shanghai, a patriotic protest."],
    "C_intimidation": ["Workers are forced to strike by threats and intimidation, coercion."],
    "C_labour": ["Workers demand higher wages and better conditions, an economic grievance."],
}
BRITISH = {"PAPER", "BRITISH_OFFICIAL", "BRITISH_OTHER"}
CHINESE = {"CHINESE", "CANTON_GOVT"}
HK_CANTON = ("hongkong", "hong kong", "kowloon", "canton", "shameen", "kwangtung")


def embed(texts):
    vecs = []
    inputs = [f"Instruct: {INSTRUCTION}\nQuery:{t}" for t in texts]
    for i in range(0, len(inputs), 32):
        body = {"model": "qwen3-embedding:8b", "input": inputs[i:i + 32], "keep_alive": "2m"}
        req = urllib.request.Request("http://localhost:11434/api/embed", json.dumps(body).encode(), {"Content-Type": "application/json"})
        vecs += json.load(urllib.request.urlopen(req, timeout=600))["embeddings"]
    m = np.array(vecs, dtype=np.float64)
    return m / np.linalg.norm(m, axis=1, keepdims=True)


def fortnight(date):
    y, m, d = date.split("-")
    return f"{y}-{m} {'a (1-15)' if int(d) <= 15 else 'b (16-)'}"


def assign(sims_by_cat, threshold):
    """sims_by_cat: {cat: max sim}. Nearest category if >= threshold and >= MARGIN above the next; else 'other'."""
    ranked = sorted(sims_by_cat.items(), key=lambda kv: -kv[1])
    (c1, s1), (_, s2) = ranked[0], ranked[1]
    return c1 if s1 >= threshold and s1 - s2 >= MARGIN else "other"


def voice_group(t):
    return "BRITISH" if t in BRITISH else "CHINESE" if t in CHINESE else "OTHER"


def main():
    t0 = time.time()
    rows = C.load_jsonl(C.OUT / "normalised.jsonl")
    arts = {a["article_id"]: a for a in C.load_jsonl(C.OUT / "articles_selected.jsonl")}
    spk = {}
    for r in C.load_jsonl(C.OUT / "speakers.jsonl"):
        for c in r["claims"]:
            spk[(r["article_id"], c["quote"], c["cause"], c["effect"])] = c
    texts = sorted({r[k] for r in rows for k in ("cause_description", "effect_description")})
    anchor_texts = STRIKE + [t for v in ANCHORS.values() for t in v]
    M = embed(texts + anchor_texts)
    T, A = M[:len(texts)], M[len(texts):]
    idx = {t: i for i, t in enumerate(texts)}
    S = T @ A.T  # description x anchor
    cats = ["STRIKE"] * len(STRIKE) + [c for c, v in ANCHORS.items() for _ in v]

    def cat_sims(row):
        out = defaultdict(lambda: -1.0)
        for c, s in zip(cats, row):
            out[c] = max(out[c], float(s))
        return dict(out)

    desc_sims = [cat_sims(S[i]) for i in range(len(texts))]

    # event layer
    D = np.clip(1 - T @ T.T, 0, 2)
    np.fill_diagonal(D, 0)
    labels = AgglomerativeClustering(n_clusters=None, metric="precomputed", linkage="average",
                                     distance_threshold=EVENT_THRESHOLD).fit_predict(D) if len(texts) > 1 else np.zeros(1, int)
    members = defaultdict(list)
    for i, l in enumerate(labels):
        members[int(l)].append(i)
    order = sorted(members, key=lambda k: (-len(members[k]), min(members[k])))
    event_of, events = {}, []
    for n, k in enumerate(order):
        ids = members[k]
        centre = ids[int(np.argmin(D[np.ix_(ids, ids)].sum(1)))]
        cv = T[ids].mean(0)
        cv /= np.linalg.norm(cv)
        sims = cat_sims(A @ cv)
        events.append({"event": f"e{n}", "label": texts[centre], "size": len(ids), "concept": assign(sims, THRESHOLD),
                       "concept_sim": round(max(sims.values()), 3), "members": [texts[i] for i in ids]})
        for i in ids:
            event_of[i] = f"e{n}"

    # claims
    claims = []
    for r in rows:
        ci, ei = idx[r["cause_description"]], idx[r["effect_description"]]
        sp = spk.get((r["article_id"], r["quote"], r["cause"], r["effect"]), {})
        a = arts.get(r["article_id"], {})
        eplace = (r.get("effect_place") or "").lower()
        es = desc_sims[ei]
        rec = {"id": r["key"], "article_id": r["article_id"], "page": r["page"], "date": r["date"], "fortnight": fortnight(r["date"]),
               "headline": r["headline"], "is_letter": a.get("is_letter", False),
               "speaker": sp.get("speaker", ""), "speaker_type": sp.get("speaker_type", "MISSING"),
               "voice_group": voice_group(sp.get("speaker_type", "")),
               "quote": r["quote"], "cause": r["cause"], "effect": r["effect"],
               "cause_place": r.get("cause_place", ""), "cause_description": r["cause_description"],
               "effect_place": r.get("effect_place", ""), "effect_description": r["effect_description"],
               "cause_event": event_of[ci], "effect_event": event_of[ei],
               "effect_hk_canton": any(p in eplace for p in HK_CANTON),
               "effect_place_unknown": eplace.strip() in ("", "unknown"),
               "effect_strike_sim": round(es["STRIKE"], 3)}
        for th in SENSITIVITY:
            tag = f"{int(th * 100)}"
            strike = assign(es, th) == "STRIKE"
            rec[f"in_scope_strict_{tag}"] = rec["effect_hk_canton"] and strike  # plan: place named as Hongkong or Canton
            rec[f"in_scope_{tag}"] = (rec["effect_hk_canton"] or rec["effect_place_unknown"]) and strike  # broad: or no place given
            rec[f"cause_concept_{tag}"] = assign({k: v for k, v in desc_sims[ci].items() if k != "STRIKE"}, th)
        rec["effect_concept"] = assign(es, THRESHOLD)
        rec["cause_concept"], rec["in_scope"] = rec["cause_concept_65"], rec["in_scope_65"]
        for c in ANCHORS:
            rec[f"sim_{c}"] = round(desc_sims[ci][c], 3)
        claims.append(rec)

    # tables
    def write(name, recs):
        if not recs:
            (G / name).write_text("", encoding="utf-8")
            return
        with open(G / name, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(recs[0]))
            w.writeheader()
            w.writerows(recs)

    write("claims.csv", claims)
    write("events.csv", [{k: v for k, v in e.items() if k != "members"} for e in events])
    ee = defaultdict(list)
    for c in claims:
        ee[(c["cause_event"], c["effect_event"])].append(c["id"])
    write("event_edges.csv", [{"source": s, "target": t, "claims": len(v), "self_loop": s == t, "claim_ids": ";".join(v)}
                              for (s, t), v in sorted(ee.items(), key=lambda kv: -len(kv[1]))])
    ce = defaultdict(Counter)
    for c in claims:
        tgt = "HK_STRIKE" if c["in_scope"] else c["effect_concept"]
        if tgt == "STRIKE":
            tgt = "STRIKE_ELSEWHERE"
        ce[(c["cause_concept"], tgt)][c["voice_group"]] += 1
    write("concept_edges.csv", [{"source": s, "target": t, "total": sum(v.values()), **{g: v[g] for g in ("BRITISH", "CHINESE", "OTHER")}}
                                for (s, t), v in sorted(ce.items(), key=lambda kv: -sum(kv[1].values()))])
    sp_rows = Counter((c["speaker"], c["speaker_type"]) for c in claims)
    write("speakers.csv", [{"speaker": s, "speaker_type": t, "claims": n} for (s, t), n in sp_rows.most_common()])
    dna = Counter((c["speaker"], c["speaker_type"], c["cause_concept"]) for c in claims if c["in_scope"] and c["cause_concept"] != "other")
    write("speaker_concept.csv", [{"speaker": s, "speaker_type": t, "concept": k, "claims": n} for (s, t, k), n in dna.most_common()])
    (G / "anchors.json").write_text(json.dumps({"instruction": INSTRUCTION, "threshold": THRESHOLD, "margin": MARGIN,
                                                "event_threshold": EVENT_THRESHOLD, "strike": STRIKE, "anchors": ANCHORS}, indent=1), encoding="utf-8")
    graph = {"layers": ["article", "claim", "event", "concept", "speaker"],
             "concepts": ["HK_STRIKE", "STRIKE_ELSEWHERE", *ANCHORS, "other"],
             "events": events, "claims": claims,
             "articles": [{"article_id": k, "page": a["page"], "date": a["date"], "headline": a.get("headline"), "is_letter": a.get("is_letter")}
                          for k, a in arts.items() if any(c["article_id"] == k for c in claims)]}
    (G / "graph.json").write_text(json.dumps(graph, ensure_ascii=False), encoding="utf-8")

    # counts report
    L = [f"# Perception run: category counts (unvalidated)\n", f"Built {time.strftime('%Y-%m-%d %H:%M')}. Claims {len(claims)}, "
         f"descriptions {len(texts)}, events {len(events)}. Threshold {THRESHOLD}, margin {MARGIN}.\n"]
    runs = [(th, "", "broad: Hongkong, Canton or no place") for th in SENSITIVITY] + [(THRESHOLD, "strict_", "strict: Hongkong or Canton named")]
    for th, sx, desc in runs:
        tag = f"{int(th * 100)}"
        sc = [c for c in claims if c[f"in_scope_{sx}{tag}"]]
        L.append(f"\n## Causes of the Hongkong strike, threshold {th}, scope {desc} ({len(sc)} claims)\n")
        L.append("| cause concept | BRITISH | CHINESE | OTHER | total |\n|---|---|---|---|---|")
        cnt = defaultdict(Counter)
        for c in sc:
            cnt[c[f"cause_concept_{tag}"]][c["voice_group"]] += 1
        for k in [*ANCHORS, "other"]:
            v = cnt[k]
            L.append(f"| {k} | {v['BRITISH']} | {v['CHINESE']} | {v['OTHER']} | {sum(v.values())} |")
    sc = [c for c in claims if c["in_scope"]]
    L.append("\n## By speaker type (threshold 0.65, in scope)\n")
    types = sorted({c["speaker_type"] for c in claims})
    L.append("| cause concept | " + " | ".join(types) + " |\n|" + "---|" * (len(types) + 1))
    for k in [*ANCHORS, "other"]:
        L.append(f"| {k} | " + " | ".join(str(sum(c["cause_concept"] == k and c["speaker_type"] == t for c in sc)) for t in types) + " |")
    L.append("\n## By fortnight, British voices (threshold 0.65, in scope)\n")
    fns = sorted({c["fortnight"] for c in claims})
    L.append("| cause concept | " + " | ".join(fns) + " |\n|" + "---|" * (len(fns) + 1))
    for k in [*ANCHORS, "other"]:
        L.append(f"| {k} | " + " | ".join(str(sum(c["cause_concept"] == k and c["fortnight"] == f and c["voice_group"] == "BRITISH" for c in sc)) for f in fns) + " |")
    for vg in ("BRITISH", "CHINESE"):
        L.append(f"\n## By month, {vg} voices (threshold 0.65, in scope)\n")
        ms = sorted({c["date"][:7] for c in claims})
        L.append("| cause concept | " + " | ".join(ms) + " |\n|" + "---|" * (len(ms) + 1))
        for k in [*ANCHORS, "other"]:
            L.append(f"| {k} | " + " | ".join(str(sum(c["cause_concept"] == k and c["date"][:7] == m and c["voice_group"] == vg for c in sc)) for m in ms) + " |")
    L.append(f"\nSpeaker types, all claims:{dict(Counter(c['speaker_type'] for c in claims))}")
    L.append(f"\nLetters: {sum(c['is_letter'] for c in claims)} claims. Time {time.time() - t0:.0f} s.")
    (G / "counts.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
