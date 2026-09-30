"""
Generators for Neo4j Cypher scripts, JSON graph exports, Plotly (3D & 2D),
and interactive WebGL/SVG viewers (3D & 2D).

Step 1 Focus:
- 16 Dispersed, unclustered vocabulary nodes.
- Identifying colors, topic labels, and causal spoilers REMOVED from the visual layer.
- Latent topic metadata retained solely in properties for future clustering steps.
- Both 3D and 2D interactive HTML viewers provided.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from .data import TOPICS, STRIKE_NODES, UNIFORM_NODE_COLOR


def generate_cypher_script() -> str:
    """Generate Cypher commands to populate Neo4j with the 16 uniform, dispersed word nodes."""
    lines = [
        "// ====================================================================",
        "// 1920s Chinese Labor Strike Causal Knowledge Graph (Step 1)",
        "// Visual Representation: 16 Dispersed, Unclustered Vocabulary Nodes",
        "// (Identifying cluster colors & groupings removed for Step 1 baseline)",
        "// ====================================================================",
        "",
        "// 1. Schema Constraints & Indexes",
        "CREATE CONSTRAINT word_id_unique IF NOT EXISTS",
        "FOR (w:StrikeWord) REQUIRE w.id IS UNIQUE;",
        "",
        "// 2. Clear existing demonstration nodes",
        "MATCH (w:StrikeWord) DETACH DELETE w;",
        "",
        "// 3. Create 16 Dispersed Nodes with uniform label :StrikeWord:Word",
    ]

    for node in STRIKE_NODES:
        cypher_node = (
            f"CREATE (:StrikeWord:Word {{\n"
            f'    id: "{node["id"]}",\n'
            f'    word: "{node["word"]}",\n'
            f'    chinese: "{node["chinese"]}",\n'
            f'    historical_source: "{node["historical_source"]}",\n'
            f'    context: "{node["context"]}",\n'
            f'    x: {node["x"]}, y: {node["y"]}, z: {node["z"]},\n'
            f"    step: 1,\n"
            f'    status: "dispersed_unclustered",\n'
            f'    latent_topic_id: "{node["latent_topic_id"]}",\n'
            f'    latent_topic_name: "{node["latent_topic_name"]}"\n'
            f"}});"
        )
        lines.append(cypher_node)

    lines.extend([
        "",
        "// ====================================================================",
        "// Step 1 Query: Retrieve all 16 dispersed nodes with coordinates",
        "// ====================================================================",
        "MATCH (w:StrikeWord)",
        "RETURN w.id AS id, w.word AS word, w.chinese AS chinese,",
        "       w.x AS x, w.y AS y, w.z AS z, w.historical_source AS source;",
        "",
    ])
    return "\n".join(lines)


def generate_json_export() -> Dict[str, Any]:
    """Generate structured JSON representation of the graph."""
    return {
        "metadata": {
            "title": "1920s Chinese Strike Causal Knowledge Graph",
            "step": 1,
            "description": "16 dispersed words from 1920s newspaper press before clustering.",
            "total_nodes": len(STRIKE_NODES),
            "total_edges": 0,
            "clustering_mode": "unclustered_dispersed",
        },
        "nodes": STRIKE_NODES,
        "edges": [],
    }


def generate_plotly_3d_html() -> str:
    """Generate a self-contained Plotly 3D scatter graph with uniform styling (no cluster spoilers)."""
    import plotly.graph_objects as go

    fig = go.Figure()

    xs = [n["x"] for n in STRIKE_NODES]
    ys = [n["y"] for n in STRIKE_NODES]
    zs = [n["z"] for n in STRIKE_NODES]
    labels = [f"<b>{n['word']}</b><br>({n['chinese']})" for n in STRIKE_NODES]
    hover_texts = [
        f"<b>{n['word']}</b> ({n['chinese']})<br>"
        f"<b>Historical Source:</b> {n['historical_source']}<br>"
        f"<b>Archival Context:</b> {n['context']}<br>"
        f"<b>3D Coordinates:</b> ({n['x']}, {n['y']}, {n['z']})"
        for n in STRIKE_NODES
    ]

    fig.add_trace(
        go.Scatter3d(
            x=xs,
            y=ys,
            z=zs,
            mode="markers+text",
            name="1920s Press Vocabulary (Dispersed Nodes)",
            text=labels,
            textposition="top center",
            textfont=dict(size=11, color="#F0F4F8"),
            hoverinfo="text",
            hovertext=hover_texts,
            marker=dict(
                size=8,
                color=UNIFORM_NODE_COLOR,
                opacity=0.95,
                line=dict(color="#FFFFFF", width=1.5),
                symbol="circle",
            ),
        )
    )

    fig.update_layout(
        title=dict(
            text=(
                "<b>1920s Chinese Newspaper Labor Strike: Knowledge Graph (3D)</b><br>"
                "<sup>Step 1: 16 Dispersed Vocabulary Nodes (Raw Unclustered Baseline)</sup>"
            ),
            font=dict(size=18, color="#FFFFFF"),
            x=0.5,
            xanchor="center",
            y=0.95,
        ),
        paper_bgcolor="#0E131F",
        plot_bgcolor="#0E131F",
        legend=dict(
            font=dict(color="#E0E6ED", size=11),
            bgcolor="rgba(20, 27, 45, 0.8)",
            bordercolor="rgba(255, 255, 255, 0.2)",
            borderwidth=1,
            x=0.02,
            y=0.95,
        ),
        scene=dict(
            xaxis=dict(
                title=dict(text="Spatial X", font=dict(color="#9CA3AF")),
                backgroundcolor="#111827",
                gridcolor="#1F2937",
                showbackground=True,
                zerolinecolor="#374151",
                tickfont=dict(color="#9CA3AF"),
            ),
            yaxis=dict(
                title=dict(text="Spatial Y", font=dict(color="#9CA3AF")),
                backgroundcolor="#111827",
                gridcolor="#1F2937",
                showbackground=True,
                zerolinecolor="#374151",
                tickfont=dict(color="#9CA3AF"),
            ),
            zaxis=dict(
                title=dict(text="Spatial Z", font=dict(color="#9CA3AF")),
                backgroundcolor="#111827",
                gridcolor="#1F2937",
                showbackground=True,
                zerolinecolor="#374151",
                tickfont=dict(color="#9CA3AF"),
            ),
            camera=dict(
                eye=dict(x=1.6, y=1.6, z=1.2),
                up=dict(x=0, y=0, z=1),
            ),
        ),
        margin=dict(l=0, r=0, b=0, t=80),
    )

    return fig.to_html(include_plotlyjs="cdn", full_html=True)


def generate_plotly_2d_html() -> str:
    """Generate a self-contained Plotly 2D scatter graph with uniform styling (no cluster spoilers)."""
    import plotly.graph_objects as go

    fig = go.Figure()

    xs = [n["x"] for n in STRIKE_NODES]
    ys = [n["y"] for n in STRIKE_NODES]
    labels = [f"<b>{n['word']}</b><br>({n['chinese']})" for n in STRIKE_NODES]
    hover_texts = [
        f"<b>{n['word']}</b> ({n['chinese']})<br>"
        f"<b>Historical Source:</b> {n['historical_source']}<br>"
        f"<b>Archival Context:</b> {n['context']}<br>"
        f"<b>2D Coordinates:</b> ({n['x']}, {n['y']})"
        for n in STRIKE_NODES
    ]

    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="markers+text",
            name="1920s Press Vocabulary (Dispersed Nodes)",
            text=labels,
            textposition="top center",
            textfont=dict(size=11, color="#F0F4F8"),
            hoverinfo="text",
            hovertext=hover_texts,
            marker=dict(
                size=14,
                color=UNIFORM_NODE_COLOR,
                opacity=0.95,
                line=dict(color="#FFFFFF", width=2),
                symbol="circle",
            ),
        )
    )

    fig.update_layout(
        title=dict(
            text=(
                "<b>1920s Chinese Newspaper Labor Strike: Knowledge Graph (2D)</b><br>"
                "<sup>Step 1: 16 Dispersed Vocabulary Nodes (Raw Unclustered Baseline)</sup>"
            ),
            font=dict(size=18, color="#FFFFFF"),
            x=0.5,
            xanchor="center",
            y=0.95,
        ),
        paper_bgcolor="#0E131F",
        plot_bgcolor="#0E131F",
        legend=dict(
            font=dict(color="#E0E6ED", size=11),
            bgcolor="rgba(20, 27, 45, 0.8)",
            bordercolor="rgba(255, 255, 255, 0.2)",
            borderwidth=1,
            x=0.02,
            y=0.95,
        ),
        xaxis=dict(
            title=dict(text="Spatial X", font=dict(color="#9CA3AF")),
            gridcolor="#1F2937",
            zerolinecolor="#374151",
            tickfont=dict(color="#9CA3AF"),
        ),
        yaxis=dict(
            title=dict(text="Spatial Y", font=dict(color="#9CA3AF")),
            gridcolor="#1F2937",
            zerolinecolor="#374151",
            tickfont=dict(color="#9CA3AF"),
            scaleanchor="x",
            scaleratio=1,
        ),
        margin=dict(l=60, r=60, b=60, t=90),
    )

    return fig.to_html(include_plotlyjs="cdn", full_html=True)


def generate_threejs_viewer_html() -> str:
    """Generate a rich, interactive 3D WebGL viewer with uniform appearance (no cluster hints)."""
    graph_json = json.dumps(generate_json_export())

    template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D Causal Graph - Step 1: Dispersed Words</title>
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
            background: radial-gradient(circle at center, #111827 0%, #030712 100%);
            color: #F3F4F6;
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
            background: rgba(17, 24, 39, 0.85);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 12px;
            padding: 20px 24px;
            max-width: 400px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
        }
        .hud-title {
            font-size: 17px;
            font-weight: 700;
            color: #F9FAFB;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .badge {
            display: inline-block;
            background: #0284C7;
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
            color: #9CA3AF;
            line-height: 1.5;
            margin-bottom: 16px;
        }
        .status-box {
            background: rgba(31, 41, 55, 0.7);
            border-radius: 8px;
            padding: 10px 12px;
            margin-bottom: 16px;
            border-left: 3px solid #38BDF8;
            font-size: 12px;
            color: #D1D5DB;
            line-height: 1.4;
        }
        .controls-group {
            display: flex;
            gap: 8px;
            margin-top: 10px;
        }
        .btn {
            flex: 1;
            background: #374151;
            border: 1px solid #4B5563;
            color: #F3F4F6;
            padding: 8px 12px;
            font-size: 12px;
            font-weight: 500;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn:hover {
            background: #4B5563;
            border-color: #6B7280;
        }
        .btn.active {
            background: #0284C7;
            border-color: #38BDF8;
            color: #FFFFFF;
        }
        #node-details {
            position: absolute;
            bottom: 24px;
            right: 24px;
            z-index: 10;
            background: rgba(17, 24, 39, 0.9);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 12px;
            padding: 20px 24px;
            max-width: 360px;
            display: none;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
        }
        #node-details h3 {
            font-size: 18px;
            color: #F9FAFB;
            margin-bottom: 4px;
        }
        #node-details .chinese {
            font-size: 14px;
            color: #38BDF8;
            margin-bottom: 12px;
            font-weight: 600;
        }
        #node-details .meta-row {
            font-size: 12px;
            color: #D1D5DB;
            margin-bottom: 6px;
            line-height: 1.4;
        }
        #node-details .meta-row strong {
            color: #93C5FD;
        }
    </style>
</head>
<body>
    <div id="3d-graph"></div>

    <div class="hud-panel">
        <div class="hud-title">
            <span>China Strike Knowledge Graph</span>
            <span class="badge">Step 1 • 3D</span>
        </div>
        <div class="hud-desc">
            16 dispersed vocabulary terms extracted from 1920s newspaper press (<i>The China Mail</i>, Hong Kong MMIS).
        </div>

        <div class="status-box">
            <strong>State:</strong> Dispersed, unclustered terms in 3D coordinate space. Cluster groupings and causal connections will be modeled in subsequent steps.
        </div>

        <div class="controls-group">
            <button class="btn active" id="btn-toggle-labels" onclick="toggleLabels()">Toggle Labels</button>
            <button class="btn" onclick="resetCamera()">Reset View</button>
        </div>
    </div>

    <div id="node-details">
        <h3 id="det-word">Word</h3>
        <div class="chinese" id="det-chinese">中文</div>
        <div class="meta-row"><strong>Historical Source:</strong> <span id="det-source"></span></div>
        <div class="meta-row"><strong>Archival Context:</strong> <span id="det-context"></span></div>
        <div class="meta-row"><strong>3D Coordinates:</strong> <span id="det-coords"></span></div>
    </div>

    <script>
        const graphData = __GRAPH_JSON__;
        let showLabels = true;
        const uniformColor = '__UNIFORM_COLOR__';

        const gData = {
            nodes: graphData.nodes.map(n => ({
                id: n.id,
                name: n.word,
                chinese: n.chinese,
                historical_source: n.historical_source,
                context: n.context,
                fx: n.x,
                fy: n.y,
                fz: n.z,
                color: uniformColor
            })),
            links: []
        };

        const Graph = ForceGraph3D()(document.getElementById('3d-graph'))
            .graphData(gData)
            .backgroundColor('#030712')
            .showNavInfo(false)
            .nodeRelSize(7)
            .nodeColor(node => uniformColor)
            .nodeThreeObject(node => {
                const group = new THREE.Group();

                const sphereGeometry = new THREE.SphereGeometry(3.5, 24, 24);
                const sphereMaterial = new THREE.MeshLambertMaterial({
                    color: uniformColor,
                    transparent: true,
                    opacity: 0.95
                });
                const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
                group.add(sphere);

                if (showLabels) {
                    const sprite = new SpriteText(`${node.name}\\n(${node.chinese})`);
                    sprite.color = '#F3F4F6';
                    sprite.textHeight = 3.2;
                    sprite.position.y = 7;
                    sprite.backgroundColor = 'rgba(15, 23, 42, 0.75)';
                    sprite.padding = 2;
                    sprite.borderRadius = 3;
                    group.add(sprite);
                }

                return group;
            })
            .onNodeClick(node => {
                const distance = 80;
                const distRatio = 1 + distance/Math.hypot(node.fx, node.fy, node.fz);
                Graph.cameraPosition(
                    { x: node.fx * distRatio, y: node.fy * distRatio, z: node.fz * distRatio },
                    { x: node.fx, y: node.fy, z: node.fz },
                    2000
                );

                document.getElementById('node-details').style.display = 'block';
                document.getElementById('det-word').innerText = node.name;
                document.getElementById('det-chinese').innerText = node.chinese;
                document.getElementById('det-source').innerText = node.historical_source;
                document.getElementById('det-context').innerText = node.context;
                document.getElementById('det-coords').innerText = `(${node.fx}, ${node.fy}, ${node.fz})`;
            })
            .onBackgroundClick(() => {
                document.getElementById('node-details').style.display = 'none';
            });

        Graph.cameraPosition({ x: 180, y: 140, z: 200 });

        function toggleLabels() {
            showLabels = !showLabels;
            const btn = document.getElementById('btn-toggle-labels');
            btn.classList.toggle('active', showLabels);
            Graph.refresh();
        }

        function resetCamera() {
            Graph.cameraPosition({ x: 180, y: 140, z: 200 }, { x: 0, y: 0, z: 0 }, 1500);
            document.getElementById('node-details').style.display = 'none';
        }
    </script>
</body>
</html>
"""
    return template.replace("__GRAPH_JSON__", graph_json).replace("__UNIFORM_COLOR__", UNIFORM_NODE_COLOR)


def generate_d3_2d_viewer_html() -> str:
    """Generate a rich, interactive 2D SVG/D3.js viewer with drag, zoom, pan, and uniform styling."""
    graph_json = json.dumps(generate_json_export())

    template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>2D Causal Graph - Step 1: Dispersed Words</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            background: radial-gradient(circle at center, #111827 0%, #030712 100%);
            color: #F3F4F6;
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
        }
        #svg-canvas:active {
            cursor: grabbing;
        }
        .hud-panel {
            position: absolute;
            top: 20px;
            left: 20px;
            z-index: 10;
            background: rgba(17, 24, 39, 0.85);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 12px;
            padding: 20px 24px;
            max-width: 400px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
        }
        .hud-title {
            font-size: 17px;
            font-weight: 700;
            color: #F9FAFB;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .badge {
            display: inline-block;
            background: #0284C7;
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
            color: #9CA3AF;
            line-height: 1.5;
            margin-bottom: 16px;
        }
        .status-box {
            background: rgba(31, 41, 55, 0.7);
            border-radius: 8px;
            padding: 10px 12px;
            margin-bottom: 16px;
            border-left: 3px solid #38BDF8;
            font-size: 12px;
            color: #D1D5DB;
            line-height: 1.4;
        }
        .controls-group {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }
        .btn {
            background: #374151;
            border: 1px solid #4B5563;
            color: #F3F4F6;
            padding: 7px 12px;
            font-size: 12px;
            font-weight: 500;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn:hover {
            background: #4B5563;
            border-color: #6B7280;
        }
        .btn.active {
            background: #0284C7;
            border-color: #38BDF8;
            color: #FFFFFF;
        }
        #node-details {
            position: absolute;
            bottom: 24px;
            right: 24px;
            z-index: 10;
            background: rgba(17, 24, 39, 0.9);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 12px;
            padding: 20px 24px;
            max-width: 360px;
            display: none;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
        }
        #node-details h3 {
            font-size: 18px;
            color: #F9FAFB;
            margin-bottom: 4px;
        }
        #node-details .chinese {
            font-size: 14px;
            color: #38BDF8;
            margin-bottom: 12px;
            font-weight: 600;
        }
        #node-details .meta-row {
            font-size: 12px;
            color: #D1D5DB;
            margin-bottom: 6px;
            line-height: 1.4;
        }
        #node-details .meta-row strong {
            color: #93C5FD;
        }
        .close-btn {
            position: absolute;
            top: 12px;
            right: 12px;
            background: none;
            border: none;
            color: #9CA3AF;
            font-size: 18px;
            cursor: pointer;
        }
        .close-btn:hover {
            color: #FFFFFF;
        }
        /* SVG Graph Styling */
        .node-circle {
            cursor: pointer;
            transition: r 0.2s ease, filter 0.2s ease;
        }
        .node-circle:hover {
            filter: drop-shadow(0 0 10px #38BDF8);
        }
        .node-halo {
            pointer-events: none;
            animation: pulse-halo 3s infinite ease-in-out;
        }
        @keyframes pulse-halo {
            0% { opacity: 0.3; transform: scale(1); }
            50% { opacity: 0.6; transform: scale(1.15); }
            100% { opacity: 0.3; transform: scale(1); }
        }
        .node-label-pill {
            pointer-events: none;
        }
        .label-bg {
            fill: rgba(15, 23, 42, 0.85);
            stroke: rgba(255, 255, 255, 0.15);
            stroke-width: 1px;
            rx: 5px;
            ry: 5px;
        }
        .label-text-en {
            fill: #F3F4F6;
            font-size: 11px;
            font-weight: 600;
            text-anchor: middle;
            dominant-baseline: central;
        }
        .label-text-zh {
            fill: #38BDF8;
            font-size: 10px;
            font-weight: 500;
            text-anchor: middle;
            dominant-baseline: central;
        }
        .selected-ring {
            fill: none;
            stroke: #FBBF24;
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
            <span class="badge">Step 1 • 2D</span>
        </div>
        <div class="hud-desc">
            16 dispersed vocabulary terms from 1920s newspaper press (<i>The China Mail</i>, Hong Kong MMIS).
        </div>

        <div class="status-box">
            <strong>State:</strong> Dispersed, unclustered terms on a 2D plane. Drag nodes to explore, or scroll to zoom. Cluster groupings and causal directed edges will be introduced in subsequent steps.
        </div>

        <div class="controls-group">
            <button class="btn active" id="btn-toggle-labels" onclick="toggleLabels()">Toggle Labels</button>
            <button class="btn" onclick="zoomIn()">Zoom (+)</button>
            <button class="btn" onclick="zoomOut()">Zoom (-)</button>
            <button class="btn" onclick="resetZoom()">Reset View</button>
        </div>
    </div>

    <div id="node-details">
        <button class="close-btn" onclick="closeDetails()">&times;</button>
        <h3 id="det-word">Word</h3>
        <div class="chinese" id="det-chinese">中文</div>
        <div class="meta-row"><strong>Historical Source:</strong> <span id="det-source"></span></div>
        <div class="meta-row"><strong>Archival Context:</strong> <span id="det-context"></span></div>
        <div class="meta-row"><strong>2D Coordinates:</strong> <span id="det-coords"></span></div>
    </div>

    <script>
        const graphData = __GRAPH_JSON__;
        let showLabels = true;
        let selectedNodeId = null;
        const uniformColor = '__UNIFORM_COLOR__';

        const svg = d3.select("#svg-canvas");
        const width = window.innerWidth;
        const height = window.innerHeight;
        svg.attr("width", width).attr("height", height);

        // Definitions: gradients and filters
        const defs = svg.append("defs");

        // Glowing gradient for nodes
        const grad = defs.append("radialGradient")
            .attr("id", "node-grad")
            .attr("cx", "35%")
            .attr("cy", "35%");
        grad.append("stop").attr("offset", "0%").attr("stop-color", "#7DD3FC");
        grad.append("stop").attr("offset", "100%").attr("stop-color", "#0284C7");

        // Background subtle grid pattern
        const pattern = defs.append("pattern")
            .attr("id", "grid")
            .attr("width", 40)
            .attr("height", 40)
            .attr("patternUnits", "userSpaceOnUse");
        pattern.append("circle")
            .attr("cx", 20)
            .attr("cy", 20)
            .attr("r", 1)
            .attr("fill", "rgba(255, 255, 255, 0.08)");

        // Background grid rect
        svg.append("rect")
            .attr("width", "100%")
            .attr("height", "100%")
            .attr("fill", "url(#grid)");

        // Root zoomable container
        const container = svg.append("g").attr("id", "zoom-container");

        // Scale coordinates to fit comfortable screen bounds
        const scaleFactor = 4.8;
        const nodes = graphData.nodes.map(n => ({
            ...n,
            x: width / 2 + n.x * scaleFactor,
            y: height / 2 - n.y * scaleFactor,
            origX: width / 2 + n.x * scaleFactor,
            origY: height / 2 - n.y * scaleFactor
        }));

        // Zoom Behavior
        const zoom = d3.zoom()
            .scaleExtent([0.3, 3])
            .on("zoom", (event) => {
                container.attr("transform", event.transform);
            });
        svg.call(zoom);

        // Drag Behavior
        const drag = d3.drag()
            .on("start", function(event, d) {
                d3.select(this).raise();
            })
            .on("drag", function(event, d) {
                d.x = event.x;
                d.y = event.y;
                d3.select(this).attr("transform", `translate(${d.x}, ${d.y})`);
            });

        // Render Nodes Group
        const nodeGroups = container.selectAll(".node-group")
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

        // Pulsing Halo Circle
        nodeGroups.append("circle")
            .attr("class", "node-halo")
            .attr("r", 20)
            .attr("fill", uniformColor)
            .attr("opacity", 0.15);

        // Core Node Circle
        nodeGroups.append("circle")
            .attr("class", "node-circle")
            .attr("r", 12)
            .attr("fill", "url(#node-grad)")
            .attr("stroke", "#FFFFFF")
            .attr("stroke-width", 2);

        // Selection Ring
        nodeGroups.append("circle")
            .attr("class", "selected-ring")
            .attr("r", 18)
            .attr("display", d => (d.id === selectedNodeId ? "block" : "none"));

        // Label Pill
        const labelGroups = nodeGroups.append("g")
            .attr("class", "node-label-pill")
            .attr("transform", "translate(0, 24)");

        // Background pill
        labelGroups.append("rect")
            .attr("class", "label-bg")
            .attr("x", -65)
            .attr("y", -8)
            .attr("width", 130)
            .attr("height", 32);

        // English text
        labelGroups.append("text")
            .attr("class", "label-text-en")
            .attr("y", 2)
            .text(d => d.word);

        // Chinese text
        labelGroups.append("text")
            .attr("class", "label-text-zh")
            .attr("y", 16)
            .text(d => d.chinese);

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
            document.getElementById("det-source").innerText = d.historical_source;
            document.getElementById("det-context").innerText = d.context;
            document.getElementById("det-coords").innerText = `(${d.x.toFixed(1)}, ${d.y.toFixed(1)})`;
        }

        function updateSelection() {
            container.selectAll(".selected-ring")
                .attr("display", d => (d.id === selectedNodeId ? "block" : "none"));
        }

        function closeDetails() {
            document.getElementById("node-details").style.display = "none";
            selectedNodeId = null;
            updateSelection();
        }

        function toggleLabels() {
            showLabels = !showLabels;
            const btn = document.getElementById("btn-toggle-labels");
            btn.classList.toggle("active", showLabels);
            container.selectAll(".node-label-pill")
                .attr("display", showLabels ? "block" : "none");
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
    return template.replace("__GRAPH_JSON__", graph_json).replace("__UNIFORM_COLOR__", UNIFORM_NODE_COLOR)


def export_all_formats(output_dir: Optional[Path] = None) -> Dict[str, Path]:
    """
    Generate all graph representations and save them to output_dir.
    Files created:
    - create_graph.cypher        (Neo4j Cypher ingestion)
    - graph_data.json            (Structured JSON export)
    - graph_3d_plotly.html       (Plotly 3D visualizer)
    - graph_3d_viewer.html       (WebGL Three.js 3D viewer)
    - graph_2d_plotly.html       (Plotly 2D visualizer)
    - graph_2d_viewer.html       (D3.js 2D interactive viewer)
    """
    if output_dir is None:
        output_dir = Path(__file__).resolve().parents[3] / "artifacts"
    output_dir.mkdir(parents=True, exist_ok=True)

    results: Dict[str, Path] = {}

    # 1. Cypher script
    cypher_path = output_dir / "create_graph.cypher"
    cypher_path.write_text(generate_cypher_script(), encoding="utf-8")
    results["cypher"] = cypher_path

    # 2. JSON data
    json_path = output_dir / "graph_data.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(generate_json_export(), f, indent=2, ensure_ascii=False)
    results["json"] = json_path

    # 3. Plotly 3D HTML
    plotly_3d_path = output_dir / "graph_3d_plotly.html"
    plotly_3d_path.write_text(generate_plotly_3d_html(), encoding="utf-8")
    results["plotly_3d"] = plotly_3d_path

    # 4. WebGL Three.js HTML Viewer (3D)
    threejs_path = output_dir / "graph_3d_viewer.html"
    threejs_path.write_text(generate_threejs_viewer_html(), encoding="utf-8")
    results["threejs_3d"] = threejs_path

    # 5. Plotly 2D HTML
    plotly_2d_path = output_dir / "graph_2d_plotly.html"
    plotly_2d_path.write_text(generate_plotly_2d_html(), encoding="utf-8")
    results["plotly_2d"] = plotly_2d_path

    # 6. D3.js 2D HTML Viewer
    d3_2d_path = output_dir / "graph_2d_viewer.html"
    d3_2d_path.write_text(generate_d3_2d_viewer_html(), encoding="utf-8")
    results["d3_2d"] = d3_2d_path

    return results


def connect_and_upload_neo4j(
    uri: str = "bolt://localhost:7687",
    user: str = "neo4j",
    password: str = "password",
) -> Dict[str, Any]:
    """
    Connect to a running Neo4j instance and upload the 16 uniform nodes.
    Returns dictionary with execution results.
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

            # Create constraint
            session.run(
                "CREATE CONSTRAINT word_id_unique IF NOT EXISTS "
                "FOR (w:StrikeWord) REQUIRE w.id IS UNIQUE"
            )

            # Insert nodes in batch with uniform label :StrikeWord:Word
            query = """
            UNWIND $batch AS item
            CREATE (w:StrikeWord:Word {
                id: item.id,
                word: item.word,
                chinese: item.chinese,
                historical_source: item.historical_source,
                context: item.context,
                x: item.x,
                y: item.y,
                z: item.z,
                step: 1,
                status: 'dispersed_unclustered',
                latent_topic_id: item.latent_topic_id,
                latent_topic_name: item.latent_topic_name
            })
            """
            batch = [dict(n) for n in STRIKE_NODES]
            session.run(query, batch=batch)

            # Count created nodes
            result = session.run("MATCH (w:StrikeWord) RETURN count(w) AS total")
            total = result.single()["total"]

        driver.close()
        return {
            "status": "success",
            "message": f"Successfully connected to Neo4j and created {total} uniform nodes.",
            "total_nodes": total,
            "uri": uri,
        }
    except Exception as e:
        return {
            "status": "failed_connection",
            "message": f"Could not connect to Neo4j at {uri}: {e}",
            "hint": "Ensure Neo4j is running and credentials are valid, or load create_graph.cypher manually.",
        }
