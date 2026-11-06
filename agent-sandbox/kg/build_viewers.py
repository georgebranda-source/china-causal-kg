"""Build one graph page per instruction and threshold, in the simplified demo format.

Usage (from agent-sandbox/):  .venv-kg/Scripts/python kg/build_viewers.py
Writes kg/viewer/<version>.html, based on demo_kg/causal_kg_demo_local.html, which is only read. Each page links to the
others. Needs internet for Cytoscape.js, like the demo. Does not change kg/out/nodes.json or edges.json.
"""
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import numpy as np
from sklearn.cluster import AgglomerativeClustering

KG = Path(__file__).resolve().parent
OUT = KG / "out"
VIEW = KG / "viewer"
VIEW.mkdir(exist_ok=True)
DEMO = (KG.parent / "demo_kg" / "causal_kg_demo_local.html").read_text(encoding="utf-8")

VERSIONS = [("event-030", "Event, 0.30", "embed_qwen_instruct.npy", "event", 0.30),
            ("event-035", "Event, 0.35", "embed_qwen_instruct.npy", "event", 0.35),
            ("topic-030", "Topic, 0.30", "embed_qwen_topic.npy", "topic", 0.30),
            ("topic-035", "Topic, 0.35", "embed_qwen_topic.npy", "topic", 0.35)]

T = json.load(open(OUT / "embed_texts.json", encoding="utf-8"))
ROWS = [json.loads(line) for line in open(OUT / "normalised.jsonl", encoding="utf-8")]
FIELDS = ("date", "page", "headline", "quote", "cause", "effect")


def short(description):
    """Label without the closing general phrase."""
    return description.rsplit(",", 1)[0].strip() if "," in description else description.rstrip(".")


def graph(file, threshold):
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
        nodes.append({"id": f"n{n}", "label": short(T[centre]), "loops": []})
        for i in ids:
            node_of[T[i]] = f"n{n}"
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
    stats = {"all_nodes": len(nodes), "singletons": sum(len(v) == 1 for v in groups.values()), "nodes": len(used),
             "edges": len(edges), "multi": sum(len(e["evidence"]) >= 2 for e in edges.values()), "loops": sum(len(n["loops"]) for n in nodes)}
    return {"nodes": used, "edges": list(edges.values()), "stats": stats}


def sub(s, old, new):
    assert old in s, old[:60]
    return s.replace(old, new)


def fmt(d):
    x = date.fromisoformat(d)
    return f"{x.day} {x:%b %Y}"


def build(slug, name, g):
    s = DEMO
    days = sorted(r["date"] for r in ROWS)
    st = g["stats"]
    links = " | ".join(f"<b>{n}</b>" if v == slug else f'<a href="{v}.html">{n}</a>' for v, n, *_ in VERSIONS)
    intro = (f"<p>Version: {links}</p>\n  <p>This graph is built from {len({r['page'] for r in ROWS})} pages of the China Mail, published {fmt(days[0])} to {fmt(days[-1])}, "
             f"covering the 1925 Canton–Hongkong strike. Arrows represent cause/effect relationships stated in the newspaper, as extracted by a local model and not yet hand-checked.</p>\n"
             f"  <p>{len(ROWS)} claims: {st['edges']} arrows ({st['multi']} with more than one claim), {st['all_nodes']} groups ({st['singletons']} with one description), "
             f"and {st['loops']} claims with cause and effect in the same group, listed on that node.</p>")
    s = sub(s, "<h1>China Mail Causal Knowledge Graph Demo</h1>", f"<h1>China Mail Causal Knowledge Graph: {name}</h1>")
    s, n = re.subn(r"<p>This graph is built from 8 pages.*?</p>", lambda _: intro, s, count=1, flags=re.S)
    assert n == 1
    s, n = re.subn(r'(<script id="graph-data" type="application/json">).*?(</script>)',
                   lambda m: m[1] + json.dumps(g, ensure_ascii=False).replace("</", "<\\/") + m[2], s, count=1, flags=re.S)
    assert n == 1
    s, n = re.subn(r"  // keep only explicit causal claims.*?  G\.nodes = G\.nodes\.filter\(n => used\.has\(n\.id\)\);\n", "", s, count=1, flags=re.S)
    assert n == 1
    s = sub(s, "thicker = more articles", "thicker = more claims")
    s = sub(s, '<span class="who">${esc(v.asserted_by)}</span>', "")
    s = sub(s, 'caused, according to ${d.evidence.length} quote,${d.evidence.length > 1 ? "s" : ""}', 'caused, according to ${d.evidence.length} quote${d.evidence.length > 1 ? "s" : ""}')
    s = sub(s, '''<ul class="links">${outs.map(e => row(e, "out")).join("")}</ul>` : ""}`;''',
            '''<ul class="links">${outs.map(e => row(e, "out")).join("")}</ul>` : ""}
      ${d.loops.length ? `<div class="sect">Cause and effect both in this group:</div>${d.loops.map(evHtml).join("")}` : ""}`;''')
    s = sub(s, '<div class="main">', """<p><label for="minw">Minimum claims per arrow: <input type="range" id="minw" min="1" max="2" step="1" value="1"> <span id="minw-out">1</span></label> <span id="minw-count" class="sub"></span></p>

  <div class="main">""")
    s = sub(s, """  cy.on("tap", ev => { if (ev.target === cy) { cy.elements().unselect().removeClass("faded hl"); panel.innerHTML = ""; } });
""", """  cy.on("tap", ev => { if (ev.target === cy) { cy.elements().unselect().removeClass("faded hl"); panel.innerHTML = ""; } });

  // ---- edge weight filter ----
  const minEl = document.getElementById("minw"), minOut = document.getElementById("minw-out"), minCount = document.getElementById("minw-count");
  minEl.max = Math.max(...G.edges.map(e => e.evidence.length));
  function applyMin() {
    const m = +minEl.value;
    cy.elements().unselect().removeClass("faded hl");
    panel.innerHTML = "";
    cy.batch(() => {
      cy.edges().forEach(e => e.style("display", e.data("n") >= m ? "element" : "none"));
      cy.nodes().forEach(n => n.style("display", n.connectedEdges().some(e => e.data("n") >= m) ? "element" : "none"));
    });
    minOut.textContent = m;
    minCount.textContent = `(${cy.edges(":visible").length} arrows, ${cy.nodes(":visible").length} nodes shown)`;
  }
  minEl.addEventListener("input", applyMin);
  minEl.addEventListener("change", () => { runLayout(); cy.fit(cy.elements(":visible"), 30); });
  applyMin();
""")
    return s


for slug, name, file, _, threshold in VERSIONS:
    g = graph(file, threshold)
    (VIEW / f"{slug}.html").write_text(build(slug, name, g), encoding="utf-8")
    print(slug, g["stats"])
