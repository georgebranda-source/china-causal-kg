"""Build one graph page per instruction and threshold, from an adapted copy of the demo viewer.

Usage (from agent-sandbox/):  .venv-kg/Scripts/python kg/build_viewers.py
Writes kg/viewer/<version>.html. Open any of them in a browser; each links to the others. Needs internet for
Cytoscape.js and fonts, like the demo. demo_kg/ is only read. Does not change kg/out/nodes.json or edges.json.
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sklearn.cluster import AgglomerativeClustering

KG = Path(__file__).resolve().parent
OUT = KG / "out"
VIEW = KG / "viewer"
VIEW.mkdir(exist_ok=True)
TEMPLATE = (KG.parent / "demo_kg" / "viewer_template.html").read_text(encoding="utf-8")

VERSIONS = [("event-030", "Event, 0.30", "embed_qwen_instruct.npy", "event", 0.30),
            ("event-035", "Event, 0.35", "embed_qwen_instruct.npy", "event", 0.35),
            ("topic-030", "Topic, 0.30", "embed_qwen_topic.npy", "topic", 0.30),
            ("topic-035", "Topic, 0.35", "embed_qwen_topic.npy", "topic", 0.35)]
INSTRUCTIONS = {"event": "descriptions of the same event are close, and different events are far apart, even if they share a topic",
                "topic": "events of the same topic are close, and events of different topics are far apart"}
THEMES = {"violence": "Violence", "agitation": "Agitation & politics", "labour": "Labour action", "economy": "Economy & daily life",
          "response": "Official response", "diplomacy": "Diplomacy", "opinion": "Other"}
KEYWORDS = {
    "violence": r"shoot|shot|\bfir(e|ed|ing)\b|killed|wounded|riot|\bmob\b|murder|assault|bloodshed|attack|pirate|fight",
    "agitation": r"bolshev|soviet|communist|agitat|intimidat|propaganda|instigat|student|unrest|discontent",
    "labour": r"strike|labou?r|coolie|seamen|workers|union|boycott|wage|employees|servants",
    "economy": r"price|\brice\b|food|market|bank|shipping|cargo|\bships?\b|trade|financ|mail|postal|delivery|business|shops",
    "response": r"government|police|regulation|emergency|volunteer|governor|troops|marines|naval",
    "diplomacy": r"consul|legation|diplomatic|protest|powers|foreign office|foreign affairs",
}

T = json.load(open(OUT / "embed_texts.json", encoding="utf-8"))
ROWS = [json.loads(line) for line in open(OUT / "normalised.jsonl", encoding="utf-8")]
FIELDS = ("date", "page", "headline", "quote", "cause", "effect", "cause_description", "effect_description")


def theme_of(members):
    hits = {k: sum(len(re.findall(p, t, re.I)) for t in members) for k, p in KEYWORDS.items()}
    best = max(hits, key=hits.get)
    return best if hits[best] else "opinion"


def short(description):
    """Label without the closing general phrase."""
    return description.rsplit(",", 1)[0].strip() if "," in description else description.rstrip(".")


def graph(file, instruction, threshold):
    m = np.load(OUT / file).astype(np.float64)
    d = np.clip(1 - m @ m.T, 0, 2)
    np.fill_diagonal(d, 0)
    labels = AgglomerativeClustering(n_clusters=None, metric="precomputed", linkage="average", distance_threshold=threshold).fit_predict(d)
    groups = defaultdict(list)
    for i, l in enumerate(labels):
        groups[int(l)].append(i)
    nodes, node_of = [], {}
    for n, k in enumerate(sorted(groups, key=lambda k: -len(groups[k]))):
        ids = groups[k]
        centre = ids[int(np.argmin(d[np.ix_(ids, ids)].sum(1)))]
        members = [T[i] for i in ids]
        nodes.append({"id": f"n{n}", "label": short(T[centre]), "theme": theme_of(members), "phrases": members, "loops": []})
        for t in members:
            node_of[t] = f"n{n}"
    by_id = {n["id"]: n for n in nodes}
    edges = {}
    for r in ROWS:
        a, b = node_of[r["cause_description"]], node_of[r["effect_description"]]
        ev = {k: r[k] or "" for k in FIELDS}
        if a == b:
            by_id[a]["loops"].append(ev)
        else:
            edges.setdefault((a, b), {"source": a, "target": b, "evidence": []})["evidence"].append(ev)
    weight = Counter()
    for (a, b), e in edges.items():
        weight[a] += len(e["evidence"])
        weight[b] += len(e["evidence"])
    used = [n for n in nodes if weight[n["id"]]]
    for n in used:
        n["weight"] = weight[n["id"]]
    loops = sum(len(n["loops"]) for n in nodes)
    return {"themes": THEMES, "nodes": used, "edges": list(edges.values()),
            "stats": {"pages": len({r["page"] for r in ROWS}), "relations": len(ROWS), "groups": sum(len(n["phrases"]) >= 2 for n in nodes),
                      "singletons": sum(len(n["phrases"]) == 1 for n in nodes), "all_nodes": len(nodes), "nodes": len(used),
                      "edges": len(edges), "multi": sum(len(e["evidence"]) >= 2 for e in edges.values()), "loops": loops,
                      "phrases": len(T), "instruction": instruction, "threshold": threshold}}


def sub(s, old, new):
    assert old in s, old[:60]
    return s.replace(old, new)


def adapt(template):
    s = template
    s = sub(s, "<title>Hongkong Strike Causal Graph</title>", "<title>Strike Graph Comparison</title>")
    s = sub(s, "16 June – 3 July 1925", "June–July 1925 · local Qwen run")
    s = sub(s, "What caused the 1925 Hongkong strike, according to the China Mail", "__VERSION_TITLE__")
    s = re.sub(r'<p class="lede">.*?</p>', '<p class="lede">Each arrow is a causal claim printed in the paper, extracted by a local model. <strong>Click any arrow to read the 1925 sentences behind it.</strong> Node names and colours are provisional.</p>\n    <nav class="versions" aria-label="Versions">__VERSION_LINKS__</nav>', s, count=1, flags=re.S)
    s = sub(s, ".chip .dot {", ".versions { display: flex; flex-wrap: wrap; gap: 6px; }\n.versions a { font: 500 13px var(--font-body); color: var(--ink); text-decoration: none; background: var(--surface); border: 1px solid var(--rule); border-radius: 4px; padding: 5px 11px; }\n.versions a[aria-current] { background: var(--accent); border-color: var(--accent); color: var(--surface); }\n.chip .dot {")
    s = sub(s, '<label class="toggle" for="frag"><input type="checkbox" id="frag"> Hide isolated pairs</label>',
            '<label class="toggle" for="frag"><input type="checkbox" id="frag" checked> Hide isolated pairs</label>\n    <div class="date-ctl"><label class="ctl-label" for="minc">Minimum claims per arrow</label><input type="range" id="minc" min="1" max="4" step="1" value="1" style="width:90px"><span class="date-out" id="minc-out">1</span></div>')
    s = re.sub(r'<div class="edge-key" aria-hidden="true">.*?</div>', '<div class="edge-key" aria-hidden="true"><span>thicker = more claims · bigger = more claims touch it</span></div>', s, count=1, flags=re.S)
    s = re.sub(r'<div class="notes">.*?</div>\n</div>\n\n<script id="graph-data"', '''<div class="notes">
    <section>
      <h3>How it was built</h3>
      <ol>
        <li><b>Extraction.</b> <span id="n-extract"></span></li>
        <li><b>Descriptions.</b> The local model wrote a one-sentence description of each cause and effect from the full article.</li>
        <li><b>Grouping.</b> <span id="n-cluster"></span></li>
        <li><b>Graph.</b> Claims between the same two groups are merged into one arrow. Claims with cause and effect in the same group can't be arrows, so they're listed on the node.</li>
      </ol>
    </section>
    <section>
      <h3>How to read it</h3>
      <p>Arrows record <b>what the paper or its sources claimed</b>, not established causes. This run doesn't record who made each claim, so reported speech, Reuter cables and the paper's own voice look the same here.</p>
      <p>The sidebar shows how many claims sit inside a node instead of forming an arrow.</p>
    </section>
    <section class="caveat">
      <h3>Limits of this draft</h3>
      <p>Nothing here has been hand-checked. Node names are each group's most central description. Colours come from keyword counts and can be wrong. Notices reprinted on several days are counted each time, so some arrows look stronger than they are. Two counterfactual descriptions are known to be wrong.</p>
    </section>
  </div>
</div>

<script id="graph-data"''', s, count=1, flags=re.S)
    s = re.sub(r'document\.getElementById\("stats"\)\.innerHTML =.*?// edge kind: the strongest form any of its quotes takes\n  const kindOf = .*?\n', '''document.getElementById("stats").innerHTML =
    `<span><b>${S.relations}</b> claims</span><span><b>${S.all_nodes}</b> groups in all</span><span><b>${S.singletons}</b> singletons</span>` +
    `<span><b>${S.edges}</b> arrows</span><span><b>${S.multi}</b> arrows with 2+ claims</span><span><b>${S.loops}</b> claims inside a node</span>`;
  document.getElementById("n-extract").textContent =
    `${S.relations} cause → effect claims from ${S.pages} pages passed the quote check and the second-pass check.`;
  document.getElementById("n-cluster").textContent =
    `${S.phrases} descriptions were embedded with qwen3-embedding:8b, instructed so that ${S.instruction}, then grouped by average-link clustering at cosine distance ${S.threshold.toFixed(2)}.`;
''', s, count=1, flags=re.S)
    s = sub(s, ', n: e.evidence.length, kind: kindOf(e.evidence) } }', ', n: e.evidence.length } }')
    s = sub(s, '''        "line-style": ele => ele.data("kind") === "explicit" ? "solid" : "dashed",
        "line-dash-pattern": ele => ele.data("kind") === "counterfactual" ? [1.5, 4] : [6, 3],
''', "")
    s = sub(s, "numIter: 2500", "numIter: 1200")
    s = sub(s, "  runLayout();\n\n  // re-color", "\n  // re-color")
    s = sub(s, '''fragEl = document.getElementById("frag");''', '''fragEl = document.getElementById("frag"), minEl = document.getElementById("minc"), minOut = document.getElementById("minc-out");''')
    s = sub(s, '''  fragEl.addEventListener("change", applyFilters);''', '''  fragEl.addEventListener("change", applyFilters);
  minEl.addEventListener("input", applyFilters);''')
    s = sub(s, "    dateOut.textContent = fmtDate(upto);", "    dateOut.textContent = fmtDate(upto);\n    minOut.textContent = minEl.value;")
    s = sub(s, 'const vis = ev.length > 0 && on[', 'const vis = ev.length >= +minEl.value && on[')
    s = sub(s, '''      <div class="meta"><span class="who">${esc(v.asserted_by)}</span><span>${fmtDate(v.date)}</span><span>${esc(v.headline)}</span><span class="kind ${v.kind}">${v.kind}</span></div>
      <div class="norm">Extracted as: ${esc(v.cause)} → ${esc(v.effect)} · <code>${esc(v.page)}</code></div>''',
            '''      <div class="meta"><span>${fmtDate(v.date)}</span><span>${esc(v.headline)}</span></div>
      <div class="norm">Extracted as: ${esc(v.cause)} → ${esc(v.effect)} · <code>${esc(v.page)}</code></div>''')
    s = sub(s, "↓ caused, according to ${d.evidence.length} quote", "↓ according to ${d.evidence.length} quote")
    s = sub(s, '''<div class="sect">Extracted phrases merged here</div>''', '''${d.loops.length ? `<div class="sect">Claims inside this node (${d.loops.length})</div>${d.loops.map(evHtml).join("")}` : ""}
      <div class="sect">Descriptions grouped here (${d.phrases.length})</div>''')
    s = sub(s, '''
      <p class="sub">HDBSCAN cluster${d.hdbscan.length > 1 ? "s" : ""}: <code>${d.hdbscan.join(", ")}</code></p>`;''', "`;")
    s = sub(s, "  applyFilters();\n  // open on the biggest hub", "  applyFilters();\n  runLayout();\n  cy.fit(cy.elements(\":visible\"), 30);\n  // open on the biggest hub")
    return s


template = adapt(TEMPLATE)
for slug, name, file, instruction, threshold in VERSIONS:
    g = graph(file, INSTRUCTIONS[instruction], threshold)
    links = "".join(f'<a href="{s}.html"{" aria-current=\"page\"" if s == slug else ""}>{n}</a>' for s, n, *_ in VERSIONS)
    page = template.replace("__VERSION_TITLE__", f"Strike graph: {name}").replace("__VERSION_LINKS__", links)
    page = page.replace("__GRAPH_JSON__", json.dumps(g, ensure_ascii=False).replace("</", "<\\/"))
    html = '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n</head>\n<body>\n' + page + "\n</body>\n</html>\n"
    (VIEW / f"{slug}.html").write_text(html, encoding="utf-8")
    print(slug, {k: g["stats"][k] for k in ("all_nodes", "groups", "singletons", "nodes", "edges", "multi", "loops")}, Counter(n["theme"] for n in g["nodes"]).most_common(7))
