"""Build one graph page per instruction and threshold, in the simplified demo format.

Usage (from agent-sandbox/):  .venv-kg/Scripts/python kg/build_viewers.py
Writes kg/viewer/<version>.html, based on demo_kg/causal_kg_demo_local.html, which is only read. Each page links to the
others. Needs internet for Cytoscape.js, like the demo. Does not change kg/out/nodes.json or edges.json.
"""
import json
import os
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import numpy as np
from sklearn.cluster import AgglomerativeClustering

from refilmed import remove_repeats

KG = Path(__file__).resolve().parent
COMBINED = bool(os.environ.get("KG_COMBINED"))  # all finished batches, from kg/combine.py
OUT = KG / "out" / "combined" if COMBINED else KG / "out"
VIEW = KG / ("viewer_combined" if COMBINED else "viewer")
VIEW.mkdir(exist_ok=True)
DEMO = (KG.parent / "demo_kg" / "causal_kg_demo_local.html").read_text(encoding="utf-8")

VERSIONS = [("event-030", "Event, 0.30", "embed_qwen_event.npy" if COMBINED else "embed_qwen_instruct.npy", "event", 0.30),
            ("event-035", "Event, 0.35", "embed_qwen_event.npy" if COMBINED else "embed_qwen_instruct.npy", "event", 0.35),
            ("topic-030", "Topic, 0.30", "embed_qwen_topic.npy", "topic", 0.30),
            ("topic-035", "Topic, 0.35", "embed_qwen_topic.npy", "topic", 0.35)]

ROWS, REMOVED = remove_repeats([json.loads(line) for line in open(OUT / "normalised.jsonl", encoding="utf-8")])
with open(OUT / "refilmed_removed.jsonl", "w", encoding="utf-8") as f:
    for r, m in REMOVED:
        print(json.dumps({"removed": r, "same_as": m}, ensure_ascii=False), file=f)
ALL_TEXTS = json.load(open(OUT / "embed_texts.json", encoding="utf-8"))
USED = {r[k] for r in ROWS for k in ("cause_description", "effect_description")}
KEEP = [i for i, t in enumerate(ALL_TEXTS) if t in USED]  # leave out descriptions found only on removed claims
T = [ALL_TEXTS[i] for i in KEEP]
FIELDS = ("date", "page", "headline", "quote", "cause", "effect")


def short(description):
    """Label without the closing general phrase."""
    return description.rsplit(",", 1)[0].strip() if "," in description else description.rstrip(".")


def graph(file, threshold):
    m = np.load(OUT / file)[KEEP].astype(np.float64)
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
    s = sub(s, 'caused, according to ${d.evidence.length} quote,${d.evidence.length > 1 ? "s" : ""}', 'caused, according to ${ev.length} quote${ev.length > 1 ? "s" : ""}')
    s = sub(s, 'const d = edgeData[e.id()], s = nodeById[d.source], t = nodeById[d.target];',
            'const d = edgeData[e.id()], s = nodeById[d.source], t = nodeById[d.target], ev = d.evidence.filter(inDates);')
    s = sub(s, '${d.evidence.map(evHtml).join("")}`;', '${ev.map(evHtml).join("")}`;')
    s = sub(s, '<span class="n">${edgeData[e.id()].evidence.length}</span>', '<span class="n">${e.data("n")}</span>')
    s = sub(s, 'const ins = n.incomers("edge"), outs = n.outgoers("edge");',
            'const ins = n.incomers("edge").filter(":visible"), outs = n.outgoers("edge").filter(":visible"), loops = d.loops.filter(inDates);')
    s = sub(s, '''<ul class="links">${outs.map(e => row(e, "out")).join("")}</ul>` : ""}`;''',
            '''<ul class="links">${outs.map(e => row(e, "out")).join("")}</ul>` : ""}
      ${loops.length ? `<div class="sect">Cause and effect both in this group:</div>${loops.map(evHtml).join("")}` : ""}`;''')
    s = sub(s, '<div class="main">', """<p><label for="q">Search: <input type="search" id="q" size="40" placeholder="words in a node, quote, cause, effect, page or date"></label> <span id="q-count" class="sub"></span></p>
  <p><label for="minw">Minimum claims per arrow: <input type="range" id="minw" min="1" max="2" step="1" value="1"> <span id="minw-out">1</span></label> <span id="minw-count" class="sub"></span></p>
  <p>In-degree: <input type="number" id="in-min" min="0" style="width:5em" aria-label="Minimum in-degree"> to <input type="number" id="in-max" min="0" style="width:5em" aria-label="Maximum in-degree">
    &nbsp; Out-degree: <input type="number" id="out-min" min="0" style="width:5em" aria-label="Minimum out-degree"> to <input type="number" id="out-max" min="0" style="width:5em" aria-label="Maximum out-degree">
    &nbsp; Also show their: <label><input type="checkbox" id="show-causes"> causes</label> <label><input type="checkbox" id="show-effects"> effects</label></p>
  <p>Dates: <input type="date" id="d-from" aria-label="From date"> to <input type="date" id="d-to" aria-label="To date">
    &nbsp; <button type="button" id="reset">Reset filters</button></p>

  <div class="main">""")
    s = sub(s, """  cy.on("tap", ev => { if (ev.target === cy) { cy.elements().unselect().removeClass("faded hl"); panel.innerHTML = ""; } });
""", """  cy.on("tap", ev => { if (ev.target === cy) { cy.elements().unselect().removeClass("faded hl"); panel.innerHTML = ""; } });

  // ---- filters: claims per arrow, degree, dates ----
  // Dates apply first, then claims per arrow; degree is counted on the arrows that remain.
  const byId = id => document.getElementById(id);
  const minEl = byId("minw"), minOut = byId("minw-out"), minCount = byId("minw-count");
  const inMin = byId("in-min"), inMax = byId("in-max"), outMin = byId("out-min"), outMax = byId("out-max");
  const causesEl = byId("show-causes"), effectsEl = byId("show-effects"), fromEl = byId("d-from"), toEl = byId("d-to");
  const tally = key => { const c = {}; G.edges.forEach(e => { c[e[key]] = (c[e[key]] || 0) + 1; }); return Math.max(...Object.values(c)); };
  const topIn = tally("target"), topOut = tally("source");
  const allDates = [...G.edges.flatMap(e => e.evidence), ...G.nodes.flatMap(n => n.loops)].map(v => v.date).sort();
  const firstDate = allDates[0], lastDate = allDates[allDates.length - 1];
  minEl.max = Math.max(...G.edges.map(e => e.evidence.length));
  inMin.max = inMax.max = topIn;
  outMin.max = outMax.max = topOut;
  fromEl.min = toEl.min = firstDate;
  fromEl.max = toEl.max = lastDate;
  function inDates(v) { return (!fromEl.value || v.date >= fromEl.value) && (!toEl.value || v.date <= toEl.value); }
  function resetFilters() {
    minEl.value = 1;
    inMin.value = outMin.value = 0;
    inMax.value = topIn;
    outMax.value = topOut;
    causesEl.checked = effectsEl.checked = false;
    fromEl.value = firstDate;
    toEl.value = lastDate;
  }
  function applyFilters() {
    const m = +minEl.value, num = (x, d) => x.value === "" ? d : +x.value;
    const live = [], ins = {}, outs = {}, pass = new Set(), edgesOn = new Set(), nodesOn = new Set();
    cy.elements().unselect().removeClass("faded hl");
    panel.innerHTML = "";
    cy.batch(() => {
      cy.edges().forEach(e => {
        const k = edgeData[e.id()].evidence.filter(inDates).length;
        e.data("n", k);
        if (k > 0 && k >= m) {
          live.push(e);
          outs[e.data("source")] = (outs[e.data("source")] || 0) + 1;
          ins[e.data("target")] = (ins[e.data("target")] || 0) + 1;
        }
      });
      cy.nodes().forEach(n => {
        const i = ins[n.id()] || 0, o = outs[n.id()] || 0;
        if (i + o > 0 && i >= num(inMin, 0) && i <= num(inMax, topIn) && o >= num(outMin, 0) && o <= num(outMax, topOut)) pass.add(n.id());
      });
      pass.forEach(id => nodesOn.add(id));
      live.forEach(e => {
        const s = e.data("source"), t = e.data("target");
        if ((pass.has(s) && pass.has(t)) || (causesEl.checked && pass.has(t)) || (effectsEl.checked && pass.has(s))) {
          edgesOn.add(e.id());
          nodesOn.add(s);
          nodesOn.add(t);
        }
      });
      cy.edges().forEach(e => e.style("display", edgesOn.has(e.id()) ? "element" : "none"));
      cy.nodes().forEach(n => n.style("display", nodesOn.has(n.id()) ? "element" : "none"));
    });
    minOut.textContent = m;
    minCount.textContent = `(${edgesOn.size} arrows, ${nodesOn.size} nodes shown)`;
  }
  const relayout = () => { runLayout(); cy.fit(cy.elements(":visible"), 30); };
  const controls = [minEl, inMin, inMax, outMin, outMax, causesEl, effectsEl, fromEl, toEl];
  controls.forEach(c => {
    c.addEventListener("input", applyFilters);
    c.addEventListener("change", relayout);
  });
  resetFilters();
  applyFilters();

  // ---- search ----
  const qEl = document.getElementById("q"), qCount = document.getElementById("q-count");
  const MAX_ROWS = 100;
  let searching = false, timer;
  function openResult(ele) {
    if (!ele.visible()) {  // hidden by a filter
      resetFilters();
      applyFilters();
      relayout();
    }
    select(ele);
    cy.animate({ center: { eles: ele }, duration: 200 });
  }
  function resultList(title, items, row) {
    if (!items.length) return "";
    const more = items.length > MAX_ROWS ? ` (first ${MAX_ROWS} of ${items.length})` : "";
    return `<div class="sect">${title}${more}:</div><ul class="links">${items.slice(0, MAX_ROWS).map(row).join("")}</ul>`;
  }
  function runSearch() {
    const q = qEl.value.trim().toLowerCase();
    if (q.length < 2) {
      qCount.textContent = "";
      if (searching) { cy.elements().unselect().removeClass("faded hl"); panel.innerHTML = ""; }
      searching = false;
      return;
    }
    searching = true;
    const has = x => String(x || "").toLowerCase().includes(q);
    const hit = v => inDates(v) && [v.quote, v.cause, v.effect, v.page, v.headline, v.date].some(has);
    const nodes = G.nodes.filter(n => has(n.label));
    const arrows = G.edges.map((e, i) => ({ id: "e" + i, e, k: e.evidence.filter(hit).length })).filter(a => a.k).sort((a, b) => b.k - a.k);
    const loops = G.nodes.map(n => ({ n, k: n.loops.filter(hit).length })).filter(a => a.k).sort((a, b) => b.k - a.k);
    const keep = new Set([...nodes.map(n => n.id), ...loops.map(a => a.n.id), ...arrows.flatMap(a => [a.id, a.e.source, a.e.target])]);
    cy.batch(() => {
      cy.elements().unselect().removeClass("faded hl");
      cy.elements().filter(el => !keep.has(el.id())).addClass("faded");
    });
    const claims = arrows.reduce((t, a) => t + a.k, 0) + loops.reduce((t, a) => t + a.k, 0);
    qCount.textContent = `(${nodes.length} nodes, ${claims} claims)`;
    const nodeRow = n => `<li><button type="button" data-node="${n.id}"><span class="n">${n.weight}</span><span>${esc(n.label)}</span></button></li>`;
    const arrowRow = a => `<li><button type="button" data-edge="${a.id}"><span class="n">${a.k}</span><span>${esc(nodeById[a.e.source].label)} → ${esc(nodeById[a.e.target].label)}</span></button></li>`;
    const loopRow = a => `<li><button type="button" data-node="${a.n.id}"><span class="n">${a.k}</span><span>${esc(a.n.label)}</span></button></li>`;
    panel.innerHTML = (`<h2>Results for “${esc(qEl.value.trim())}”</h2>`
      + resultList("Nodes (number = claims on its arrows)", nodes, nodeRow)
      + resultList("Arrows (number = matching claims)", arrows, arrowRow)
      + resultList("Cause and effect both in the group (number = matching claims)", loops, loopRow));
    if (!nodes.length && !arrows.length && !loops.length) panel.innerHTML += "<p>No matches.</p>";
    panel.querySelectorAll("[data-edge]").forEach(b => b.addEventListener("click", () => openResult(cy.getElementById(b.dataset.edge))));
    panel.querySelectorAll("[data-node]").forEach(b => b.addEventListener("click", () => openResult(cy.getElementById(b.dataset.node))));
  }
  qEl.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(runSearch, 150); });
  qEl.addEventListener("focus", runSearch);  // click back in the box to return to the results
  controls.forEach(c => c.addEventListener("input", runSearch));
  byId("reset").addEventListener("click", () => { resetFilters(); applyFilters(); relayout(); runSearch(); });
""")
    return s


for slug, name, file, _, threshold in VERSIONS:
    g = graph(file, threshold)
    (VIEW / f"{slug}.html").write_text(build(slug, name, g), encoding="utf-8")
    print(slug, g["stats"])
