"""
Generators for Step 2 of the China Strike Causal Knowledge Graph.

Step 2 Focus:
- The 16 vocabulary terms are visibly grouped into 4 distinct thematic clusters (A, B, C, D).
- Visible cluster boundary bubbles, distinct cluster color palettes, and overall cluster header labels.
- Layout foreshadows the causal flow: A (top-left) & B (bottom-left) -> C (center) -> D (right).
- Full white background aesthetic matching project standards.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from .data import TOPICS, get_step2_nodes, get_step2_intra_links


def generate_step2_cypher_script() -> str:
    """Generate Cypher commands to populate Neo4j with Step 2 clustered nodes and topic entities."""
    nodes = get_step2_nodes()
    lines = [
        "// ====================================================================",
        "// 1920s Chinese Labor Strike Causal Knowledge Graph (Step 2)",
        "// Thematic Topic Clustering: 16 Nodes Grouped into 4 Visible Topics",
        "// Topic Structure: (A: Economic) -> (C: Strike) <- (B: Union)",
        "//                  (C: Strike) -> (D: Paralysis)",
        "// ====================================================================",
        "",
        "// 1. Schema Constraints & Indexes",
        "CREATE CONSTRAINT word_id_unique IF NOT EXISTS",
        "FOR (w:StrikeWord) REQUIRE w.id IS UNIQUE;",
        "",
        "CREATE CONSTRAINT cluster_id_unique IF NOT EXISTS",
        "FOR (c:TopicCluster) REQUIRE c.id IS UNIQUE;",
        "",
        "// 2. Clear existing demonstration nodes",
        "MATCH (w:StrikeWord) DETACH DELETE w;",
        "MATCH (c:TopicCluster) DETACH DELETE c;",
        "",
        "// 3. Create 4 Topic Cluster Entity Nodes",
    ]

    for topic_id, t in TOPICS.items():
        c2d = t["centroid_2d"]
        c3d = t["centroid_3d"]
        cluster_stmt = (
            f"CREATE (:TopicCluster {{\n"
            f'    id: "Topic_{topic_id}",\n'
            f'    topic_id: "{topic_id}",\n'
            f'    name: "{t["name"]}",\n'
            f'    short_label: "{t["short_label"]}",\n'
            f'    chinese_name: "{t["chinese_name"]}",\n'
            f'    causal_role: "{t["causal_role"]}",\n'
            f'    description: "{t["description"]}",\n'
            f'    color: "{t["color"]}",\n'
            f'    centroid_x: {c2d["x"]}, centroid_y: {c2d["y"]}, centroid_z: {c3d["z"]},\n'
            f'    step: 2\n'
            f"}});"
        )
        lines.append(cluster_stmt)

    lines.extend([
        "",
        "// 4. Create 16 Clustered Vocabulary Nodes and Connect to Clusters",
    ])

    for node in nodes:
        t = TOPICS[node["topic_id"]]
        node_stmt = (
            f"CREATE (w_{node['id']}:Topic_{node['topic_id']}:StrikeWord:Word {{\n"
            f'    id: "{node["id"]}",\n'
            f'    word: "{node["word"]}",\n'
            f'    chinese: "{node["chinese"]}",\n'
            f'    topic_id: "{node["topic_id"]}",\n'
            f'    topic_name: "{node["topic_name"]}",\n'
            f'    cluster_label: "{node["cluster_label"]}",\n'
            f'    causal_role: "{node["causal_role"]}",\n'
            f'    historical_source: "{node["historical_source"]}",\n'
            f'    context: "{node["context"]}",\n'
            f'    color: "{node["color"]}",\n'
            f'    x: {node["x"]}, y: {node["y"]}, z: {node["z"]},\n'
            f'    step: 2,\n'
            f'    status: "clustered"\n'
            f"}})\n"
            f'WITH w_{node["id"]}\n'
            f'MATCH (c:TopicCluster {{topic_id: "{node["topic_id"]}"}})\n'
            f'CREATE (w_{node["id"]})-[:BELONGS_TO {{topic_id: "{node["topic_id"]}"}}]->(c);'
        )
        lines.append(node_stmt)

    lines.extend([
        "",
        "// ====================================================================",
        "// Step 2 Query: Retrieve all Topic Clusters and Member Words",
        "// ====================================================================",
        "MATCH (c:TopicCluster)<-[r:BELONGS_TO]-(w:StrikeWord)",
        "RETURN c, r, w;",
        "",
    ])
    return "\n".join(lines)


def generate_step2_json_export() -> Dict[str, Any]:
    """Generate structured JSON representation of Step 2 clustered graph."""
    nodes = get_step2_nodes()
    links = get_step2_intra_links()
    return {
        "metadata": {
            "title": "1920s Chinese Strike Causal Knowledge Graph",
            "step": 2,
            "step_title": "Thematic Topic Clustering",
            "description": "16 vocabulary terms clustered into 4 topics (A, B, C, D) with overall cluster labels.",
            "total_nodes": len(nodes),
            "total_clusters": len(TOPICS),
            "total_intra_links": len(links),
            "theme": "light_white_background",
            "causal_flow": "(A: Economic) & (B: Union) -> (C: Strike) -> (D: Paralysis)",
        },
        "topics": TOPICS,
        "nodes": nodes,
        "intra_cluster_links": links,
    }


def generate_step2_plotly_2d_html() -> str:
    """Generate Plotly 2D scatter graph with visible topic clusters and cluster label annotations."""
    import plotly.graph_objects as go

    nodes = get_step2_nodes()
    fig = go.Figure()

    # 1. Traced cluster boundaries (translucent rounded capsules encircling initial node positions)
    for topic_id, t in TOPICS.items():
        t_nodes = [n for n in nodes if n["topic_id"] == topic_id]
        min_x = min(n["x"] for n in t_nodes) - 12
        max_x = max(n["x"] for n in t_nodes) + 12
        min_y = min(n["y"] for n in t_nodes) - 10
        max_y = max(n["y"] for n in t_nodes) + 10
        fig.add_shape(
            type="rect",
            x0=min_x,
            y0=min_y,
            x1=max_x,
            y1=max_y,
            line=dict(color=t["color"], width=1.8, dash="dash"),
            fillcolor=t["bg_color"],
            layer="below",
        )

    # 2. Intra-cluster subtle connection lines
    for topic_id, t in TOPICS.items():
        t_nodes = [n for n in nodes if n["topic_id"] == topic_id]
        c = t["centroid_2d"]
        for n in t_nodes:
            fig.add_trace(
                go.Scatter(
                    x=[c["x"], n["x"]],
                    y=[c["y"], n["y"]],
                    mode="lines",
                    line=dict(color=t["color"], width=1.2, dash="dot"),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

    # 2. Add traces per topic cluster
    for topic_id, t in TOPICS.items():
        t_nodes = [n for n in nodes if n["topic_id"] == topic_id]
        xs = [n["x"] for n in t_nodes]
        ys = [n["y"] for n in t_nodes]
        labels = [f"<b>{n['word']}</b><br>({n['chinese']})" for n in t_nodes]
        hover_texts = [
            f"<b>{n['word']}</b> ({n['chinese']})<br>"
            f"<b>Topic:</b> {t['name']}<br>"
            f"<b>Causal Role:</b> {t['causal_role']}<br>"
            f"<b>Historical Source:</b> {n['historical_source']}<br>"
            f"<b>Archival Context:</b> {n['context']}<br>"
            f"<b>Coordinates:</b> ({n['x']}, {n['y']})"
            for n in t_nodes
        ]

        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="markers+text",
                name=f"{t['short_label']}",
                text=labels,
                textposition="top center",
                textfont=dict(size=11, color="#0F172A"),
                hoverinfo="text",
                hovertext=hover_texts,
                marker=dict(
                    size=15,
                    color=t["color"],
                    opacity=0.95,
                    line=dict(color="#FFFFFF", width=2.5),
                    symbol="circle",
                ),
            )
        )

    # 3. Add Cluster Centroid Header Badges
    for topic_id, t in TOPICS.items():
        c = t["centroid_2d"]
        # Position label badge above centroid
        badge_y = c["y"] + (26 if c["y"] >= 0 else 26)
        fig.add_annotation(
            x=c["x"],
            y=badge_y,
            text=f"<b>{t['short_label']}</b><br><span style='font-size:10px; color:{t['color']}'>{t['chinese_name']} • {t['causal_role']}</span>",
            showarrow=False,
            font=dict(size=12, color="#0F172A"),
            bgcolor="rgba(255, 255, 255, 0.95)",
            bordercolor=t["color"],
            borderwidth=1.5,
            borderpad=6,
            align="center",
        )

    fig.update_layout(
        title=dict(
            text=(
                "<b>1920s Chinese Newspaper Labor Strike: Knowledge Graph (2D)</b><br>"
                "<sup>Step 2: Thematic Topic Clusters (A, B → C → D Causal Blueprint)</sup>"
            ),
            font=dict(size=18, color="#0F172A"),
            x=0.5,
            xanchor="center",
            y=0.96,
        ),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        legend=dict(
            title=dict(text="<b>Thematic Clusters</b>", font=dict(color="#0F172A")),
            font=dict(color="#0F172A", size=11),
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="#CBD5E1",
            borderwidth=1,
            x=0.02,
            y=0.98,
        ),
        xaxis=dict(
            title=dict(text="Spatial X (Causal Precursors ➔ Central Strike ➔ Outcomes)", font=dict(color="#475569")),
            gridcolor="#F1F5F9",
            zerolinecolor="#E2E8F0",
            tickfont=dict(color="#64748B"),
            range=[-115, 115],
        ),
        yaxis=dict(
            title=dict(text="Spatial Y", font=dict(color="#475569")),
            gridcolor="#F1F5F9",
            zerolinecolor="#E2E8F0",
            tickfont=dict(color="#64748B"),
            scaleanchor="x",
            scaleratio=1,
            range=[-105, 95],
        ),
        margin=dict(l=60, r=60, b=60, t=100),
    )

    return fig.to_html(include_plotlyjs="cdn", full_html=True)


def generate_step2_d3_2d_viewer_html() -> str:
    """Generate D3.js 2D SVG viewer with visible cluster boundary bubbles and overall cluster labels."""
    graph_json = json.dumps(generate_step2_json_export())

    template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>2D Causal Graph - Step 2: Thematic Topic Clusters</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            background: #FFFFFF;
            color: #0F172A;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            overflow: hidden;
            width: 100vw;
            height: 100vh;
            user-select: none;
        }
        #svg-canvas {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            cursor: grab;
            background: #FFFFFF;
        }
        #svg-canvas:active {
            cursor: grabbing;
        }
        .hud-panel {
            position: absolute;
            top: 20px;
            left: 20px;
            z-index: 10;
            background: rgba(255, 255, 255, 0.94);
            backdrop-filter: blur(12px);
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 20px 24px;
            max-width: 420px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
        }
        .hud-title {
            font-size: 17px;
            font-weight: 700;
            color: #0F172A;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .badge {
            display: inline-block;
            background: #2563EB;
            color: #EFF6FF;
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 999px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        .hud-desc {
            font-size: 13px;
            color: #64748B;
            line-height: 1.5;
            margin-bottom: 14px;
        }
        .causal-blueprint {
            background: #F8FAFC;
            border-radius: 8px;
            padding: 10px 12px;
            margin-bottom: 14px;
            border-left: 3px solid #2563EB;
            font-size: 12px;
            color: #334155;
            line-height: 1.5;
        }
        .blueprint-row {
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 2px;
            font-family: "SF Mono", Consolas, monospace;
            font-size: 11px;
            color: #1E293B;
        }
        .cluster-pill-list {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 6px;
            margin-bottom: 14px;
        }
        .cluster-pill-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 11px;
            font-weight: 600;
            padding: 6px 8px;
            border-radius: 6px;
            background: #F1F5F9;
            cursor: pointer;
            transition: all 0.2s;
        }
        .cluster-pill-item:hover {
            transform: translateY(-1px);
        }
        .cluster-color-circle {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            flex-shrink: 0;
        }
        .controls-group {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        .btn {
            background: #F1F5F9;
            border: 1px solid #CBD5E1;
            color: #334155;
            padding: 6px 12px;
            font-size: 12px;
            font-weight: 500;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn:hover {
            background: #E2E8F0;
        }
        .btn.active {
            background: #2563EB;
            border-color: #2563EB;
            color: #FFFFFF;
        }
        #node-details {
            position: absolute;
            bottom: 24px;
            right: 24px;
            z-index: 10;
            background: rgba(255, 255, 255, 0.96);
            backdrop-filter: blur(12px);
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 20px 24px;
            max-width: 380px;
            display: none;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12);
        }
        #node-details h3 {
            font-size: 18px;
            color: #0F172A;
            margin-bottom: 2px;
        }
        #node-details .chinese {
            font-size: 14px;
            margin-bottom: 12px;
            font-weight: 600;
        }
        #node-details .meta-row {
            font-size: 12px;
            color: #475569;
            margin-bottom: 6px;
            line-height: 1.4;
        }
        #node-details .meta-row strong {
            color: #0F172A;
        }
        .close-btn {
            position: absolute;
            top: 12px;
            right: 12px;
            background: none;
            border: none;
            color: #94A3B8;
            font-size: 18px;
            cursor: pointer;
        }
        .close-btn:hover {
            color: #0F172A;
        }

        /* SVG Clustered Elements */
        .cluster-hull {
            fill-opacity: 0.08;
            stroke-dasharray: 6, 4;
            stroke-width: 1.8px;
            transition: fill-opacity 0.2s, stroke-width 0.2s;
            cursor: pointer;
        }
        .cluster-hull:hover {
            fill-opacity: 0.14;
            stroke-width: 2.5px;
        }
        .cluster-badge-group {
            cursor: pointer;
            filter: drop-shadow(0 4px 10px rgba(0, 0, 0, 0.08));
        }
        .cluster-badge-bg {
            fill: #FFFFFF;
            rx: 8px;
            ry: 8px;
            stroke-width: 1.5px;
        }
        .cluster-badge-title {
            font-size: 13px;
            font-weight: 700;
            text-anchor: middle;
            dominant-baseline: central;
        }
        .cluster-badge-sub {
            font-size: 10px;
            font-weight: 500;
            text-anchor: middle;
            dominant-baseline: central;
        }
        .intra-link {
            stroke-opacity: 0.25;
            stroke-width: 1px;
            stroke-dasharray: 3, 3;
            pointer-events: none;
        }
        .node-circle {
            cursor: pointer;
            transition: r 0.2s ease, filter 0.2s ease;
        }
        .node-circle:hover {
            filter: drop-shadow(0 0 10px currentColor);
        }
        .node-halo {
            pointer-events: none;
            animation: pulse-halo 3s infinite ease-in-out;
        }
        @keyframes pulse-halo {
            0% { opacity: 0.15; transform: scale(1); }
            50% { opacity: 0.35; transform: scale(1.18); }
            100% { opacity: 0.15; transform: scale(1); }
        }
        .label-bg {
            fill: rgba(255, 255, 255, 0.95);
            stroke: #CBD5E1;
            stroke-width: 1px;
            rx: 6px;
            ry: 6px;
            filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.08));
        }
        .label-text-en {
            fill: #0F172A;
            font-size: 11px;
            font-weight: 600;
            text-anchor: middle;
            dominant-baseline: central;
        }
        .label-text-zh {
            font-size: 10px;
            font-weight: 600;
            text-anchor: middle;
            dominant-baseline: central;
        }
        .selected-ring {
            fill: none;
            stroke: #F59E0B;
            stroke-width: 3px;
            stroke-dasharray: 4, 3;
            animation: rotate-ring 6s linear infinite;
        }
        @keyframes rotate-ring {
            100% { stroke-dashoffset: 28; }
        }
    </style>
</head>
<body>
    <svg id="svg-canvas"></svg>

    <div class="hud-panel">
        <div class="hud-title">
            <span>China Strike Knowledge Graph</span>
            <span class="badge" id="hud-badge">Step 2 • Clustered</span>
        </div>
        <div class="hud-desc">
            Nodes maintain their exact initial coordinates. Clusters are identified based on spatial proximity in initial embedding space, delineated by colored boundaries and cluster header labels.
        </div>
        <div style="font-size:11px; background:#F8FAFC; border:1px solid #E2E8F0; border-radius:6px; padding:7px 10px; margin-bottom:12px; color:#475569; line-height:1.4;">
            💡 <strong>Zero Node Movement:</strong> Nodes do not shift when clustered. Toggle below to compare initial unclustered baseline vs. traced cluster boundaries.
        </div>

        <div class="causal-blueprint">
            <div style="font-weight: 700; margin-bottom: 4px; color: #0F172A;">Causal Blueprint Architecture:</div>
            <div class="blueprint-row"><span>(A) Economic Grievances</span> <span>➔</span> <span>(C) Strike</span></div>
            <div class="blueprint-row"><span>(B) Union Mobilization</span>  <span>➔</span> <span>(C) Strike</span></div>
            <div class="blueprint-row"><span>(C) General Strike</span>      <span>➔</span> <span>(D) Paralysis</span></div>
        </div>

        <div class="cluster-pill-list" id="cluster-pills"></div>

        <div class="controls-group">
            <button class="btn active" id="btn-toggle-mode" onclick="toggleClusterMode()" style="font-weight:700;">Mode: Clusters Revealed</button>
            <button class="btn active" id="btn-toggle-labels" onclick="toggleLabels()">Labels</button>
            <button class="btn active" id="btn-toggle-hulls" onclick="toggleHulls()">Boundaries</button>
            <button class="btn" onclick="zoomIn()">Zoom (+)</button>
            <button class="btn" onclick="zoomOut()">Zoom (-)</button>
            <button class="btn" onclick="resetZoom()">Reset View</button>
        </div>
    </div>

    <div id="node-details">
        <button class="close-btn" onclick="closeDetails()">&times;</button>
        <h3 id="det-word">Word</h3>
        <div class="chinese" id="det-chinese">中文</div>
        <div class="meta-row"><strong>Thematic Cluster:</strong> <span id="det-cluster"></span></div>
        <div class="meta-row"><strong>Causal Role:</strong> <span id="det-role"></span></div>
        <div class="meta-row"><strong>Historical Source:</strong> <span id="det-source"></span></div>
        <div class="meta-row"><strong>Archival Context:</strong> <span id="det-context"></span></div>
        <div class="meta-row"><strong>2D Coordinates:</strong> <span id="det-coords"></span></div>
    </div>

    <script>
        const graphData = __GRAPH_JSON__;
        let showLabels = true;
        let showHulls = true;
        let selectedNodeId = null;

        const svg = d3.select("#svg-canvas");
        const width = window.innerWidth;
        const height = window.innerHeight;
        svg.attr("width", width).attr("height", height);

        // Populate HUD cluster pills
        const pillsContainer = document.getElementById("cluster-pills");
        Object.entries(graphData.topics).forEach(([id, t]) => {
            const item = document.createElement("div");
            item.className = "cluster-pill-item";
            item.innerHTML = `
                <div class="cluster-color-circle" style="background:${t.color};"></div>
                <span style="color:#0F172A;">Topic ${id}</span>
            `;
            item.onclick = () => focusCluster(id);
            pillsContainer.appendChild(item);
        });

        // SVG Definitions
        const defs = svg.append("defs");

        // Background subtle grid pattern
        const pattern = defs.append("pattern")
            .attr("id", "grid")
            .attr("width", 40)
            .attr("height", 40)
            .attr("patternUnits", "userSpaceOnUse");
        pattern.append("circle")
            .attr("cx", 20)
            .attr("cy", 20)
            .attr("r", 1.2)
            .attr("fill", "rgba(0, 0, 0, 0.05)");

        svg.append("rect")
            .attr("width", "100%")
            .attr("height", "100%")
            .attr("fill", "url(#grid)");

        const container = svg.append("g").attr("id", "zoom-container");
        const hullLayer = container.append("g").attr("id", "hull-layer");
        const linkLayer = container.append("g").attr("id", "link-layer");
        const badgeLayer = container.append("g").attr("id", "badge-layer");
        const nodeLayer = container.append("g").attr("id", "node-layer");

        // Scale coordinates
        const scaleFactor = 4.8;
        const nodes = graphData.nodes.map(n => ({
            ...n,
            x: width / 2 + n.x * scaleFactor,
            y: height / 2 - n.y * scaleFactor
        }));

        // Quick lookup by ID
        const nodeMap = new Map(nodes.map(n => [n.id, n]));

        // Calculate Clusters
        const clusters = {};
        Object.entries(graphData.topics).forEach(([id, t]) => {
            const tNodes = nodes.filter(n => n.topic_id === id);
            const cx = d3.mean(tNodes, n => n.x);
            const cy = d3.mean(tNodes, n => n.y);
            clusters[id] = {
                id: id,
                meta: t,
                nodes: tNodes,
                cx: cx,
                cy: cy
            };
        });

        // 1. Draw Intra-Cluster Links
        graphData.intra_cluster_links.forEach(l => {
            const src = nodeMap.get(l.source);
            const tgt = nodeMap.get(l.target);
            if (src && tgt) {
                linkLayer.append("line")
                    .attr("class", "intra-link")
                    .attr("x1", src.x)
                    .attr("y1", src.y)
                    .attr("x2", tgt.x)
                    .attr("y2", tgt.y)
                    .attr("stroke", l.color);
            }
        });

        // 2. Draw Cluster Boundary Bubbles (Hulls)
        function updateHulls() {
            hullLayer.selectAll("*").remove();
            if (!showHulls) return;

            Object.values(clusters).forEach(cl => {
                const points = cl.nodes.map(n => [n.x, n.y]);
                const hull = d3.polygonHull(points);
                if (hull) {
                    // Expand hull outward from centroid for padding
                    const padding = 55;
                    const expanded = hull.map(pt => {
                        const dx = pt[0] - cl.cx;
                        const dy = pt[1] - cl.cy;
                        const dist = Math.hypot(dx, dy) || 1;
                        return [cl.cx + (dx / dist) * (dist + padding), cl.cy + (dy / dist) * (dist + padding)];
                    });

                    const pathData = d3.line().curve(d3.curveCardinalClosed.tension(0.65))(expanded);
                    hullLayer.append("path")
                        .attr("class", "cluster-hull")
                        .attr("d", pathData)
                        .attr("fill", cl.meta.color)
                        .attr("stroke", cl.meta.color)
                        .on("click", (event) => {
                            event.stopPropagation();
                            focusCluster(cl.id);
                        });
                }
            });
        }
        updateHulls();

        // 3. Draw Overall Cluster Header Badges
        Object.values(clusters).forEach(cl => {
            const badge = badgeLayer.append("g")
                .attr("class", "cluster-badge-group")
                .attr("transform", `translate(${cl.cx}, ${cl.cy - 95})`)
                .on("click", (event) => {
                    event.stopPropagation();
                    focusCluster(cl.id);
                });

            // Badge Background Pill
            badge.append("rect")
                .attr("class", "cluster-badge-bg")
                .attr("x", -135)
                .attr("y", -24)
                .attr("width", 270)
                .attr("height", 48)
                .attr("stroke", cl.meta.color);

            // Title
            badge.append("text")
                .attr("class", "cluster-badge-title")
                .attr("y", -6)
                .attr("fill", cl.meta.color)
                .text(cl.meta.short_label);

            // Subtitle
            badge.append("text")
                .attr("class", "cluster-badge-sub")
                .attr("y", 12)
                .attr("fill", "#475569")
                .text(`${cl.meta.chinese_name} • ${cl.meta.causal_role}`);
        });

        // 4. Render Nodes
        const drag = d3.drag()
            .on("start", function(event, d) {
                d3.select(this).raise();
            })
            .on("drag", function(event, d) {
                d.x = event.x;
                d.y = event.y;
                d3.select(this).attr("transform", `translate(${d.x}, ${d.y})`);
                updateHulls();
            });

        const nodeGroups = nodeLayer.selectAll(".node-group")
            .data(nodes)
            .enter()
            .append("g")
            .attr("class", "node-group")
            .attr("transform", d => `translate(${d.x}, ${d.y})`)
            .call(drag)
            .on("click", (event, d) => {
                event.stopPropagation();
                selectNode(d);
            });

        // Pulsing Halo
        nodeGroups.append("circle")
            .attr("class", "node-halo")
            .attr("r", 20)
            .attr("fill", d => d.color);

        // Core Circle
        nodeGroups.append("circle")
            .attr("class", "node-circle")
            .attr("r", 13)
            .attr("fill", d => d.color)
            .attr("stroke", "#FFFFFF")
            .attr("stroke-width", 2.5);

        // Selection Ring
        nodeGroups.append("circle")
            .attr("class", "selected-ring")
            .attr("r", 19)
            .attr("display", d => (d.id === selectedNodeId ? "block" : "none"));

        // Label Pill
        const labelGroups = nodeGroups.append("g")
            .attr("class", "node-label-pill")
            .attr("transform", "translate(0, 24)");

        labelGroups.append("rect")
            .attr("class", "label-bg")
            .attr("x", -65)
            .attr("y", -8)
            .attr("width", 130)
            .attr("height", 32)
            .attr("stroke", d => d.color);

        labelGroups.append("text")
            .attr("class", "label-text-en")
            .attr("y", 2)
            .text(d => d.word);

        labelGroups.append("text")
            .attr("class", "label-text-zh")
            .attr("y", 16)
            .attr("fill", d => d.color)
            .text(d => d.chinese);

        // Zoom Behavior
        const zoom = d3.zoom()
            .scaleExtent([0.3, 3])
            .on("zoom", (event) => {
                container.attr("transform", event.transform);
            });
        svg.call(zoom);

        // Background click clears selection
        svg.on("click", () => {
            selectedNodeId = null;
            updateSelection();
            closeDetails();
        });

        function selectNode(d) {
            selectedNodeId = d.id;
            updateSelection();

            document.getElementById("node-details").style.display = "block";
            document.getElementById("det-word").innerText = d.word;
            document.getElementById("det-chinese").innerText = d.chinese;
            document.getElementById("det-chinese").style.color = d.color;
            document.getElementById("det-cluster").innerText = `${d.cluster_label} (${d.topic_chinese})`;
            document.getElementById("det-role").innerText = d.causal_role;
            document.getElementById("det-source").innerText = d.historical_source;
            document.getElementById("det-context").innerText = d.context;
            document.getElementById("det-coords").innerText = `(${d.x.toFixed(1)}, ${d.y.toFixed(1)})`;
        }

        function updateSelection() {
            container.selectAll(".selected-ring")
                .attr("display", d => (d.id === selectedNodeId ? "block" : "none"));
        }

        function focusCluster(topicId) {
            const cl = clusters[topicId];
            if (!cl) return;
            svg.transition().duration(750).call(
                zoom.transform,
                d3.zoomIdentity.translate(width / 2 - cl.cx, height / 2 - cl.cy).scale(1.2)
            );
        }

        function closeDetails() {
            document.getElementById("node-details").style.display = "none";
            selectedNodeId = null;
            updateSelection();
        }

        let clusterMode = true;

        function toggleClusterMode() {
            clusterMode = !clusterMode;
            const btn = document.getElementById("btn-toggle-mode");
            const badge = document.getElementById("hud-badge");

            if (clusterMode) {
                btn.classList.add("active");
                btn.textContent = "Mode: Clusters Revealed";
                badge.textContent = "Step 2 • Clustered";
                badge.style.background = "#2563EB";

                hullLayer.transition().duration(500).style("opacity", showHulls ? 1 : 0);
                badgeLayer.transition().duration(500).style("opacity", 1);
                linkLayer.transition().duration(500).style("opacity", 1);

                nodeGroups.selectAll(".node-halo").transition().duration(500).attr("fill", d => d.color);
                nodeGroups.selectAll(".node-circle").transition().duration(500).attr("fill", d => d.color);
                labelGroups.selectAll(".label-bg").transition().duration(500).attr("stroke", d => d.color);
                labelGroups.selectAll(".label-text-zh").transition().duration(500).attr("fill", d => d.color);
            } else {
                btn.classList.remove("active");
                btn.textContent = "Mode: Initial Baseline";
                badge.textContent = "Step 1 • Initial Positions";
                badge.style.background = "#64748B";

                hullLayer.transition().duration(500).style("opacity", 0);
                badgeLayer.transition().duration(500).style("opacity", 0);
                linkLayer.transition().duration(500).style("opacity", 0);

                nodeGroups.selectAll(".node-halo").transition().duration(500).attr("fill", "#0284C7");
                nodeGroups.selectAll(".node-circle").transition().duration(500).attr("fill", "#0284C7");
                labelGroups.selectAll(".label-bg").transition().duration(500).attr("stroke", "#CBD5E1");
                labelGroups.selectAll(".label-text-zh").transition().duration(500).attr("fill", "#64748B");
            }
        }

        function toggleLabels() {
            showLabels = !showLabels;
            const btn = document.getElementById("btn-toggle-labels");
            btn.classList.toggle("active", showLabels);
            container.selectAll(".node-label-pill")
                .attr("display", showLabels ? "block" : "none");
        }

        function toggleHulls() {
            showHulls = !showHulls;
            const btn = document.getElementById("btn-toggle-hulls");
            btn.classList.toggle("active", showHulls);
            if (clusterMode) {
                hullLayer.transition().duration(300).style("opacity", showHulls ? 1 : 0);
            }
        }

        function zoomIn() {
            svg.transition().duration(350).call(zoom.scaleBy, 1.3);
        }

        function zoomOut() {
            svg.transition().duration(350).call(zoom.scaleBy, 0.7);
        }

        function resetZoom() {
            svg.transition().duration(500).call(zoom.transform, d3.zoomIdentity);
            closeDetails();
        }

        window.addEventListener("resize", () => {
            const newW = window.innerWidth;
            const newH = window.innerHeight;
            svg.attr("width", newW).attr("height", newH);
        });
    </script>
</body>
</html>
"""
    return template.replace("__GRAPH_JSON__", graph_json)


def generate_step2_plotly_3d_html() -> str:
    """Generate Plotly 3D scatter graph with visible topic clusters and cluster headers."""
    import plotly.graph_objects as go

    nodes = get_step2_nodes()
    fig = go.Figure()

    # 1. Intra-cluster 3D boundary lines connecting nodes of each cluster
    for topic_id, t in TOPICS.items():
        t_nodes = [n for n in nodes if n["topic_id"] == topic_id]
        lx, ly, lz = [], [], []
        for i in range(len(t_nodes)):
            for j in range(i + 1, len(t_nodes)):
                lx.extend([t_nodes[i]["x"], t_nodes[j]["x"], None])
                ly.extend([t_nodes[i]["y"], t_nodes[j]["y"], None])
                lz.extend([t_nodes[i]["z"], t_nodes[j]["z"], None])
        fig.add_trace(
            go.Scatter3d(
                x=lx,
                y=ly,
                z=lz,
                mode="lines",
                line=dict(color=t["color"], width=2.5, dash="dash"),
                hoverinfo="none",
                showlegend=False,
                opacity=0.45,
            )
        )

    # 2. Traces per topic
    for topic_id, t in TOPICS.items():
        t_nodes = [n for n in nodes if n["topic_id"] == topic_id]
        xs = [n["x"] for n in t_nodes]
        ys = [n["y"] for n in t_nodes]
        zs = [n["z"] for n in t_nodes]
        labels = [f"<b>{n['word']}</b><br>({n['chinese']})" for n in t_nodes]
        hover_texts = [
            f"<b>{n['word']}</b> ({n['chinese']})<br>"
            f"<b>Topic:</b> {t['name']}<br>"
            f"<b>Causal Role:</b> {t['causal_role']}<br>"
            f"<b>Historical Source:</b> {n['historical_source']}<br>"
            f"<b>Archival Context:</b> {n['context']}<br>"
            f"<b>Coordinates:</b> ({n['x']}, {n['y']}, {n['z']})"
            for n in t_nodes
        ]

        fig.add_trace(
            go.Scatter3d(
                x=xs,
                y=ys,
                z=zs,
                mode="markers+text",
                name=f"{t['short_label']}",
                text=labels,
                textposition="top center",
                textfont=dict(size=11, color="#0F172A"),
                hoverinfo="text",
                hovertext=hover_texts,
                marker=dict(
                    size=10,
                    color=t["color"],
                    opacity=0.95,
                    line=dict(color="#FFFFFF", width=2),
                    symbol="circle",
                ),
            )
        )

    # Centroid annotations
    for topic_id, t in TOPICS.items():
        c = t["centroid_3d"]
        fig.add_trace(
            go.Scatter3d(
                x=[c["x"]],
                y=[c["y"]],
                z=[c["z"] + 20],
                mode="text",
                text=[f"<b>[ {t['short_label']} ]</b>"],
                textposition="middle center",
                textfont=dict(size=12, color=t["color"]),
                hoverinfo="none",
                showlegend=False,
            )
        )

    fig.update_layout(
        title=dict(
            text=(
                "<b>1920s Chinese Newspaper Labor Strike: Knowledge Graph (3D)</b><br>"
                "<sup>Step 2: Thematic Topic Clusters (A, B → C → D Causal Blueprint)</sup>"
            ),
            font=dict(size=18, color="#0F172A"),
            x=0.5,
            xanchor="center",
            y=0.95,
        ),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        legend=dict(
            title=dict(text="<b>Thematic Clusters</b>", font=dict(color="#0F172A")),
            font=dict(color="#0F172A", size=11),
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="#CBD5E1",
            borderwidth=1,
            x=0.02,
            y=0.95,
        ),
        scene=dict(
            xaxis=dict(
                title=dict(text="Spatial X (Causal Direction ➔)", font=dict(color="#475569")),
                backgroundcolor="#F8FAFC",
                gridcolor="#E2E8F0",
                showbackground=True,
                zerolinecolor="#CBD5E1",
                tickfont=dict(color="#64748B"),
            ),
            yaxis=dict(
                title=dict(text="Spatial Y", font=dict(color="#475569")),
                backgroundcolor="#F8FAFC",
                gridcolor="#E2E8F0",
                showbackground=True,
                zerolinecolor="#CBD5E1",
                tickfont=dict(color="#64748B"),
            ),
            zaxis=dict(
                title=dict(text="Spatial Z", font=dict(color="#475569")),
                backgroundcolor="#F8FAFC",
                gridcolor="#E2E8F0",
                showbackground=True,
                zerolinecolor="#CBD5E1",
                tickfont=dict(color="#64748B"),
            ),
            camera=dict(
                eye=dict(x=1.7, y=1.5, z=1.3),
                up=dict(x=0, y=0, z=1),
            ),
        ),
        margin=dict(l=0, r=0, b=0, t=80),
    )

    return fig.to_html(include_plotlyjs="cdn", full_html=True)


def generate_step2_threejs_viewer_html() -> str:
    """Generate 3D WebGL viewer with visible clusters, cluster billboards, and intra-cluster links."""
    graph_json = json.dumps(generate_step2_json_export())

    template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D Causal Graph - Step 2: Thematic Topic Clusters</title>
    <script src="https://unpkg.com/three@0.160.0/build/three.min.js"></script>
    <script src="https://unpkg.com/three-spritetext@1.8.2/dist/three-spritetext.min.js"></script>
    <script src="https://unpkg.com/3d-force-graph@1.73.3/dist/3d-force-graph.min.js"></script>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            background: #FFFFFF;
            color: #0F172A;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            overflow: hidden;
            width: 100vw;
            height: 100vh;
        }
        #3d-graph {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 1;
        }
        .hud-panel {
            position: absolute;
            top: 20px;
            left: 20px;
            z-index: 10;
            background: rgba(255, 255, 255, 0.94);
            backdrop-filter: blur(12px);
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 20px 24px;
            max-width: 420px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
        }
        .hud-title {
            font-size: 17px;
            font-weight: 700;
            color: #0F172A;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .badge {
            display: inline-block;
            background: #2563EB;
            color: #EFF6FF;
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 999px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        .hud-desc {
            font-size: 13px;
            color: #64748B;
            line-height: 1.5;
            margin-bottom: 14px;
        }
        .causal-blueprint {
            background: #F8FAFC;
            border-radius: 8px;
            padding: 10px 12px;
            margin-bottom: 14px;
            border-left: 3px solid #2563EB;
            font-size: 12px;
            color: #334155;
            line-height: 1.5;
        }
        .blueprint-row {
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 2px;
            font-family: "SF Mono", Consolas, monospace;
            font-size: 11px;
            color: #1E293B;
        }
        .cluster-pill-list {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 6px;
            margin-bottom: 14px;
        }
        .cluster-pill-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 11px;
            font-weight: 600;
            padding: 6px 8px;
            border-radius: 6px;
            background: #F1F5F9;
            cursor: pointer;
            transition: all 0.2s;
        }
        .cluster-pill-item:hover {
            transform: translateY(-1px);
        }
        .cluster-color-circle {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            flex-shrink: 0;
        }
        .controls-group {
            display: flex;
            gap: 8px;
        }
        .btn {
            flex: 1;
            background: #F1F5F9;
            border: 1px solid #CBD5E1;
            color: #334155;
            padding: 8px 12px;
            font-size: 12px;
            font-weight: 500;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn:hover {
            background: #E2E8F0;
        }
        .btn.active {
            background: #2563EB;
            border-color: #2563EB;
            color: #FFFFFF;
        }
        #node-details {
            position: absolute;
            bottom: 24px;
            right: 24px;
            z-index: 10;
            background: rgba(255, 255, 255, 0.96);
            backdrop-filter: blur(12px);
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 20px 24px;
            max-width: 380px;
            display: none;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12);
        }
        #node-details h3 {
            font-size: 18px;
            color: #0F172A;
            margin-bottom: 2px;
        }
        #node-details .chinese {
            font-size: 14px;
            margin-bottom: 12px;
            font-weight: 600;
        }
        #node-details .meta-row {
            font-size: 12px;
            color: #475569;
            margin-bottom: 6px;
            line-height: 1.4;
        }
        #node-details .meta-row strong {
            color: #0F172A;
        }
    </style>
</head>
<body>
    <div id="3d-graph"></div>

    <div class="hud-panel">
        <div class="hud-title">
            <span>China Strike Knowledge Graph</span>
            <span class="badge" id="hud-badge-3d">Step 2 • 3D Clustered</span>
        </div>
        <div class="hud-desc">
            Nodes maintain their exact initial coordinates in 3D space. Clusters are identified based on spatial proximity in embedding space, delineated by cluster billboards, boundary bubbles, and palettes.
        </div>
        <div style="font-size:11px; background:#F8FAFC; border:1px solid #E2E8F0; border-radius:6px; padding:7px 10px; margin-bottom:12px; color:#475569; line-height:1.4;">
            💡 <strong>Zero Node Movement:</strong> Nodes do not shift when clustered. Toggle below to compare initial unclustered baseline vs. traced cluster boundaries.
        </div>

        <div class="causal-blueprint">
            <div style="font-weight: 700; margin-bottom: 4px; color: #0F172A;">Causal Blueprint Architecture:</div>
            <div class="blueprint-row"><span>(A) Economic Grievances</span> <span>➔</span> <span>(C) Strike</span></div>
            <div class="blueprint-row"><span>(B) Union Mobilization</span>  <span>➔</span> <span>(C) Strike</span></div>
            <div class="blueprint-row"><span>(C) General Strike</span>      <span>➔</span> <span>(D) Paralysis</span></div>
        </div>

        <div class="cluster-pill-list" id="cluster-pills"></div>

        <div class="controls-group">
            <button class="btn active" id="btn-toggle-mode-3d" onclick="toggleClusterMode3D()" style="font-weight:700;">Mode: Clusters Revealed</button>
            <button class="btn active" id="btn-toggle-labels" onclick="toggleLabels()">Labels</button>
            <button class="btn" onclick="resetCamera()">Reset View</button>
        </div>
    </div>

    <div id="node-details">
        <h3 id="det-word">Word</h3>
        <div class="chinese" id="det-chinese">中文</div>
        <div class="meta-row"><strong>Thematic Cluster:</strong> <span id="det-cluster"></span></div>
        <div class="meta-row"><strong>Causal Role:</strong> <span id="det-role"></span></div>
        <div class="meta-row"><strong>Historical Source:</strong> <span id="det-source"></span></div>
        <div class="meta-row"><strong>Archival Context:</strong> <span id="det-context"></span></div>
        <div class="meta-row"><strong>3D Coordinates:</strong> <span id="det-coords"></span></div>
    </div>

    <script>
        const graphData = __GRAPH_JSON__;
        let showLabels = true;
        let clusterMode3D = true;
        const clusterBillboards = [];
        const boundaryMeshes = [];
        const nodeSpheres = [];

        // Populate HUD cluster pills
        const pillsContainer = document.getElementById("cluster-pills");
        Object.entries(graphData.topics).forEach(([id, t]) => {
            const item = document.createElement("div");
            item.className = "cluster-pill-item";
            item.innerHTML = `
                <div class="cluster-color-circle" style="background:${t.color};"></div>
                <span style="color:#0F172A;">Topic ${id}</span>
            `;
            item.onclick = () => focusCluster3D(id);
            pillsContainer.appendChild(item);
        });

        // 3D Graph Data
        const nodes3d = graphData.nodes.map(n => ({
            id: n.id,
            name: n.word,
            chinese: n.chinese,
            topic_id: n.topic_id,
            topic_name: n.topic_name,
            cluster_label: n.cluster_label,
            causal_role: n.causal_role,
            historical_source: n.historical_source,
            context: n.context,
            color: n.color,
            fx: n.x,
            fy: n.y,
            fz: n.z
        }));

        // Cluster Centroid Billboard pseudo-nodes
        Object.entries(graphData.topics).forEach(([id, t]) => {
            nodes3d.push({
                id: `cluster_badge_${id}`,
                isClusterBadge: true,
                topic_id: id,
                title: t.short_label,
                subtitle: `${t.chinese_name} • ${t.causal_role}`,
                color: t.color,
                fx: t.centroid_3d.x,
                fy: t.centroid_3d.y + 24,
                fz: t.centroid_3d.z + 18
            });
        });

        const links3d = graphData.intra_cluster_links.map(l => ({
            source: l.source,
            target: l.target,
            color: l.color
        }));

        const gData = {
            nodes: nodes3d,
            links: links3d
        };

        const Graph = ForceGraph3D()(document.getElementById('3d-graph'))
            .graphData(gData)
            .backgroundColor('#FFFFFF')
            .showNavInfo(false)
            .nodeRelSize(7)
            .linkColor(link => link.color)
            .linkWidth(1.2)
            .linkOpacity(0.35)
            .nodeThreeObject(node => {
                if (node.isClusterBadge) {
                    const badgeSprite = new SpriteText(`${node.title}\\n${node.subtitle}`);
                    badgeSprite.color = node.color;
                    badgeSprite.textHeight = 4.2;
                    badgeSprite.backgroundColor = 'rgba(255, 255, 255, 0.94)';
                    badgeSprite.borderColor = node.color;
                    badgeSprite.borderWidth = 1;
                    badgeSprite.padding = 3;
                    badgeSprite.borderRadius = 4;
                    clusterBillboards.push(badgeSprite);
                    return badgeSprite;
                }

                const group = new THREE.Group();

                const sphereGeometry = new THREE.SphereGeometry(3.6, 24, 24);
                const sphereMaterial = new THREE.MeshLambertMaterial({
                    color: node.color,
                    transparent: true,
                    opacity: 0.95
                });
                const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
                group.add(sphere);

                let labelSprite = null;
                labelSprite = new SpriteText(`${node.name}\\n(${node.chinese})`);
                labelSprite.color = '#0F172A';
                labelSprite.textHeight = 3.2;
                labelSprite.position.y = 7;
                labelSprite.backgroundColor = 'rgba(255, 255, 255, 0.9)';
                labelSprite.borderColor = node.color;
                labelSprite.borderWidth = 0.8;
                labelSprite.padding = 2;
                labelSprite.borderRadius = 3;
                group.add(labelSprite);

                nodeSpheres.push({ node, sphere, labelSprite });
                return group;
            })
            .onNodeClick(node => {
                if (node.isClusterBadge) {
                    focusCluster3D(node.topic_id);
                    return;
                }
                const distance = 80;
                const distRatio = 1 + distance / Math.hypot(node.fx, node.fy, node.fz);
                Graph.cameraPosition(
                    { x: node.fx * distRatio, y: node.fy * distRatio, z: node.fz * distRatio },
                    { x: node.fx, y: node.fy, z: node.fz },
                    2000
                );

                document.getElementById('node-details').style.display = 'block';
                document.getElementById('det-word').innerText = node.name;
                document.getElementById('det-chinese').innerText = node.chinese;
                document.getElementById('det-chinese').style.color = node.color;
                document.getElementById('det-cluster').innerText = node.cluster_label;
                document.getElementById('det-role').innerText = node.causal_role;
                document.getElementById('det-source').innerText = node.historical_source;
                document.getElementById('det-context').innerText = node.context;
                document.getElementById('det-coords').innerText = `(${node.fx}, ${node.fy}, ${node.fz})`;
            })
            .onBackgroundClick(() => {
                document.getElementById('node-details').style.display = 'none';
            });

        // Add 3D wireframe boundary spheres around cluster territories
        Object.entries(graphData.topics).forEach(([id, t]) => {
            const geom = new THREE.SphereGeometry(24, 20, 16);
            const mat = new THREE.MeshBasicMaterial({
                color: t.color,
                wireframe: true,
                transparent: true,
                opacity: 0.16
            });
            const mesh = new THREE.Mesh(geom, mat);
            mesh.position.set(t.centroid_3d.x, t.centroid_3d.y, t.centroid_3d.z);
            mesh.name = `boundary_${id}`;
            Graph.scene().add(mesh);
            boundaryMeshes.push(mesh);
        });

        Graph.cameraPosition({ x: 210, y: 170, z: 230 });

        function toggleClusterMode3D() {
            clusterMode3D = !clusterMode3D;
            const btn = document.getElementById("btn-toggle-mode-3d");
            const badge = document.getElementById("hud-badge-3d");

            if (clusterMode3D) {
                btn.classList.add("active");
                btn.textContent = "Mode: Clusters Revealed";
                badge.textContent = "Step 2 • 3D Clustered";
                badge.style.background = "#2563EB";

                clusterBillboards.forEach(b => b.visible = true);
                boundaryMeshes.forEach(m => m.visible = true);
                Graph.linkOpacity(0.35);

                nodeSpheres.forEach(item => {
                    item.sphere.material.color.set(item.node.color);
                    if (item.labelSprite) {
                        item.labelSprite.borderColor = item.node.color;
                    }
                });
            } else {
                btn.classList.remove("active");
                btn.textContent = "Mode: Initial Baseline";
                badge.textContent = "Step 1 • Initial Positions";
                badge.style.background = "#64748B";

                clusterBillboards.forEach(b => b.visible = false);
                boundaryMeshes.forEach(m => m.visible = false);
                Graph.linkOpacity(0);

                nodeSpheres.forEach(item => {
                    item.sphere.material.color.set("#0284C7");
                    if (item.labelSprite) {
                        item.labelSprite.borderColor = "#CBD5E1";
                    }
                });
            }
        }

        function focusCluster3D(topicId) {
            const t = graphData.topics[topicId];
            if (!t) return;
            const c = t.centroid_3d;
            Graph.cameraPosition(
                { x: c.x * 1.5 + 40, y: c.y * 1.5 + 40, z: c.z * 1.5 + 80 },
                { x: c.x, y: c.y, z: c.z },
                1800
            );
        }

        function toggleLabels() {
            showLabels = !showLabels;
            const btn = document.getElementById('btn-toggle-labels');
            btn.classList.toggle('active', showLabels);
            nodeSpheres.forEach(item => {
                if (item.labelSprite) {
                    item.labelSprite.visible = showLabels;
                }
            });
        }

        function resetCamera() {
            Graph.cameraPosition({ x: 210, y: 170, z: 230 }, { x: 0, y: 0, z: 0 }, 1500);
            document.getElementById('node-details').style.display = 'none';
        }
    </script>
</body>
</html>
"""
    return template.replace("__GRAPH_JSON__", graph_json)


def export_step2_formats(output_dir: Path) -> Dict[str, Path]:
    """
    Generate all Step 2 clustered graph representations.
    Files created:
    - create_graph.cypher
    - graph_data.json
    - graph_2d_viewer.html (D3.js with visible hulls & cluster labels)
    - graph_2d_plotly.html
    - graph_3d_viewer.html (Three.js with 3D cluster billboards)
    - graph_3d_plotly.html
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    results: Dict[str, Path] = {}

    # 1. Cypher script
    cypher_path = output_dir / "create_graph.cypher"
    cypher_path.write_text(generate_step2_cypher_script(), encoding="utf-8")
    results["cypher"] = cypher_path

    # 2. JSON data
    json_path = output_dir / "graph_data.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(generate_step2_json_export(), f, indent=2, ensure_ascii=False)
    results["json"] = json_path

    # 3. 2D D3.js Interactive Viewer
    d3_2d_path = output_dir / "graph_2d_viewer.html"
    d3_2d_path.write_text(generate_step2_d3_2d_viewer_html(), encoding="utf-8")
    results["d3_2d"] = d3_2d_path

    # 4. 2D Plotly
    plotly_2d_path = output_dir / "graph_2d_plotly.html"
    plotly_2d_path.write_text(generate_step2_plotly_2d_html(), encoding="utf-8")
    results["plotly_2d"] = plotly_2d_path

    # 5. 3D Three.js WebGL Viewer
    threejs_3d_path = output_dir / "graph_3d_viewer.html"
    threejs_3d_path.write_text(generate_step2_threejs_viewer_html(), encoding="utf-8")
    results["threejs_3d"] = threejs_3d_path

    # 6. 3D Plotly
    plotly_3d_path = output_dir / "graph_3d_plotly.html"
    plotly_3d_path.write_text(generate_step2_plotly_3d_html(), encoding="utf-8")
    results["plotly_3d"] = plotly_3d_path

    return results


def connect_and_upload_neo4j_step2(
    uri: str = "bolt://localhost:7687",
    user: str = "neo4j",
    password: str = "password",
) -> Dict[str, Any]:
    """
    Connect to a running Neo4j instance and upload the Step 2 clustered graph:
    - 4 TopicCluster nodes
    - 16 StrikeWord nodes
    - 16 [:BELONGS_TO] relationships
    """
    try:
        from neo4j import GraphDatabase
    except ImportError:
        return {"status": "error", "message": "neo4j python package not installed."}

    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            # Clear old demonstration nodes
            session.run("MATCH (w:StrikeWord) DETACH DELETE w")
            session.run("MATCH (c:TopicCluster) DETACH DELETE c")

            # Create constraints
            session.run("CREATE CONSTRAINT word_id_unique IF NOT EXISTS FOR (w:StrikeWord) REQUIRE w.id IS UNIQUE")
            session.run("CREATE CONSTRAINT cluster_id_unique IF NOT EXISTS FOR (c:TopicCluster) REQUIRE c.id IS UNIQUE")

            # Insert 4 Topic Clusters
            for topic_id, t in TOPICS.items():
                c2d = t["centroid_2d"]
                c3d = t["centroid_3d"]
                session.run(
                    """
                    CREATE (:TopicCluster {
                        id: $id,
                        topic_id: $topic_id,
                        name: $name,
                        short_label: $short_label,
                        chinese_name: $chinese_name,
                        causal_role: $causal_role,
                        description: $description,
                        color: $color,
                        centroid_x: $cx, centroid_y: $cy, centroid_z: $cz,
                        step: 2
                    })
                    """,
                    id=f"Topic_{topic_id}",
                    topic_id=topic_id,
                    name=t["name"],
                    short_label=t["short_label"],
                    chinese_name=t["chinese_name"],
                    causal_role=t["causal_role"],
                    description=t["description"],
                    color=t["color"],
                    cx=c2d["x"],
                    cy=c2d["y"],
                    cz=c3d["z"],
                )

            # Insert 16 Words and [:BELONGS_TO]
            nodes = get_step2_nodes()
            for node in nodes:
                session.run(
                    f"""
                    CREATE (w:Topic_{node['topic_id']}:StrikeWord:Word {{
                        id: $id,
                        word: $word,
                        chinese: $chinese,
                        topic_id: $topic_id,
                        topic_name: $topic_name,
                        cluster_label: $cluster_label,
                        causal_role: $causal_role,
                        historical_source: $historical_source,
                        context: $context,
                        color: $color,
                        x: $x, y: $y, z: $z,
                        step: 2,
                        status: 'clustered'
                    }})
                    WITH w
                    MATCH (c:TopicCluster {{topic_id: $topic_id}})
                    CREATE (w)-[:BELONGS_TO {{topic_id: $topic_id}}]->(c)
                    """,
                    id=node["id"],
                    word=node["word"],
                    chinese=node["chinese"],
                    topic_id=node["topic_id"],
                    topic_name=node["topic_name"],
                    cluster_label=node["cluster_label"],
                    causal_role=node["causal_role"],
                    historical_source=node["historical_source"],
                    context=node["context"],
                    color=node["color"],
                    x=node["x"],
                    y=node["y"],
                    z=node["z"],
                )

            # Verification
            w_res = session.run("MATCH (w:StrikeWord) RETURN count(w) AS total")
            w_total = w_res.single()["total"]
            c_res = session.run("MATCH (c:TopicCluster) RETURN count(c) AS total")
            c_total = c_res.single()["total"]
            r_res = session.run("MATCH ()-[r:BELONGS_TO]->() RETURN count(r) AS total")
            r_total = r_res.single()["total"]

        driver.close()
        return {
            "status": "success",
            "message": f"Successfully uploaded Step 2 to Neo4j: {w_total} words, {c_total} topic clusters, {r_total} BELONGS_TO relationships.",
            "total_words": w_total,
            "total_clusters": c_total,
            "total_relationships": r_total,
            "uri": uri,
        }
    except Exception as e:
        return {
            "status": "failed_connection",
            "message": f"Could not connect to Neo4j at {uri}: {e}",
            "hint": "Ensure Neo4j is running and credentials are valid, or load create_graph.cypher manually.",
        }

