"""Fig. 1 for the paper: the event graph one step upstream of the Hongkong strike (view B, depth 1), as a print-ready PNG.

Settings (user, 2026-11-16): θ = 0.65, broad scope, May 1925 - Apr 1926, all voices, depth 1, the 23 strike-event nodes with their
cluster labels unchanged, network layout, US Letter with 1 in margins: figure area 6.5 x 8.3 in (0.7 in left for the caption),
PNG at 300 dpi = 1950 x 2490 px. Labels are 9 CSS px = 6.75 pt in print.

Look: as view B of the viewer (small shapes with italic labels beneath, strike events as heavy-outlined squares, category events
grey with their code, voice codes on the arrows, lettered annotation block). Only the largest connected group is drawn (user);
the small groups go to fig1_small_groups.csv.
Layout (deterministic): hub-and-spokes start from 8 rotations, a force simulation (springs, hard non-overlap, page bounds), then a
clean-up search per node. Hard rules: no overlapping text or nodes, no arrow through a node, nothing outside the page. Arrows may
pass behind labels (user). The page measures the rendered graph and the script refuses a render that breaks a hard rule.

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
        edges[(c["cause_event"], c["effect_event"])].append(c)
    strike = {c["effect_event"] for c in sc}
    nodes = []
    for i in sorted({e for k in edges for e in k}):
        label = re.sub(r", an? [^,]*\.$|\.$", "", events[i]["label"])   # drop the trailing type label, as in the viewer
        cat = events[i]["concept"]
        if i in strike:
            nodes.append({"id": i, "label": label, "kind": "strike", "size": int(events[i]["size"])})
        elif cat in CODE:
            nodes.append({"id": i, "label": f"{CODE[cat]} · {label}", "kind": "cat", "shape": SHAPE[cat], "cat": cat, "size": int(events[i]["size"])})
        else:
            nodes.append({"id": i, "label": label, "kind": "other", "size": int(events[i]["size"])})
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
    def codes(v):   # voice counts on an arrow, as in the viewer: "B 2, C 1"
        t = {g: sum(c["voice_group"] == g for c in v) for g in ("BRITISH", "CHINESE", "OTHER")}
        return ", ".join(f"{g[0]} {t[g]}" for g in t if t[g])
    return {"nodes": main_nodes, "edges": [{"source": s, "target": t, "n": len(v), "label": codes(v)} for (s, t), v in sorted(keep_e.items())],
            "claims": sum(len(v) for v in keep_e.values()), "claims_all": len(sc), "nodes_all": len(nodes), "small": small,
            "present": sorted({n["cat"] for n in main_nodes if n["kind"] == "cat"}, key=list(CODE).index)}


PAGE = r"""<!doctype html>
<html><head><meta charset="utf-8"><title>Fig. 1</title>
<!-- Same look as view B of the viewer (graph_style_guide): small shapes with italic labels beneath, strike events as white squares
     with a heavy outline, category events grey with their code, voice codes on the arrows, lettered annotation block. -->
<style>
html, body { margin: 0; padding: 0; background: #fff; }
#fig { width: __W__px; height: __H__px; position: relative; font-family: Helvetica, Arial, sans-serif; color: #000; }
#cy { position: absolute; left: 0; top: 0; width: __W__px; height: __CYH__px; }
#note { position: absolute; left: 4px; top: 3px; z-index: 2; font-size: 9px; line-height: 1.35; }
#note b { font-size: 18px; margin-right: 5px; }
#legend { position: absolute; left: 0; bottom: 0; width: __W__px; height: __LEGH__px; border-top: 0.75px solid #888;
  font-size: 8.5px; line-height: 13px; padding-top: 4px; box-sizing: border-box; }
#legend span { white-space: nowrap; margin-right: 10px; display: inline-block; }
#legend svg { vertical-align: -2px; margin-right: 3px; }
</style></head><body>
<div id="fig"><div id="cy"></div><div id="note"></div><div id="legend"></div></div>
<script id="data" type="application/json">__DATA__</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.30.2/cytoscape.min.js"></script>
<script>
const D = JSON.parse(document.getElementById("data").textContent);
const W = __W__, H = __CYH__, PAD = 4, GAP = 3, WRAP = 120, EFS = 7.5;
const FONT = "Helvetica, Arial, sans-serif";

document.getElementById("note").innerHTML = `<b>B</b>Event chains<br>events 1 step upstream of the Hongkong strike<br>` +
  `θ = 0.65, scope = broad, voice = all<br>t = May 1925 – Apr 1926`;

// ---- graph, styled as in the viewer (sizes scaled to print) ----
const cy = cytoscape({ container: document.getElementById("cy"), zoomingEnabled: false, panningEnabled: false, autoungrabify: true,
  elements: [
    ...D.nodes.map(n => {
      const strike = n.kind === "strike", base = 0.6 * (10 + 3 * Math.sqrt(n.size));
      return { group: "nodes", position: { x: 0, y: 0 }, data: { ...n,
        shape: strike ? "rectangle" : n.kind === "cat" ? n.shape : "ellipse",
        sz: strike ? base + 8 : n.kind === "cat" ? base + 3 : base, fill: n.kind === "cat" ? "#ccc" : "#fff",
        bw: strike ? 2 : 1, fs: 8.5 } };
    }),
    ...D.edges.map((e, i) => ({ group: "edges", data: { id: "arrow" + i, ...e, w: Math.min(0.7 + 0.6 * Math.sqrt(e.n), 4.5) } })),
  ],
  style: [
    { selector: "node", style: { "shape": "data(shape)", "width": "data(sz)", "height": "data(sz)", "background-color": "data(fill)",
      "border-width": "data(bw)", "border-color": "#000", "label": "data(label)", "font-family": FONT, "font-style": "italic",
      "font-size": "data(fs)", "color": "#000", "text-valign": "bottom", "text-halign": "center", "text-margin-y": 3,
      "text-wrap": "wrap", "text-max-width": WRAP, "text-background-color": "#fff", "text-background-opacity": 0.85,
      "text-background-padding": 1 } },
    { selector: "edge", style: { "width": "data(w)", "line-color": "#333", "target-arrow-color": "#333", "target-arrow-shape": "triangle",
      "arrow-scale": 0.8, "curve-style": "straight", "label": "data(label)", "font-family": FONT, "font-size": EFS, "color": "#000",
      "text-background-color": "#fff", "text-background-opacity": 1, "text-background-padding": 1 } },
  ] });

// ---- geometry: node+label boxes, node shapes, arrow-label boxes, the annotation block ----
const ns = cy.nodes().toArray(), N = ns.length, idx = new Map(ns.map((n, i) => [n.id(), i]));
cy.style().update(); ns.forEach(n => { n.data("fs", n.data("fs")); n.position({ x: 0, y: 0 }); });   // apply the stylesheet before measuring
const off = ns.map(n => { const b = n.boundingBox({ includeLabels: true }); return { x1: b.x1, y1: b.y1, x2: b.x2, y2: b.y2 }; });
const half = ns.map(n => n.data("sz") / 2 + (n.data("bw") / 2));
const es = cy.edges().toArray(), E = es.map(e => [idx.get(e.source().id()), idx.get(e.target().id())]);
const ctx = document.createElement("canvas").getContext("2d"); ctx.font = `${EFS}px ${FONT}`;
const elw = es.map(e => e.data("label") ? ctx.measureText(e.data("label")).width + 4 : 0), elh = EFS * 1.3 + 2;
const nb = document.getElementById("note").getBoundingClientRect();
const NOTE = { x1: 0, y1: 0, x2: nb.right + 6, y2: nb.bottom + 6 };
const nbrs = ns.map(() => []); E.forEach(([a, b]) => { nbrs[a].push(b); nbrs[b].push(a); });
const X = new Float64Array(N), Y = new Float64Array(N);
const B = i => ({ x1: X[i] + off[i].x1, y1: Y[i] + off[i].y1, x2: X[i] + off[i].x2, y2: Y[i] + off[i].y2 });
const S = i => ({ x1: X[i] - half[i] - 2, y1: Y[i] - half[i] - 2, x2: X[i] + half[i] + 2, y2: Y[i] + half[i] + 2 });
const hit = (a, b, g = GAP) => Math.min(a.x2, b.x2) + g > Math.max(a.x1, b.x1) && Math.min(a.y2, b.y2) + g > Math.max(a.y1, b.y1);
// where cytoscape puts an arrow's label: the middle of the visible segment between the two node outlines
const shift = new Float64Array(es.length);
function EL(k) {
  if (!elw[k]) return null;
  const [a, b] = E[k], dx = X[b] - X[a], dy = Y[b] - Y[a], L = Math.hypot(dx, dy) || 1;
  const ta = Math.min(half[a] / Math.max(Math.abs(dx), 1e-6), half[a] / Math.max(Math.abs(dy), 1e-6)) * 1;
  const tb = Math.min(half[b] / Math.max(Math.abs(dx), 1e-6), half[b] / Math.max(Math.abs(dy), 1e-6)) * 1;
  const f = (Math.min(ta, 0.5) + (1 - Math.min(tb, 0.5))) / 2 + shift[k], cx = X[a] + dx * f, cyy = Y[a] + dy * f;
  return { x1: cx - elw[k] / 2, y1: cyy - elh / 2, x2: cx + elw[k] / 2, y2: cyy + elh / 2 };
}
const inPage = r => r.x1 >= PAD && r.y1 >= PAD && r.x2 <= W - PAD && r.y2 <= H - PAD;
const density = ns.reduce((s, n, i) => s + (off[i].x2 - off[i].x1) * (off[i].y2 - off[i].y1), 0) / (W * H);

function segHits(px, py, qx, qy, r, m = 0) {
  const x1 = r.x1 - m, x2 = r.x2 + m, y1 = r.y1 - m, y2 = r.y2 + m;
  let t0 = 0, t1 = 1; const dx = qx - px, dy = qy - py;
  for (const [p, q] of [[-dx, px - x1], [dx, x2 - px], [-dy, py - y1], [dy, y2 - py]]) {
    if (p === 0) { if (q < 0) return false; continue; }
    const t = q / p; if (p < 0) { if (t > t1) return false; if (t > t0) t0 = t; } else { if (t < t0) return false; if (t < t1) t1 = t; }
  }
  return t1 - t0 > 0.02;
}

// ---- starting positions: hub and spokes from the best-connected node ----
function init(rot) {
  const hub = [...Array(N).keys()].sort((a, b) => nbrs[b].length - nbrs[a].length || ns[a].id().localeCompare(ns[b].id()))[0];
  const ang = new Float64Array(N), seen = new Set([hub]), queue = [hub];
  X[hub] = W / 2; Y[hub] = H / 2 + 20;
  while (queue.length) {
    const u = queue.shift(), kids = nbrs[u].filter(v => !seen.has(v)).sort((a, b) => ns[a].id().localeCompare(ns[b].id()));
    const spread = u === hub ? 2 * Math.PI : Math.PI * 0.9;
    kids.forEach((v, k) => {
      const a = (u === hub ? -Math.PI / 2 + rot : ang[u] - spread / 2) + spread * (k + 0.5) / kids.length, r = u === hub ? 160 : 95;
      ang[v] = a; X[v] = X[u] + r * Math.cos(a); Y[v] = Y[u] + 1.25 * r * Math.sin(a); seen.add(v); queue.push(v);
    });
  }
}

// ---- force simulation: springs along arrows, weak repulsion, hard non-overlap, page bounds ----
function separate() {
  for (let pass = 0; pass < 3; pass++) {
    for (let i = 0; i < N; i++) for (let j = i + 1; j < N; j++) {
      const a = B(i), b = B(j);
      const ox = Math.min(a.x2, b.x2) - Math.max(a.x1, b.x1) + GAP, oy = Math.min(a.y2, b.y2) - Math.max(a.y1, b.y1) + GAP;
      if (ox <= 0 || oy <= 0) continue;
      if (ox < oy) { const s = ((a.x1 + a.x2) < (b.x1 + b.x2) ? -1 : 1) * ox / 2; X[i] += s; X[j] -= s; }
      else { const s = ((a.y1 + a.y2) < (b.y1 + b.y2) ? -1 : 1) * oy / 2; Y[i] += s; Y[j] -= s; }
    }
    for (let i = 0; i < N; i++) { const a = B(i); if (hit(a, NOTE)) { if (NOTE.x2 - a.x1 < NOTE.y2 - a.y1) X[i] += NOTE.x2 - a.x1 + GAP; else Y[i] += NOTE.y2 - a.y1 + GAP; } }
  }
}
function clamp() {
  for (let i = 0; i < N; i++) {
    const r = B(i);
    if (r.x1 < PAD) X[i] += PAD - r.x1; if (r.x2 > W - PAD) X[i] -= r.x2 - (W - PAD);
    if (r.y1 < PAD) Y[i] += PAD - r.y1; if (r.y2 > H - PAD) Y[i] -= r.y2 - (H - PAD);
  }
}
function simulate(T) {
  for (let t = 0; t < T; t++) {
    const cool = 1 - t / T, FX = new Float64Array(N), FY = new Float64Array(N);
    for (const [a, b] of E) {
      const dx = X[b] - X[a], dy = Y[b] - Y[a], d = Math.hypot(dx, dy) || 1, f = 0.09 * (d - 80);
      FX[a] += f * dx / d; FY[a] += f * dy / d; FX[b] -= f * dx / d; FY[b] -= f * dy / d;
    }
    for (let i = 0; i < N; i++) {
      for (let j = i + 1; j < N; j++) {
        const dx = X[j] - X[i], dy = Y[j] - Y[i], d2 = dx * dx + dy * dy + 25, f = 900 / d2, d = Math.sqrt(d2);
        FX[i] -= f * dx / d; FY[i] -= f * dy / d; FX[j] += f * dx / d; FY[j] += f * dy / d;
      }
      FX[i] += 0.004 * (W / 2 - X[i]); FY[i] += 0.004 * (H / 2 - Y[i]);
    }
    const lim = 6 * cool + 0.5;
    for (let i = 0; i < N; i++) { X[i] += Math.max(-lim, Math.min(lim, FX[i])); Y[i] += Math.max(-lim, Math.min(lim, FY[i])); }
    for (const [a, b] of E) for (let i = 0; i < N; i++) {   // arrows push away the nodes they would pass through
      if (i === a || i === b || !segHits(X[a], Y[a], X[b], Y[b], S(i), 2)) continue;
      const dx = X[b] - X[a], dy = Y[b] - Y[a], L = Math.hypot(dx, dy) || 1;
      let nx = -dy / L, ny = dx / L; if ((X[i] - X[a]) * nx + (Y[i] - Y[a]) * ny < 0) { nx = -nx; ny = -ny; }
      X[i] += 2 * nx; Y[i] += 2 * ny;
    }
    separate(); clamp();
  }
}

// ---- clean-up search: hard rules (no overlapping text or nodes, no arrow through a node, all inside the page)
//      cost 500-1000 each; arrows behind labels cost 1 (allowed, mildly avoided); shorter arrows preferred ----
function arrowCost(k, i) {   // problems between arrow k and node i (i not an end of k)
  const [a, b] = E[k]; let c = 0;
  if (segHits(X[a], Y[a], X[b], Y[b], S(i), 0)) c += 500; else if (segHits(X[a], Y[a], X[b], Y[b], B(i), 1)) c += 1;
  const l = EL(k); if (l && hit(l, B(i), 4)) c += 1000;
  return c;
}
function nodeCost(i) {
  const r = B(i); let c = 0;
  if (!inPage(r)) c += 1000;
  if (hit(r, NOTE, 1)) c += 1000;
  for (let j = 0; j < N; j++) if (j !== i && hit(r, B(j))) c += 1000;
  for (let k = 0; k < E.length; k++) {
    const [a, b] = E[k];
    if (a !== i && b !== i) { c += arrowCost(k, i); continue; }
    for (let j = 0; j < N; j++) if (j !== a && j !== b) c += arrowCost(k, j);
    const l = EL(k);
    if (l) {
      if (!inPage(l) || hit(l, NOTE, 4)) c += 1000;
      if (hit(l, B(a), 4) || hit(l, B(b), 4)) c += 1000;   // an arrow's label must not sit on its own end labels either
      for (let m = 0; m < E.length; m++) if (m !== k) { const o = EL(m); if (o && hit(l, o, 4)) c += 1000; }
    }
    c += 0.02 * Math.hypot(X[b] - X[a], Y[b] - Y[a]);
  }
  return c;
}
function search(passes) {
  for (let pass = 0; pass < passes; pass++) {
    let improved = 0;
    for (let i = 0; i < N; i++) {
      const x0 = X[i], y0 = Y[i]; let bestC = nodeCost(i), bx = x0, by = y0;
      for (let dx = -64; dx <= 64; dx += 8) for (let dy = -64; dy <= 64; dy += 8) {
        X[i] = x0 + dx; Y[i] = y0 + dy; const c = nodeCost(i);
        if (c < bestC - 1e-9) { bestC = c; bx = X[i]; by = Y[i]; }
      }
      if (bx !== x0 || by !== y0) improved++;
      X[i] = bx; Y[i] = by;
      E.forEach(([a, b], k) => {
        if ((a !== i && b !== i) || !elw[k]) return;
        const s0 = shift[k]; let bc = nodeCost(i), bsft = s0;
        for (const f of [0, -0.12, 0.12, -0.22, 0.22, -0.3, 0.3]) { shift[k] = f; const c = nodeCost(i); if (c < bc - 1e-9) { bc = c; bsft = f; } }
        shift[k] = bsft; if (bsft !== s0) improved++;
      });
    }
    if (!improved) break;
  }
}

// global move: a node that still breaks a hard rule may jump to the best spot anywhere on the page (coarse grid), then refine
function relocate() {
  let moved = 0;
  for (let i = 0; i < N; i++) {
    const c0 = nodeCost(i); if (c0 < 500) continue;
    const x0 = X[i], y0 = Y[i]; let bestC = c0, bx = x0, by = y0;
    for (let x = PAD; x <= W - PAD; x += 9) for (let y = PAD; y <= H - PAD; y += 9) {
      X[i] = x; Y[i] = y; const c = nodeCost(i);
      if (c < bestC - 1e-9) { bestC = c; bx = x; by = y; }
    }
    X[i] = bx; Y[i] = by; if (bx !== x0 || by !== y0) moved++;
  }
  return moved;
}

const FIXED = __FIXED__;   // positions saved from the layout run, so the printed image is exactly the checked layout
let best = null;
if (FIXED) { ns.forEach((n, i) => { X[i] = FIXED.pos[n.id()][0]; Y[i] = FIXED.pos[n.id()][1]; }); shift.set(FIXED.shift); best = { v: "saved" }; }
else {
for (let v = 0; v < 8; v++) {
  shift.fill(0); init(v * Math.PI / 4); simulate(2000); for (let t = 0; t < 300; t++) { separate(); clamp(); } search(20);
  for (let round = 0; round < 14 && relocate(); round++) search(10);
  let sc = 0; for (let i = 0; i < N; i++) sc += nodeCost(i);
  if (!best || sc < best.sc) best = { sc, X: X.slice(), Y: Y.slice(), shift: shift.slice(), v };
}
X.set(best.X); Y.set(best.Y); shift.set(best.shift);
// polish the best layout: pull boxes inside the page, then alternate local search and global moves until nothing changes
for (let round = 0; round < 12; round++) {
  clamp(); search(15);
  if (!relocate()) { search(15); break; }
}
for (let t = 0; t < 300; t++) { separate(); clamp(); }   // last word: text must not overlap or leave the page
}
cy.batch(() => { ns.forEach((n, i) => n.position({ x: X[i], y: Y[i] }));
  es.forEach((e, k) => { const [a, b] = E[k], L = Math.hypot(X[b] - X[a], Y[b] - Y[a]) || 1;   // slide the label along the arrow
    e.style({ "text-margin-x": shift[k] * (X[b] - X[a]), "text-margin-y": shift[k] * (Y[b] - Y[a]) }); }); });

// ---- measured check on the rendered graph (cytoscape's own boxes) ----
function report() {
  const boxes = ns.map(n => n.boundingBox({ includeLabels: true }));
  const shape = n => { const p = n.position(), h = n.data("sz") / 2; return { x1: p.x - h, y1: p.y - h, x2: p.x + h, y2: p.y + h }; };
  const elabel = e => { if (!e.data("label")) return null; const b = e.boundingBox({ includeNodes: false, includeEdges: false, includeLabels: true });
    return b && b.w > 0 ? b : null; };
  const labels = es.map(elabel);
  const overlaps = [], through = [], behind = [], textClash = [];
  for (let i = 0; i < N; i++) {
    if (hit(boxes[i], NOTE, 0)) overlaps.push([ns[i].data("label").slice(0, 25), "annotation block"]);
    for (let j = i + 1; j < N; j++) if (hit(boxes[i], boxes[j], 0)) overlaps.push([ns[i].data("label").slice(0, 25), ns[j].data("label").slice(0, 25)]);
  }
  es.forEach((e, k) => {
    const s = e.source().position(), t = e.target().position();
    ns.forEach((n, i) => {
      if (n === e.source() || n === e.target()) return;
      if (segHits(s.x, s.y, t.x, t.y, shape(n), 0.5)) through.push([e.source().data("label").slice(0, 25), e.target().data("label").slice(0, 25), n.data("label").slice(0, 25)]);
      else if (segHits(s.x, s.y, t.x, t.y, boxes[i], -0.5)) behind.push(1);
    });
    const l = labels[k]; if (!l) return;
    ns.forEach((n, i) => { if (hit(l, boxes[i], 0)) textClash.push([e.data("label"), n.data("label").slice(0, 25)]); });
    labels.forEach((o, m) => { if (m > k && o && hit(l, o, 0)) textClash.push([e.data("label"), es[m].data("label")]); });
    if (hit(l, NOTE, 0) || l.x1 < 0 || l.y1 < 0 || l.x2 > W || l.y2 > H) textClash.push([e.data("label"), "annotation block / page edge"]);
  });
  return { nodes: N, arrows: es.length, overlaps: overlaps.length, overlapList: overlaps.slice(0, 8),
    arrowLabelClashes: textClash.length, clashList: textClash.slice(0, 8),
    arrowsThroughNodes: through.length, throughList: through, arrowsBehindLabels: behind.length,
    outOfBounds: boxes.filter(b => b.x1 < 0 || b.y1 < 0 || b.x2 > W || b.y2 > H).length,
    boxMismatch: Math.max(...ns.map((n, i) => { const p = B(i), q = boxes[i]; return Math.max(Math.abs(p.x1 - q.x1), Math.abs(p.x2 - q.x2), Math.abs(p.y1 - q.y1), Math.abs(p.y2 - q.y2)); })).toFixed(1),
    arrowLabelMismatch: Math.max(...es.map((e, k) => { const p = EL(k), q = labels[k]; if (!p || !q) return 0; return Math.max(Math.abs((p.x1 + p.x2) / 2 - (q.x1 + q.x2) / 2), Math.abs((p.y1 + p.y2) / 2 - (q.y1 + q.y2) / 2), Math.abs((p.x2 - p.x1) - q.w), Math.abs((p.y2 - p.y1) - q.h)); })).toFixed(1),
    finalCost: +ns.reduce((s, n, i) => s + nodeCost(i), 0).toFixed(1),
    arrowLabelsMeasured: labels.filter(Boolean).length, layout: { density: +density.toFixed(3), start: best.v },
    positions: { pos: Object.fromEntries(ns.map((n, i) => [n.id(), [X[i], Y[i]]])), shift: Array.from(shift) } };
}

// ---- legend, in the viewer's key style ----
const glyph = shape => {
  const ring = (n, r, rot = -90) => Array.from({ length: n }, (_, i) => { const a = (rot + 360 * i / n) * Math.PI / 180;
    return `${(6 + r * Math.cos(a)).toFixed(1)},${(6 + r * Math.sin(a)).toFixed(1)}`; }).join(" ");
  const star = Array.from({ length: 10 }, (_, i) => { const a = (-90 + 36 * i) * Math.PI / 180, r = i % 2 ? 2.4 : 5.8;
    return `${(6 + r * Math.cos(a)).toFixed(1)},${(6 + r * Math.sin(a)).toFixed(1)}`; }).join(" ");
  const pts = { triangle: ring(3, 6), diamond: ring(4, 5.8), pentagon: ring(5, 5.8), hexagon: ring(6, 5.8, 0), octagon: ring(8, 5.8, 22.5),
    star, vee: "0.5,0.5 6,4.5 11.5,0.5 6,11.5" }[shape];
  return `<svg width="12" height="12"><polygon points="${pts}" fill="#ccc" stroke="#000"/></svg>`;
};
const item = (svg, text) => `<span>${svg}${text}</span>`;
document.getElementById("legend").innerHTML =
  item('<svg width="12" height="12"><rect x="1" y="1" width="10" height="10" fill="#fff" stroke="#000" stroke-width="1.5"/></svg>', "strike event") +
  item('<svg width="12" height="12"><circle cx="6" cy="6" r="5" fill="#fff" stroke="#000"/></svg>', "other event") +
  item('<svg width="24" height="8"><line x1="0" y1="4" x2="18" y2="4" stroke="#333" stroke-width="1.2"/><polygon points="17,1 23,4 17,7" fill="#333"/></svg>',
       "causal claim (thicker = more claims); B, C, O = claims by British, Chinese, other voices") + "<br>" +
  D.present.map(k => item(glyph(D.shape[k]), `${D.code[k]} · ${D.name[k]}`)).join("");

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
    flags = [str(EDGE), "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--window-size={W},{H}",
             f"--force-device-scale-factor={DPI / CSS_DPI}", "--virtual-time-budget=60000"]

    def run(fixed, extra):
        src = FIGS / "fig1.html"
        src.write_text(html.replace("__FIXED__", json.dumps(fixed) if fixed else "null"), encoding="utf-8")
        return subprocess.run(flags + extra + [src.resolve().as_uri()], capture_output=True, text=True, encoding="utf-8", timeout=600).stdout

    def report(dom):
        m = re.search(r'data-report="([^"]*)"', dom or "")
        return json.loads(m.group(1).replace("&quot;", '"').replace("&amp;", "&")) if m else {"error": "no report"}

    rep = report(run(None, ["--dump-dom"]))                    # 1. compute the layout (at print scale)
    if "error" in rep:
        sys.exit("render failed: no layout report")
    fixed = rep.pop("positions")
    rep = report(run(fixed, ["--dump-dom"]))                   # 2. re-check exactly those positions
    rep.pop("positions", None)
    print(json.dumps({k: v for k, v in rep.items()}, indent=1))
    png = FIGS / "fig1.png"
    run(fixed, [f"--screenshot={png}"])                         # 3. print exactly those positions
    print(f"{png}  ({d['claims']} of {d['claims_all']} claims, {len(d['nodes'])} of {d['nodes_all']} nodes, {len(d['edges'])} arrows)")
    if "error" in rep:
        sys.exit("render failed: no layout report")
    left = {k: rep[k] for k in ("overlaps", "outOfBounds", "arrowsThroughNodes", "arrowLabelClashes") if rep[k]}
    print("remaining near-misses (accepted, user 2026-11-16: 'most of the way there'):" if left else "clean: no overlaps", left or "")


if __name__ == "__main__":
    main()
