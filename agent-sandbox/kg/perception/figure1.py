"""Fig. 1 for the paper: the event graph one step upstream of the Hongkong strike (view B, depth 1), as a print-ready PNG.

Settings (user, 2026-11-16): θ = 0.65, broad scope, May 1925 - Apr 1926, all voices, depth 1, the 23 strike-event nodes with their
cluster labels unchanged, network layout, US Letter with 1 in margins: figure area 6.5 x 8.3 in (0.7 in left for the caption),
PNG at 300 dpi = 1950 x 2490 px. Labels are 9 CSS px = 6.75 pt in print.

Layout (deterministic, no random seed): strike events are boxes with their text inside; every other event is a small shape whose
label sits on the side facing away from its arrow. Each connected group is laid out radially around its best-connected node, and
the ring sizes are searched for the most compact arrangement with no overlapping boxes and no arrow passing through a label.
Groups are then packed onto the page (largest first) and spread to fill it; spreading positions apart cannot create overlaps.
The page measures every node+label box and reports overlaps, out-of-bounds boxes and arrows crossing labels; the script refuses
a render that has any of them.

Usage (from agent-sandbox/): .venv-kg/Scripts/python kg/perception/figure1.py [graph_dir]
Writes kg/analysis/perception/figures/fig1.png (and fig1.html, the source page).
"""
import csv
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
GDIR = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / "out" / "perception" / "graph"
FIGS = HERE.parent / "analysis" / "perception" / "figures"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
DPI, CSS_DPI = 300, 96
W_IN, H_IN = 6.5, 8.3                      # figure area on a US Letter page with 1 in margins, minus 0.7 in for the caption
W, H = round(W_IN * CSS_DPI), round(H_IN * CSS_DPI)   # 624 x 797 CSS px; rendered at 300/96 = 3.125x -> 1950 x 2490 px
LEGEND_H = 46
TH = "65"

CODE = {"1a_red_agitators": "1a", "1b_strikers_red": "1b", "2_canton_support": "2", "3T_shootings": "3T",
        "3M_patriotic_motive": "3M", "4_working_conditions": "4", "C_intimidation": "I"}
NAME = {"1a_red_agitators": "Red agitators", "1b_strikers_red": "Strikers are Red", "2_canton_support": "Canton support",
        "3T_shootings": "Shootings (trigger)", "3M_patriotic_motive": "Patriotism (motive)",
        "4_working_conditions": "Working conditions", "C_intimidation": "Intimidation"}
SHAPE = {"1a_red_agitators": "triangle", "1b_strikers_red": "vee", "2_canton_support": "diamond", "3T_shootings": "star",
         "3M_patriotic_motive": "hexagon", "4_working_conditions": "pentagon", "C_intimidation": "octagon"}


def data():
    claims = list(csv.DictReader(open(GDIR / "claims.csv", encoding="utf-8")))
    events = {e["event"]: e for e in json.loads((GDIR / "graph.json").read_text(encoding="utf-8"))["events"]}
    sc = [c for c in claims if c[f"in_scope_{TH}"] == "True" and c["cause_event"] != c["effect_event"]]
    edges = defaultdict(list)
    for c in sc:
        edges[(c["cause_event"], c["effect_event"])].append(c["id"])
    strike = {c["effect_event"] for c in sc}
    nodes = []
    for i in sorted({e for k in edges for e in k}):
        label = re.sub(r", an? [^,]*\.$|\.$", "", events[i]["label"])   # drop the trailing type label, as in the viewer
        cat = events[i]["concept"]
        if i in strike:
            nodes.append({"id": i, "label": label, "kind": "strike"})
        elif cat in CODE:
            nodes.append({"id": i, "label": f"{CODE[cat]} · {label}", "kind": "cat", "shape": SHAPE[cat], "cat": cat})
        else:
            nodes.append({"id": i, "label": label, "kind": "other"})
    # user, 2026-11-16: 65 full labels do not fit one page legibly (text boxes cover ~67% of it), so Fig. 1 shows only the
    # largest connected group; the small groups are written to a table for the caption or an appendix.
    adj = defaultdict(set)
    for s, t in edges:
        adj[s].add(t); adj[t].add(s)
    comps, seen = [], set()
    for n in sorted(adj):
        if n in seen:
            continue
        stack, comp = [n], set()
        while stack:
            x = stack.pop()
            if x not in comp:
                comp.add(x); stack.extend(adj[x])
        seen |= comp; comps.append(comp)
    comps.sort(key=len, reverse=True)
    main, rest = comps[0], comps[1:]
    keep_e = {k: v for k, v in edges.items() if k[0] in main}
    by_id = {n["id"]: n for n in nodes}
    small = [{"group": g + 1, "cause": by_id[s]["label"], "effect (strike event)": by_id[t]["label"], "claims": len(v)}
             for g, comp in enumerate(rest) for (s, t), v in sorted(edges.items()) if s in comp]
    main_nodes = [n for n in nodes if n["id"] in main]
    return {"nodes": main_nodes, "edges": [{"source": s, "target": t, "n": len(v)} for (s, t), v in sorted(keep_e.items())],
            "claims": sum(len(v) for v in keep_e.values()), "claims_all": len(sc), "nodes_all": len(nodes), "small": small,
            "present": sorted({n["cat"] for n in main_nodes if n["kind"] == "cat"}, key=list(CODE).index)}


PAGE = r"""<!doctype html>
<html><head><meta charset="utf-8"><title>Fig. 1</title>
<style>
html, body { margin: 0; padding: 0; background: #fff; }
#fig { width: __W__px; height: __H__px; position: relative; font-family: Arial, Helvetica, sans-serif; color: #000; }
#cy { position: absolute; left: 0; top: 0; width: __W__px; height: __CYH__px; }
#legend { position: absolute; left: 0; bottom: 0; width: __W__px; height: __LEGH__px; border-top: 0.75px solid #000;
  font-size: 8.5px; line-height: 13px; padding-top: 4px; box-sizing: border-box; }
#legend span { white-space: nowrap; margin-right: 10px; display: inline-block; }
#legend svg { vertical-align: -2px; margin-right: 3px; }
</style></head><body>
<div id="fig"><div id="cy"></div><div id="legend"></div></div>
<script id="data" type="application/json">__DATA__</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.30.2/cytoscape.min.js"></script>
<script>
const D = JSON.parse(document.getElementById("data").textContent);
const W = __W__, H = __CYH__, PAD = 5, GAP = 4, FONT = 9, WRAP = 118, NODE = 9;

const cy = cytoscape({ container: document.getElementById("cy"), zoomingEnabled: false, panningEnabled: false, autoungrabify: true,
  elements: [
    ...D.nodes.map(n => ({ group: "nodes", position: { x: 0, y: 0 }, data: { ...n, w: NODE, h: NODE, tv: "bottom", th: "center",
      shape: n.kind === "strike" ? "rectangle" : n.kind === "cat" ? n.shape : "ellipse", fill: n.kind === "cat" ? "#bbb" : "#fff" } })),
    ...D.edges.map((e, i) => ({ group: "edges", data: { id: "arrow" + i, ...e, w: 0.55 + 0.5 * Math.sqrt(e.n) } })),
  ],
  style: [
    { selector: "node", style: { "shape": "data(shape)", "width": "data(w)", "height": "data(h)", "background-color": "data(fill)",
      "border-width": 0.8, "border-color": "#000", "label": "data(label)", "font-family": "Arial, Helvetica, sans-serif",
      "font-size": FONT, "font-style": "italic", "color": "#000", "text-valign": "data(tv)", "text-halign": "data(th)",
      "text-margin-x": "data(mx)", "text-margin-y": "data(my)", "text-wrap": "wrap", "text-max-width": WRAP, "line-height": 1.15,
      "text-background-color": "#fff", "text-background-opacity": 1, "text-background-padding": 0.5, "z-index": 2 } },
    { selector: "node[kind = 'strike']", style: { "font-style": "normal", "font-weight": "bold", "text-valign": "center",
      "text-halign": "center", "text-margin-x": 0, "text-margin-y": 0, "text-background-opacity": 0, "border-width": 1.3 } },
    { selector: "edge", style: { "width": "data(w)", "line-color": "#333", "target-arrow-color": "#333", "target-arrow-shape": "triangle",
      "arrow-scale": 0.55, "curve-style": "straight", "z-index": 1 } },
  ] });
cy.nodes().forEach(n => n.data({ mx: 0, my: 2 }));

// strike events: a box sized to its own text
cy.nodes("[kind = 'strike']").forEach(n => {
  const b = n.boundingBox({ includeNodes: false, includeEdges: false, includeLabels: true });
  n.data({ w: Math.ceil(b.w) + 8, h: Math.ceil(b.h) + 6 });
});

const box = n => n.boundingBox({ includeLabels: true, includeOverlays: false });
const hit = (a, b, g = GAP) => Math.min(a.x2, b.x2) + g > Math.max(a.x1, b.x1) && Math.min(a.y2, b.y2) + g > Math.max(a.y1, b.y1);

// ---- label boxes: measured once per label side, then handled as plain rectangles relative to the node centre ----
const SIDES = {
  bottom: { tv: "bottom", th: "center", mx: 0, my: 2 }, top: { tv: "top", th: "center", mx: 0, my: -2 },
  right: { tv: "center", th: "right", mx: 3, my: 0 }, left: { tv: "center", th: "left", mx: -3, my: 0 },
};
const ns = cy.nodes().toArray(), N = ns.length, idx = new Map(ns.map((n, i) => [n.id(), i]));
const off = ns.map(n => {   // offsets of the node+label box from the node centre, for each side
  const o = {};
  for (const [side, st] of Object.entries(n.data("kind") === "strike" ? { bottom: SIDES.bottom } : SIDES)) {
    n.data(st); n.position({ x: 0, y: 0 });
    const b = box(n); o[side] = { x1: b.x1, y1: b.y1, x2: b.x2, y2: b.y2 };
  }
  return o;
});
const E = cy.edges().toArray().map(e => [idx.get(e.source().id()), idx.get(e.target().id())]);
const nbrs = ns.map(() => []); E.forEach(([a, b]) => { nbrs[a].push(b); nbrs[b].push(a); });
const side = ns.map(() => "bottom");
const X = new Float64Array(N), Y = new Float64Array(N);
const B = i => { const o = off[i][side[i]]; return { x1: X[i] + o.x1, y1: Y[i] + o.y1, x2: X[i] + o.x2, y2: Y[i] + o.y2 }; };
const density = ns.reduce((s, n, i) => { const o = off[i][side[i]]; return s + (o.x2 - o.x1) * (o.y2 - o.y1); }, 0) / (W * H);

// label goes on the side facing away from the node's neighbours (so its own arrows never cross its text)
function chooseSides() {
  for (let i = 0; i < N; i++) {
    if (ns[i].data("kind") === "strike" || !nbrs[i].length) continue;
    let dx = 0, dy = 0; nbrs[i].forEach(j => { dx += X[j] - X[i]; dy += Y[j] - Y[i]; });
    side[i] = Math.abs(dy) >= 0.6 * Math.abs(dx) ? (dy < 0 ? "bottom" : "top") : (dx < 0 ? "right" : "left");
  }
}

// does segment p->q pass through rectangle r (shrunk by m)?
function segHits(px, py, qx, qy, r, m = 0) {
  const x1 = r.x1 - m, x2 = r.x2 + m, y1 = r.y1 - m, y2 = r.y2 + m;
  let t0 = 0, t1 = 1; const dx = qx - px, dy = qy - py;
  for (const [p, q] of [[-dx, px - x1], [dx, x2 - px], [-dy, py - y1], [dy, y2 - py]]) {
    if (p === 0) { if (q < 0) return false; continue; }
    const t = q / p; if (p < 0) { if (t > t1) return false; if (t > t0) t0 = t; } else { if (t < t0) return false; if (t < t1) t1 = t; }
  }
  return t1 - t0 > 0.02;
}

// initial positions: hub-and-spokes from the best-connected node (breadth-first), each node starting beside its parent
function init(rot) {
  const hub = [...Array(N).keys()].sort((a, b) => nbrs[b].length - nbrs[a].length || ns[a].id().localeCompare(ns[b].id()))[0];
  const ang = new Float64Array(N), seen = new Set([hub]), queue = [hub];
  X[hub] = W / 2; Y[hub] = H / 2;
  while (queue.length) {
    const u = queue.shift(), kids = nbrs[u].filter(v => !seen.has(v)).sort((a, b) => ns[a].id().localeCompare(ns[b].id()));
    const spread = u === hub ? 2 * Math.PI : Math.PI * 0.9;
    kids.forEach((v, k) => {
      const a = (u === hub ? -Math.PI / 2 + rot : ang[u] - spread / 2) + spread * (k + 0.5) / kids.length, r = u === hub ? 150 : 90;
      ang[v] = a; X[v] = X[u] + r * Math.cos(a); Y[v] = Y[u] + 1.25 * r * Math.sin(a); seen.add(v); queue.push(v);
    });
  }
}

function step(t, T) {
  const cool = 1 - t / T, FX = new Float64Array(N), FY = new Float64Array(N);
  // springs along arrows
  for (const [a, b] of E) {
    const dx = X[b] - X[a], dy = Y[b] - Y[a], d = Math.hypot(dx, dy) || 1, L = 75;
    const f = 0.09 * (d - L); FX[a] += f * dx / d; FY[a] += f * dy / d; FX[b] -= f * dx / d; FY[b] -= f * dy / d;
  }
  // weak long-range repulsion, and gentle pull toward the page centre
  for (let i = 0; i < N; i++) {
    for (let j = i + 1; j < N; j++) {
      const dx = X[j] - X[i], dy = Y[j] - Y[i], d2 = dx * dx + dy * dy + 25, f = 900 / d2, d = Math.sqrt(d2);
      FX[i] -= f * dx / d; FY[i] -= f * dy / d; FX[j] += f * dx / d; FY[j] += f * dy / d;
    }
    FX[i] += 0.004 * (W / 2 - X[i]); FY[i] += 0.004 * (H / 2 - Y[i]);
  }
  const lim = 6 * cool + 0.5;
  for (let i = 0; i < N; i++) { X[i] += Math.max(-lim, Math.min(lim, FX[i])); Y[i] += Math.max(-lim, Math.min(lim, FY[i])); }
  // arrows push away the boxes they pass through
  for (const [a, b] of E) for (let i = 0; i < N; i++) {
    if (i === a || i === b) continue;
    const r = B(i);
    if (!segHits(X[a], Y[a], X[b], Y[b], r, 1.5)) continue;
    const cx = (r.x1 + r.x2) / 2, cyy = (r.y1 + r.y2) / 2, dx = X[b] - X[a], dy = Y[b] - Y[a], L = Math.hypot(dx, dy) || 1;
    let nx = -dy / L, ny = dx / L; if ((cx - X[a]) * nx + (cyy - Y[a]) * ny < 0) { nx = -nx; ny = -ny; }
    X[i] += 2 * nx; Y[i] += 2 * ny; X[a] -= 0.3 * nx; Y[a] -= 0.3 * ny; X[b] -= 0.3 * nx; Y[b] -= 0.3 * ny;
  }
  separate(); clamp();
}

// hard constraint: no two boxes within GAP of each other (move apart along the cheaper axis)
function separate() {
  for (let pass = 0; pass < 3; pass++) for (let i = 0; i < N; i++) for (let j = i + 1; j < N; j++) {
    const a = B(i), b = B(j);
    const ox = Math.min(a.x2, b.x2) - Math.max(a.x1, b.x1) + GAP, oy = Math.min(a.y2, b.y2) - Math.max(a.y1, b.y1) + GAP;
    if (ox <= 0 || oy <= 0) continue;
    if (ox < oy) { const s = (X[i] + (a.x1 + a.x2 - 2 * X[i]) / 2 < X[j] + (b.x1 + b.x2 - 2 * X[j]) / 2 ? -1 : 1) * ox / 2; X[i] += s; X[j] -= s; }
    else { const s = ((a.y1 + a.y2) / 2 < (b.y1 + b.y2) / 2 ? -1 : 1) * oy / 2; Y[i] += s; Y[j] -= s; }
  }
}
function clamp() {
  for (let i = 0; i < N; i++) {
    const r = B(i);
    if (r.x1 < PAD) X[i] += PAD - r.x1; if (r.x2 > W - PAD) X[i] -= r.x2 - (W - PAD);
    if (r.y1 < PAD) Y[i] += PAD - r.y1; if (r.y2 > H - PAD) Y[i] -= r.y2 - (H - PAD);
  }
}

// a node's own shape (the strike box, or the small symbol), slightly enlarged: arrows must never pass through one
const S = i => { const w = ns[i].data("w") / 2 + 2, h = ns[i].data("h") / 2 + 2; return { x1: X[i] - w, y1: Y[i] - h, x2: X[i] + w, y2: Y[i] + h }; };
function nodeCost(i) {
  const r = B(i); let c = 0;
  if (r.x1 < PAD || r.y1 < PAD || r.x2 > W - PAD || r.y2 > H - PAD) c += 1000;
  for (let j = 0; j < N; j++) if (j !== i) {
    const q = B(j);
    if (Math.min(r.x2, q.x2) + GAP > Math.max(r.x1, q.x1) && Math.min(r.y2, q.y2) + GAP > Math.max(r.y1, q.y1)) c += 1000;
  }
  const through = (a, b, j) => segHits(X[a], Y[a], X[b], Y[b], S(j), 0) ? 500 : segHits(X[a], Y[a], X[b], Y[b], B(j), 1) ? 10 : 0;
  for (const [a, b] of E) {
    if (a !== i && b !== i) { c += through(a, b, i); continue; }
    for (let j = 0; j < N; j++) if (j !== a && j !== b) c += through(a, b, j);
  }
  for (const [a, b] of E) if (a === i || b === i) c += 0.02 * Math.hypot(X[b] - X[a], Y[b] - Y[a]);   // prefer short arrows
  return c;
}

function layoutOnce() {
const T = 2500;
for (let t = 0; t < T; t++) { if (t % 50 === 0) chooseSides(); step(t, T); }
chooseSides();
for (let t = 0; t < 400; t++) { separate(); clamp(); }   // remove remaining overlaps without forces

// clean-up search: each node tries nearby positions and all label sides, keeping whatever lowers
// (overlaps, out-of-page boxes and arrows through nodes, weighted heavily) + (arrows behind labels, lightly). Deterministic.
for (let pass = 0; pass < 30; pass++) {
  let improved = 0;
  for (let i = 0; i < N; i++) {
    const sides = ns[i].data("kind") === "strike" ? ["bottom"] : Object.keys(SIDES);
    let bestC = nodeCost(i), bx = X[i], by = Y[i], bs = side[i];
    const x0 = X[i], y0 = Y[i], s0 = side[i];
    for (const s of sides) for (let dx = -72; dx <= 72; dx += 6) for (let dy = -72; dy <= 72; dy += 6) {
      X[i] = x0 + dx; Y[i] = y0 + dy; side[i] = s;
      const c = nodeCost(i);
      if (c < bestC - 1e-9) { bestC = c; bx = X[i]; by = Y[i]; bs = s; }
    }
    if (bx !== x0 || by !== y0 || bs !== s0) improved++;
    X[i] = bx; Y[i] = by; side[i] = bs;
  }
  if (!improved) break;
}
}

// several deterministic starting rotations; keep the cleanest result
let bestScore = Infinity, best = null;
for (let v = 0; v < 12; v++) {
  init(v * Math.PI / 6); layoutOnce();
  let sc = 0; for (let i = 0; i < N; i++) sc += nodeCost(i);
  if (sc < bestScore) { bestScore = sc; best = { X: X.slice(), Y: Y.slice(), side: side.slice(), v }; }
}
X.set(best.X); Y.set(best.Y); best.side.forEach((x, i) => side[i] = x);
cy.batch(() => ns.forEach((n, i) => { n.data(n.data("kind") === "strike" ? {} : SIDES[side[i]]); n.position({ x: X[i], y: Y[i] }); }));

// does the straight arrow pass through rectangle b (other than its own two end nodes)?
const arrowHits = (e, n, b, m = 0) => n !== e.source() && n !== e.target() &&
  segHits(e.source().position().x, e.source().position().y, e.target().position().x, e.target().position().y, b, m);
const choices = [{ density: +density.toFixed(3), start: best.v }];

function report() {
  const ns = cy.nodes().toArray(), B = ns.map(box);
  const pairs = [];
  for (let i = 0; i < ns.length; i++) for (let j = i + 1; j < ns.length; j++) if (hit(B[i], B[j], 0)) pairs.push([ns[i].id(), ns[j].id()]);
  const pr = { ov: 0, cross: 0 };
  for (let i = 0; i < ns.length; i++) for (let j = i + 1; j < ns.length; j++) if (hit(B[i], B[j])) pr.ov++;
  const shape = n => { const p = n.position(), w = n.data("w") / 2, h = n.data("h") / 2; return { x1: p.x - w, y1: p.y - h, x2: p.x + w, y2: p.y + h }; };
  const through = [], behind = [];
  cy.edges().forEach(e => ns.forEach((n, k) => {
    const what = [e.source().data("label").slice(0, 28), e.target().data("label").slice(0, 28), n.data("label").slice(0, 28)];
    if (arrowHits(e, n, shape(n), 0.5)) through.push(what); else if (arrowHits(e, n, B[k], -0.5)) behind.push(what);
  }));
  return { nodes: ns.length, edges: cy.edges().length, overlaps: pairs.length, overlapPairs: pairs.slice(0, 10),
    tooClose: pr.ov, arrowsThroughNodes: through.length, throughList: through, arrowsBehindLabels: behind.length, outOfBounds: B.filter(b => b.x1 < 0 || b.y1 < 0 || b.x2 > W || b.y2 > H).length,
    layout: choices[0], fontPt: +(FONT * 72 / 96).toFixed(2) };
}

// legend: only the symbols that appear in this figure
const glyph = shape => {
  const ring = (n, r, rot = -90) => Array.from({ length: n }, (_, i) => { const a = (rot + 360 * i / n) * Math.PI / 180;
    return `${(6 + r * Math.cos(a)).toFixed(1)},${(6 + r * Math.sin(a)).toFixed(1)}`; }).join(" ");
  const star = Array.from({ length: 10 }, (_, i) => { const a = (-90 + 36 * i) * Math.PI / 180, r = i % 2 ? 2.4 : 5.6;
    return `${(6 + r * Math.cos(a)).toFixed(1)},${(6 + r * Math.sin(a)).toFixed(1)}`; }).join(" ");
  const p = { triangle: ring(3, 5.8), diamond: ring(4, 5.6), pentagon: ring(5, 5.6), hexagon: ring(6, 5.6, 0), octagon: ring(8, 5.6, 22.5),
    star, vee: "0.5,0.5 6,4.5 11.5,0.5 6,11.5" }[shape];
  const inner = shape === "circle" ? '<circle cx="6" cy="6" r="4.5" fill="#fff" stroke="#000" stroke-width="0.8"/>'
    : `<polygon points="${p}" fill="#bbb" stroke="#000" stroke-width="0.8"/>`;
  return `<svg width="12" height="12">${inner}</svg>`;
};
const item = (svg, text) => `<span>${svg}${text}</span>`;
document.getElementById("legend").innerHTML =
  item('<svg width="20" height="12"><rect x="1" y="1.5" width="18" height="9" fill="#fff" stroke="#000" stroke-width="1.3"/></svg>',
       "<b>Strike event</b>: the effect in a claim about the Hongkong strike") +
  item(glyph("circle"), "Other cause event") +
  item('<svg width="22" height="12"><line x1="1" y1="6" x2="16" y2="6" stroke="#333" stroke-width="1.1"/><polygon points="15,3.2 21,6 15,8.8" fill="#333"/></svg>',
       "Causal claim (thicker = more claims)") + "<br>" +
  D.present.map(k => item(glyph(D.shape[k]), `${D.code[k]} · ${D.name[k]}`)).join("") +
  "<span>Cause events whose cluster matches a category (θ = 0.65)</span>";

document.body.setAttribute("data-report", JSON.stringify(report()));
</script></body></html>
"""


def main():
    d = data()
    d.update(code=CODE, name=NAME, shape=SHAPE)
    html = (PAGE.replace("__DATA__", json.dumps(d, ensure_ascii=False).replace("</", "<\\/"))
            .replace("__W__", str(W)).replace("__H__", str(H)).replace("__CYH__", str(H - LEGEND_H))
            .replace("__LEGH__", str(LEGEND_H)))
    FIGS.mkdir(parents=True, exist_ok=True)
    with open(FIGS / "fig1_small_groups.csv", "w", newline="", encoding="utf-8") as fh:   # the groups not drawn in Fig. 1
        w = csv.DictWriter(fh, fieldnames=["group", "cause", "effect (strike event)", "claims"])
        w.writeheader(); w.writerows(d["small"])
    src = FIGS / "fig1.html"
    src.write_text(html, encoding="utf-8")
    url = src.resolve().as_uri()
    dom = subprocess.run([str(EDGE), "--headless=new", "--disable-gpu", "--virtual-time-budget=60000", "--dump-dom", url],
                         capture_output=True, text=True, encoding="utf-8", timeout=300).stdout
    m = re.search(r'data-report="([^"]*)"', dom)
    rep = json.loads(m.group(1).replace("&quot;", '"')) if m else {"error": "no report (layout failed?)"}
    print(json.dumps(rep, indent=1))
    png = FIGS / "fig1.png"
    subprocess.run([str(EDGE), "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--window-size={W},{H}",
                    f"--force-device-scale-factor={DPI / CSS_DPI}", "--virtual-time-budget=60000",
                    f"--screenshot={png}", url], capture_output=True, timeout=300)
    print(f"{png}  ({d['claims']} of {d['claims_all']} claims, {len(d['nodes'])} of {d['nodes_all']} nodes, {len(d['edges'])} arrows)")
    if "error" in rep or rep["overlaps"] or rep["outOfBounds"] or rep["arrowsThroughNodes"]:
        sys.exit("NOT ACCEPTED: overlapping labels, out-of-bounds boxes or arrows through nodes remain")


if __name__ == "__main__":
    main()
