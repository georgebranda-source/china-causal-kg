"""
Step 3 Causal Knowledge Graph Visualizers and Exporters.

Step 3 Focus:
- Directed Causal Relationships connecting clusters:
    * Topic A (Heavy Rain) ──➔ Topic C (Traffic Gridlock)
    * Topic B (High Winds) ──➔ Topic C (Traffic Gridlock)
    * Topic C (Traffic Gridlock) ──➔ Topic D (Daily Delays)
- Zero node movement: the 16 vocabulary nodes remain in their exact initial positions.
- NO LABELS ON THE EDGES: Clean, elegant directed flow arrows/vectors without text clutter.
- Pure crisp white background (#FFFFFF) with dark typography (#0F172A).
- Interactive 3-step mode toggle (1. Dispersed Words -> 2. Clustered Topics -> 3. Causal Graph).
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from .data import (
    TOPICS,
    CAUSAL_EDGES,
    WORD_CAUSAL_LINKS,
    get_step3_nodes,
    get_step2_intra_links,
    get_causal_edges,
    get_word_causal_links,
)


def generate_step3_cypher_script() -> str:
    """Generate Cypher commands to populate Neo4j with the complete Step 3 Causal Knowledge Graph."""
    nodes = get_step3_nodes()
    causal_edges = get_causal_edges()
    word_links = get_word_causal_links()

    lines = [
        "// ====================================================================",
        "// Weather & Commuting Disruption: Causal Knowledge Graph (Step 3)",
        "// Full Causal Induction: Directed Relationships Between Topic Clusters",
        "// Causal Flow Architecture: (A: Heavy Rain) ──➔ (C: Traffic Gridlock) ── (B: High Winds)",
        "//                           (C: Traffic Gridlock) ──➔ (D: Daily Delays)",
        "// Note: No labels on edges for clean visual representation",
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
            f'    step: 3\n'
            f"}});"
        )
        lines.append(cluster_stmt)

    lines.extend([
        "",
        "// 4. Create 16 Vocabulary Nodes with Initial Coordinates and BELONGS_TO links",
    ])

    for node in nodes:
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
            f'    step: 3,\n'
            f'    status: "causally_linked"\n'
            f"}})\n"
            f'WITH w_{node["id"]}\n'
            f'MATCH (c:TopicCluster {{topic_id: "{node["topic_id"]}"}})\n'
            f'CREATE (w_{node["id"]})-[:BELONGS_TO {{topic_id: "{node["topic_id"]}"}}]->(c);'
        )
        lines.append(node_stmt)

    lines.extend([
        "",
        "// 5. Create Macro Directed Causal Relationships Between Clusters (Clean without edge labels)",
    ])

    for edge in causal_edges:
        causal_stmt = (
            f"MATCH (src:TopicCluster {{topic_id: '{edge['source']}'}}), "
            f"(tgt:TopicCluster {{topic_id: '{edge['target']}'}})\n"
            f"CREATE (src)-[:CAUSES {{\n"
            f"    id: '{edge['id']}',\n"
            f"    causal_type: '{edge['causal_type']}',\n"
            f"    relationship: '{edge['relationship']}',\n"
            f"    mechanism: \"{edge['mechanism']}\",\n"
            f"    weight: {edge['weight']},\n"
            f"    step: 3\n"
            f"}}]->(tgt);"
        )
        lines.append(causal_stmt)

    lines.extend([
        "",
        "// 6. Create Micro Semantic Causal Relationships Between Representative Words",
    ])

    for link in word_links:
        word_stmt = (
            f"MATCH (w1:StrikeWord {{id: '{link['source']}'}}), (w2:StrikeWord {{id: '{link['target']}'}})\n"
            f"CREATE (w1)-[:LEADS_TO {{\n"
            f'    mechanism: "{link["mechanism"]}",\n'
            f'    type: "{link["type"]}"\n'
            f"}}]->(w2);"
        )
        lines.append(word_stmt)

    lines.extend([
        "",
        "// ====================================================================",
        "// Step 3 Queries: Explore the Causal Knowledge Graph",
        "// ====================================================================",
        "// Query 1: Retrieve Macro Causal Backbone (Clusters & Directed Causal Links)",
        "MATCH (c1:TopicCluster)-[r:CAUSES]->(c2:TopicCluster)",
        "RETURN c1.name AS Cause, c2.name AS Effect, r.mechanism AS Mechanism;",
        "",
        "// Query 2: Retrieve Full Graph (Clusters, Words, and Causal Connections)",
        "MATCH (c:TopicCluster)<-[:BELONGS_TO]-(w:StrikeWord)",
        "OPTIONAL MATCH (c)-[r:CAUSES]->(c2:TopicCluster)",
        "RETURN c, w, r, c2;",
    ])

    return "\n".join(lines)


def generate_step3_json_export() -> Dict[str, Any]:
    """Generate structured JSON representation of Step 3 Causal Graph."""
    return {
        "metadata": {
            "title": "Weather & Commuting Disruption: Causal Knowledge Graph",
            "step": 3,
            "description": "Directed causal graph connecting clusters (A, B -> C -> D) over stationary node coordinates with clean unlabeled arrows.",
            "total_nodes": len(get_step3_nodes()),
            "total_topics": len(TOPICS),
            "total_causal_edges": len(CAUSAL_EDGES),
            "total_intra_links": len(get_step2_intra_links()),
            "total_micro_causal_links": len(get_word_causal_links()),
            "theme": "pure_white_background",
            "clustering_mode": "stationary_spatial_clusters_with_causality",
            "edge_labels": "none_clean_arrows",
        },
        "topics": TOPICS,
        "nodes": get_step3_nodes(),
        "intra_cluster_links": get_step2_intra_links(),
        "causal_edges": get_causal_edges(),
        "word_causal_links": get_word_causal_links(),
    }


def generate_step3_plotly_2d_html() -> str:
    """Generate Plotly 2D scatter graph with visible topic clusters and directed causal flow arrows (NO edge labels)."""
    import plotly.graph_objects as go

    nodes = get_step3_nodes()
    causal_edges = get_causal_edges()
    fig = go.Figure()

    # 1. Traced cluster boundaries (translucent rounded capsules)
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
                    line=dict(color=t["color"], width=1.0, dash="dot"),
                    hoverinfo="skip",
                    showlegend=False,
                    opacity=0.4,
                )
            )

    # 3. Add traces per topic cluster (Vocabulary nodes)
    for topic_id, t in TOPICS.items():
        t_nodes = [n for n in nodes if n["topic_id"] == topic_id]
        xs = [n["x"] for n in t_nodes]
        ys = [n["y"] for n in t_nodes]
        labels = [f"<b>{n['word']}</b>" for n in t_nodes]
        
        # Smart text positioning: upper nodes top, lower nodes bottom
        textpos = []
        for n in t_nodes:
            if n["y"] < t["centroid_2d"]["y"] - 5:
                textpos.append("bottom center")
            else:
                textpos.append("top center")

        hover_texts = [
            f"<b>{n['word']}</b><br>"
            f"<b>Topic:</b> {t['name']}<br>"
            f"<b>Causal Role:</b> {t['causal_role']}<br>"
            f"<b>Context:</b> {n['context']}<br>"
            f"<b>Coordinates:</b> ({n['x']}, {n['y']})"
            for n in t_nodes
        ]

        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="markers+text",
                name=f"{t['name']}",
                text=labels,
                textposition=textpos,
                textfont=dict(size=10.5, color="#1E293B"),
                hoverinfo="text",
                hovertext=hover_texts,
                marker=dict(
                    size=13,
                    color=t["color"],
                    opacity=0.95,
                    line=dict(color="#FFFFFF", width=2.5),
                    symbol="circle",
                ),
            )
        )

    # 4. Minimal Cluster Topic Labels MOVED UP Above Each Topic Box
    for topic_id, t in TOPICS.items():
        t_nodes = [n for n in nodes if n["topic_id"] == topic_id]
        max_y = max(n["y"] for n in t_nodes) + 8
        c = t["centroid_2d"]
        badge_y = max_y + 11
        badge_x = c["x"]

        fig.add_annotation(
            x=badge_x,
            y=badge_y,
            text=f"<b>{t['name']}</b>",
            showarrow=False,
            font=dict(size=11, color="#0F172A", family="Arial, sans-serif"),
            bgcolor="rgba(255, 255, 255, 0.95)",
            bordercolor=t["color"],
            borderwidth=1.2,
            borderpad=5,
            align="center",
        )

    # 5. Prominent, Sleek Directed Causal Arrows (NO EDGE LABELS)
    arrow_corridors = [
        # (A -> C): Rain to Traffic Gridlock
        {
            "start": (-38.0, 32.0),
            "end": (-18.0, 10.0),
            "color": "#0284C7",
        },
        # (B -> C): Wind to Traffic Gridlock
        {
            "start": (-38.0, -24.0),
            "end": (-18.0, -8.0),
            "color": "#0D9488",
        },
        # (C -> D): Traffic Gridlock to Delays
        {
            "start": (28.0, 0.0),
            "end": (52.0, 0.0),
            "color": "#EA580C",
        },
    ]

    for p in arrow_corridors:
        # Subtle glow underlay for depth
        fig.add_annotation(
            x=p["end"][0],
            y=p["end"][1],
            ax=p["start"][0],
            ay=p["start"][1],
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=2,
            arrowsize=1.2,
            arrowwidth=5.5,
            arrowcolor=p["color"],
            opacity=0.22,
            text="",
        )
        # Main crisp foreground arrow
        fig.add_annotation(
            x=p["end"][0],
            y=p["end"][1],
            ax=p["start"][0],
            ay=p["start"][1],
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=2,
            arrowsize=1.1,
            arrowwidth=2.8,
            arrowcolor=p["color"],
            opacity=0.95,
            text="",
        )

    fig.update_layout(
        title=dict(
            text=(
                "<b>Weather & Commuting Disruption: Causal Knowledge Graph (2D)</b><br>"
                "<sup>Step 3: Directed Causal Graph (A, B ➔ C ➔ D Influence Flow)</sup>"
            ),
            font=dict(size=17, color="#0F172A"),
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
            title=dict(text="Spatial X (Causal Direction ➔)", font=dict(color="#475569")),
            gridcolor="#F1F5F9",
            zerolinecolor="#E2E8F0",
            tickfont=dict(color="#64748B"),
            range=[-110, 120],
        ),
        yaxis=dict(
            title=dict(text="Spatial Y", font=dict(color="#475569")),
            gridcolor="#F1F5F9",
            zerolinecolor="#E2E8F0",
            tickfont=dict(color="#64748B"),
            scaleanchor="x",
            scaleratio=1,
            range=[-100, 105],
        ),
        margin=dict(l=60, r=60, b=60, t=100),
    )

    return fig.to_html(include_plotlyjs="cdn", full_html=True)


def generate_step3_d3_2d_viewer_html() -> str:
    """Generate D3.js 2D SVG viewer with animated causal flow vectors and 3-step transition (NO edge labels)."""
    graph_json = json.dumps(generate_step3_json_export())

    template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>2D Causal Graph - Step 3: Directed Causal Induction</title>
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
            max-width: 440px;
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
            color: #64748B;
            line-height: 1.5;
            margin-bottom: 12px;
        }
        .callout-box {
            font-size: 11px;
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            padding: 8px 10px;
            margin-bottom: 12px;
            color: #475569;
            line-height: 1.4;
        }
        .causal-blueprint {
            background: #F8FAFC;
            border-radius: 8px;
            padding: 10px 12px;
            margin-bottom: 14px;
            border-left: 3px solid #0284C7;
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
        .step-toggle-group {
            display: flex;
            gap: 4px;
            margin-bottom: 12px;
            background: #F1F5F9;
            padding: 3px;
            border-radius: 8px;
        }
        .step-tab {
            flex: 1;
            text-align: center;
            padding: 6px 4px;
            font-size: 11px;
            font-weight: 600;
            color: #64748B;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            border: none;
            background: none;
        }
        .step-tab.active {
            background: #FFFFFF;
            color: #0F172A;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        .controls-group {
            display: flex;
            gap: 6px;
        }
        .btn {
            flex: 1;
            background: #F1F5F9;
            border: 1px solid #CBD5E1;
            color: #334155;
            padding: 7px 10px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn:hover {
            background: #E2E8F0;
        }
        .btn.active {
            background: #0284C7;
            border-color: #0284C7;
            color: #FFFFFF;
        }
        #node-details {
            position: absolute;
            bottom: 20px;
            right: 20px;
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
            font-size: 17px;
            color: #0F172A;
            margin-bottom: 2px;
        }
        #node-details .role-badge {
            display: inline-block;
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 4px;
            margin-bottom: 12px;
            color: #FFFFFF;
        }
        #node-details .meta-row {
            font-size: 12px;
            color: #475569;
            margin-bottom: 8px;
            line-height: 1.45;
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

        /* SVG Causal & Hull styling */
        .cluster-hull {
            fill-opacity: 0.08;
            stroke-width: 1.8px;
            stroke-dasharray: 6, 4;
            transition: fill-opacity 0.3s ease, stroke-width 0.3s ease;
            cursor: pointer;
        }
        .cluster-hull:hover {
            fill-opacity: 0.14;
            stroke-width: 2.5px;
        }
        .cluster-badge-group {
            cursor: pointer;
            transition: transform 0.2s ease, opacity 0.2s ease;
        }
        .cluster-badge-group:hover {
            transform: scale(1.05);
        }
        .cluster-badge-bg {
            fill: rgba(255, 255, 255, 0.94);
            stroke: #E2E8F0;
            stroke-width: 1px;
            rx: 11px;
            ry: 11px;
            transition: stroke 0.2s ease;
        }
        .cluster-badge-group:hover .cluster-badge-bg {
            stroke: #CBD5E1;
        }
        .cluster-badge-title {
            font-size: 11px;
            font-weight: 600;
            fill: #0F172A;
            text-anchor: middle;
            dominant-baseline: central;
        }
        .intra-link {
            stroke-width: 1.2px;
            stroke-dasharray: 2, 3;
            stroke-opacity: 0.35;
        }

        /* Directed Causal Vectors (NO EDGE LABELS) */
        .causal-vector-path {
            fill: none;
            stroke-width: 4.5px;
            stroke-linecap: round;
            cursor: pointer;
            filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.12));
            transition: stroke-width 0.2s ease;
        }
        .causal-vector-path:hover {
            stroke-width: 6.5px;
        }
        .causal-flow-pulse {
            fill: none;
            stroke: #FFFFFF;
            stroke-width: 2.2px;
            stroke-linecap: round;
            stroke-dasharray: 12, 18;
            animation: flowDash 2.4s linear infinite;
            pointer-events: none;
        }
        @keyframes flowDash {
            to { stroke-dashoffset: -120; }
        }

        /* Node styling */
        .node-circle {
            cursor: pointer;
            transition: r 0.2s ease, filter 0.2s ease;
        }
        .node-circle:hover {
            filter: drop-shadow(0 0 10px rgba(0, 0, 0, 0.2));
        }
        .node-label-pill {
            pointer-events: none;
        }
        .label-bg {
            fill: rgba(255, 255, 255, 0.96);
            filter: drop-shadow(0 2px 5px rgba(0, 0, 0, 0.08));
            rx: 6px;
            ry: 6px;
        }
        .label-text-en {
            fill: #0F172A;
            font-size: 11px;
            font-weight: 600;
            text-anchor: middle;
            dominant-baseline: central;
        }
    </style>
</head>
<body>
    <svg id="svg-canvas"></svg>

    <div class="hud-panel">
        <div class="hud-title">
            <span>Causal Knowledge Graph</span>
            <span class="badge" id="hud-badge">Step 3 • Causal Graph</span>
        </div>
        <div class="hud-desc" id="hud-desc">
            Directed causal flow vectors (A, B ➔ C ➔ D) linking clusters over stationary node positions.
        </div>

        <div class="callout-box">
            <strong>Key Visual Principle:</strong> Node coordinates are 100% stationary across all steps. Directed causal arrows show influence without text clutter.
        </div>

        <!-- 3-Step Mode Toggle -->
        <div class="step-toggle-group">
            <button class="step-tab" id="tab-step1" onclick="setStepMode(1)">1. Dispersed</button>
            <button class="step-tab" id="tab-step2" onclick="setStepMode(2)">2. Clusters</button>
            <button class="step-tab active" id="tab-step3" onclick="setStepMode(3)">3. Causal Graph</button>
        </div>

        <div class="causal-blueprint">
            <div style="font-weight: 700; margin-bottom: 6px; color: #0F172A;">Causal Blueprint:</div>
            <div class="blueprint-row">
                <span style="color: #0284C7; font-weight:600;">Heavy Rain</span>
                <span>──➔</span>
                <span style="color: #EA580C; font-weight:600;">Traffic Gridlock</span>
            </div>
            <div class="blueprint-row">
                <span style="color: #0D9488; font-weight:600;">High Winds</span>
                <span>──➔</span>
                <span style="color: #EA580C; font-weight:600;">Traffic Gridlock</span>
            </div>
            <div class="blueprint-row">
                <span style="color: #EA580C; font-weight:600;">Traffic Gridlock</span>
                <span>──➔</span>
                <span style="color: #7C3AED; font-weight:600;">Daily Delays</span>
            </div>
        </div>

        <div class="cluster-pill-list">
            <div class="cluster-pill-item" onclick="focusCluster('A')">
                <div class="cluster-color-circle" style="background: #0284C7;"></div>
                <span>Heavy Rain</span>
            </div>
            <div class="cluster-pill-item" onclick="focusCluster('B')">
                <div class="cluster-color-circle" style="background: #0D9488;"></div>
                <span>High Winds</span>
            </div>
            <div class="cluster-pill-item" onclick="focusCluster('C')">
                <div class="cluster-color-circle" style="background: #EA580C;"></div>
                <span>Traffic Gridlock</span>
            </div>
            <div class="cluster-pill-item" onclick="focusCluster('D')">
                <div class="cluster-color-circle" style="background: #7C3AED;"></div>
                <span>Daily Delays</span>
            </div>
        </div>

        <div class="controls-group">
            <button class="btn active" id="btn-toggle-vectors" onclick="toggleVectors()">Causal Vectors</button>
            <button class="btn active" id="btn-toggle-hulls" onclick="toggleHulls()">Boundaries</button>
            <button class="btn" onclick="resetZoom()">Reset View</button>
        </div>
    </div>

    <!-- Node / Edge Inspector -->
    <div id="node-details">
        <button class="close-btn" onclick="closeDetails()">&times;</button>
        <h3 id="det-word">Term Name</h3>
        <span class="role-badge" id="det-role-badge">Topic Cluster</span>
        <div class="meta-row"><strong>Topic Cluster:</strong> <span id="det-cluster">Cluster</span></div>
        <div class="meta-row"><strong>Causal Role:</strong> <span id="det-role">Role</span></div>
        <div class="meta-row" id="det-context-row"><strong>Description:</strong> <span id="det-context">Context</span></div>
        <div class="meta-row" id="det-coords-row"><strong>Coordinates:</strong> <span id="det-coords">(x, y, z)</span></div>
    </div>

    <script>
        const graphData = __GRAPH_JSON__;
        let currentStep = 3;
        let showHulls = true;
        let showVectors = true;
        let selectedNodeId = null;

        const width = window.innerWidth;
        const height = window.innerHeight;

        const svg = d3.select("#svg-canvas")
            .attr("width", width)
            .attr("height", height);

        // Arrow marker definitions per topic color (NO TEXT LABELS, just markers)
        const defs = svg.append("defs");
        Object.entries(graphData.topics).forEach(([id, t]) => {
            defs.append("marker")
                .attr("id", `arrow-${id}`)
                .attr("viewBox", "0 -5 10 10")
                .attr("refX", 7)
                .attr("refY", 0)
                .attr("markerWidth", 8)
                .attr("markerHeight", 8)
                .attr("orient", "auto")
                .append("path")
                .attr("d", "M 0,-4.5 L 9,0 L 0,4.5 Z")
                .attr("fill", t.color);
        });

        // Background dot grid
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

        // Layers for clean rendering order
        const hullLayer = container.append("g").attr("id", "hull-layer");
        const linkLayer = container.append("g").attr("id", "link-layer");
        const vectorLayer = container.append("g").attr("id", "vector-layer");
        const nodeLayer = container.append("g").attr("id", "node-layer");
        const badgeLayer = container.append("g").attr("id", "badge-layer");

        const scaleFactor = 4.8;
        const nodes = graphData.nodes.map(n => ({
            ...n,
            x: width / 2 + n.x * scaleFactor,
            y: height / 2 - n.y * scaleFactor,
            origX: width / 2 + n.x * scaleFactor,
            origY: height / 2 - n.y * scaleFactor
        }));

        // Group nodes by cluster
        const clusters = {};
        Object.entries(graphData.topics).forEach(([id, t]) => {
            const cNodes = nodes.filter(n => n.topic_id === id);
            const cx = width / 2 + t.centroid_2d.x * scaleFactor;
            const cy = height / 2 - t.centroid_2d.y * scaleFactor;
            clusters[id] = { meta: t, id: id, nodes: cNodes, cx: cx, cy: cy };
        });

        // Zoom Behavior
        const zoom = d3.zoom()
            .scaleExtent([0.35, 3.5])
            .on("zoom", (event) => {
                container.attr("transform", event.transform);
            });
        svg.call(zoom);

        // 1. Draw Intra-cluster subtle connection lines
        graphData.intra_cluster_links.forEach(l => {
            const src = nodes.find(n => n.id === l.source);
            const tgt = nodes.find(n => n.id === l.target);
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
            if (!showHulls || currentStep === 1) return;

            Object.values(clusters).forEach(cl => {
                const points = cl.nodes.map(n => [n.x, n.y]);
                const hull = d3.polygonHull(points);
                if (hull) {
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

        // 3. Draw Minimal Cluster Topic Labels
        Object.values(clusters).forEach(cl => {
            const badge = badgeLayer.append("g")
                .attr("class", "cluster-badge-group")
                .attr("transform", `translate(${cl.cx}, ${cl.cy - 72})`)
                .on("click", (event) => {
                    event.stopPropagation();
                    focusCluster(cl.id);
                });

            const topicText = cl.meta.name;
            const labelWidth = topicText.length * 7 + 28;

            badge.append("rect")
                .attr("class", "cluster-badge-bg")
                .attr("x", -labelWidth / 2)
                .attr("y", -11)
                .attr("width", labelWidth)
                .attr("height", 22);

            badge.append("circle")
                .attr("cx", -labelWidth / 2 + 10)
                .attr("cy", 0)
                .attr("r", 3)
                .attr("fill", cl.meta.color);

            badge.append("text")
                .attr("class", "cluster-badge-title")
                .attr("x", 5)
                .attr("y", 0)
                .text(topicText);
        });

        // 4. Draw Directed Causal Flow Vectors (A -> C, B -> C, C -> D)
        // STRICT REQUIREMENT: NO LABELS ON EDGES.
        function renderCausalVectors() {
            vectorLayer.selectAll("*").remove();
            if (!showVectors || currentStep !== 3) return;

            graphData.causal_edges.forEach(edge => {
                const sCl = clusters[edge.source];
                const tCl = clusters[edge.target];
                if (!sCl || !tCl) return;

                const dx = tCl.cx - sCl.cx;
                const dy = tCl.cy - sCl.cy;
                const dist = Math.hypot(dx, dy) || 1;
                const offsetStart = 85;
                const offsetEnd = 95;

                const sx = sCl.cx + (dx / dist) * offsetStart;
                const sy = sCl.cy + (dy / dist) * offsetStart;
                const tx = tCl.cx - (dx / dist) * offsetEnd;
                const ty = tCl.cy - (dy / dist) * offsetEnd;

                const midX = (sx + tx) / 2;
                const midY = (sy + ty) / 2 + (edge.source === "A" ? -28 : (edge.source === "B" ? 28 : -18));

                const pathData = `M ${sx} ${sy} Q ${midX} ${midY} ${tx} ${ty}`;

                // Background glow
                vectorLayer.append("path")
                    .attr("d", pathData)
                    .attr("stroke", edge.color)
                    .attr("stroke-width", 9)
                    .attr("stroke-opacity", 0.16)
                    .attr("fill", "none");

                // Main causal vector path with arrowhead marker
                vectorLayer.append("path")
                    .attr("class", "causal-vector-path")
                    .attr("d", pathData)
                    .attr("stroke", edge.color)
                    .attr("marker-end", `url(#arrow-${edge.target})`)
                    .on("click", (event) => {
                        event.stopPropagation();
                        showCausalDetails(edge);
                    });

                // Animated flow pulse
                vectorLayer.append("path")
                    .attr("class", "causal-flow-pulse")
                    .attr("d", pathData);
            });
        }
        renderCausalVectors();

        // 5. Render Vocabulary Nodes
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

        // Core Node Circle
        nodeGroups.append("circle")
            .attr("class", "node-circle")
            .attr("r", 12)
            .attr("fill", d => d.color)
            .attr("stroke", "#FFFFFF")
            .attr("stroke-width", 2.5);

        // Label Pill
        const labelGroups = nodeGroups.append("g")
            .attr("class", "node-label-pill")
            .attr("transform", "translate(0, 24)");

        labelGroups.append("rect")
            .attr("class", "label-bg")
            .attr("x", -70)
            .attr("y", -11)
            .attr("width", 140)
            .attr("height", 24)
            .attr("stroke", d => d.color)
            .attr("stroke-width", 1);

        labelGroups.append("text")
            .attr("class", "label-text-en")
            .attr("y", 1)
            .text(d => d.word);

        // Details Panel Functions
        function selectNode(d) {
            selectedNodeId = d.id;
            const det = document.getElementById("node-details");
            det.style.display = "block";
            document.getElementById("det-word").innerText = d.word;
            const badge = document.getElementById("det-role-badge");
            badge.innerText = currentStep === 1 ? "Dispersed Word" : d.cluster_label;
            badge.style.background = currentStep === 1 ? "#475569" : d.color;
            document.getElementById("det-cluster").innerText = currentStep === 1 ? "Latent: " + d.topic_name : d.topic_name;
            document.getElementById("det-role").innerText = currentStep === 1 ? "Initial baseline" : d.causal_role;
            document.getElementById("det-context").innerText = d.context;
            document.getElementById("det-coords").innerText = `(${d.origX.toFixed(1)}, ${d.origY.toFixed(1)})`;
            document.getElementById("det-context-row").style.display = "block";
            document.getElementById("det-coords-row").style.display = "block";
        }

        function showCausalDetails(edge) {
            const det = document.getElementById("node-details");
            det.style.display = "block";
            document.getElementById("det-word").innerText = `Causal Influence: ${edge.source_name} ➔ ${edge.target_name}`;
            const badge = document.getElementById("det-role-badge");
            badge.innerText = `Causal [${edge.causal_type}]`;
            badge.style.background = edge.color;
            document.getElementById("det-cluster").innerText = `${edge.source_name} (Topic ${edge.source}) ➔ ${edge.target_name} (Topic ${edge.target})`;
            document.getElementById("det-role").innerText = `Directed Influence (${edge.relationship})`;
            document.getElementById("det-context").innerText = edge.mechanism;
            document.getElementById("det-coords-row").style.display = "none";
        }

        function closeDetails() {
            document.getElementById("node-details").style.display = "none";
        }

        function focusCluster(topicId) {
            const cl = clusters[topicId];
            if (!cl) return;
            svg.transition().duration(800).call(
                zoom.transform,
                d3.zoomIdentity.translate(width / 2 - cl.cx, height / 2 - cl.cy).scale(1.25)
            );
        }

        function toggleHulls() {
            showHulls = !showHulls;
            document.getElementById("btn-toggle-hulls").classList.toggle("active", showHulls);
            updateHulls();
        }

        function toggleVectors() {
            showVectors = !showVectors;
            document.getElementById("btn-toggle-vectors").classList.toggle("active", showVectors);
            renderCausalVectors();
        }

        function resetZoom() {
            svg.transition().duration(800).call(
                zoom.transform,
                d3.zoomIdentity.translate(0, 0).scale(1)
            );
            closeDetails();
        }

        // 3-Step Interactive Mode Switcher
        function setStepMode(step) {
            currentStep = step;
            document.querySelectorAll(".step-tab").forEach(t => t.classList.remove("active"));
            document.getElementById(`tab-step${step}`).classList.add("active");

            const badge = document.getElementById("hud-badge");
            const desc = document.getElementById("hud-desc");

            if (step === 1) {
                badge.textContent = "Step 1 • Dispersed Words";
                badge.style.background = "#475569";
                desc.textContent = "16 everyday words positioned across 2D space (unclustered baseline).";

                badgeLayer.style("display", "none");
                linkLayer.style("display", "none");
                vectorLayer.style("display", "none");
                hullLayer.style("display", "none");

                nodeGroups.select(".node-circle")
                    .transition().duration(400)
                    .attr("fill", "#475569");
                nodeGroups.select(".label-bg")
                    .transition().duration(400)
                    .attr("stroke", "#CBD5E1");
            } else if (step === 2) {
                badge.textContent = "Step 2 • Thematic Clusters";
                badge.style.background = "#D97706";
                desc.textContent = "16 nodes grouped into 4 distinct thematic topics with boundaries and header labels.";

                badgeLayer.style("display", "block");
                linkLayer.style("display", "block");
                vectorLayer.style("display", "none");
                hullLayer.style("display", "block");
                updateHulls();

                nodeGroups.select(".node-circle")
                    .transition().duration(400)
                    .attr("fill", d => d.color);
                nodeGroups.select(".label-bg")
                    .transition().duration(400)
                    .attr("stroke", d => d.color);
            } else if (step === 3) {
                badge.textContent = "Step 3 • Causal Graph";
                badge.style.background = "#0284C7";
                desc.textContent = "Directed causal flow vectors (A, B ➔ C ➔ D) linking clusters without edge text labels.";

                badgeLayer.style("display", "block");
                linkLayer.style("display", "block");
                vectorLayer.style("display", "block");
                hullLayer.style("display", "block");
                updateHulls();
                renderCausalVectors();

                nodeGroups.select(".node-circle")
                    .transition().duration(400)
                    .attr("fill", d => d.color);
                nodeGroups.select(".label-bg")
                    .transition().duration(400)
                    .attr("stroke", d => d.color);
            }
        }

        svg.on("click", () => {
            closeDetails();
        });
    </script>
</body>
</html>
"""
    return template.replace("__GRAPH_JSON__", graph_json)


def generate_step3_plotly_3d_html() -> str:
    """Generate Plotly 3D scatter graph with visible topic clusters and 3D directed causal vectors (NO edge labels)."""
    import plotly.graph_objects as go

    nodes = get_step3_nodes()
    causal_edges = get_causal_edges()
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
                line=dict(color=t["color"], width=2.0, dash="dash"),
                hoverinfo="none",
                showlegend=False,
                opacity=0.35,
            )
        )

    # 2. Directed Causal Lines in 3D (A -> C, B -> C, C -> D) - NO EDGE LABELS
    for edge in causal_edges:
        s = TOPICS[edge["source"]]["centroid_3d"]
        t = TOPICS[edge["target"]]["centroid_3d"]
        fig.add_trace(
            go.Scatter3d(
                x=[s["x"], t["x"]],
                y=[s["y"], t["y"]],
                z=[s["z"], t["z"]],
                mode="lines",
                line=dict(color=edge["color"], width=7),
                hoverinfo="text",
                hovertext=f"<b>Causal Influence:</b> {edge['source_name']} ➔ {edge['target_name']}<br><b>Mechanism:</b> {edge['mechanism']}",
                name=f"Causal: {edge['source_name']} ➔ {edge['target_name']}",
            )
        )
        # Arrowhead indicator at target
        fig.add_trace(
            go.Scatter3d(
                x=[t["x"]],
                y=[t["y"]],
                z=[t["z"]],
                mode="markers",
                marker=dict(symbol="diamond", size=8, color=edge["color"]),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    # 3. Traces per topic (Vocabulary nodes)
    for topic_id, t in TOPICS.items():
        t_nodes = [n for n in nodes if n["topic_id"] == topic_id]
        xs = [n["x"] for n in t_nodes]
        ys = [n["y"] for n in t_nodes]
        zs = [n["z"] for n in t_nodes]
        labels = [f"<b>{n['word']}</b>" for n in t_nodes]
        hover_texts = [
            f"<b>{n['word']}</b><br>"
            f"<b>Topic:</b> {t['name']}<br>"
            f"<b>Causal Role:</b> {t['causal_role']}<br>"
            f"<b>Context:</b> {n['context']}<br>"
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
                textfont=dict(size=10.5, color="#0F172A"),
                hoverinfo="text",
                hovertext=hover_texts,
                marker=dict(
                    size=9,
                    color=t["color"],
                    opacity=0.95,
                    line=dict(color="#FFFFFF", width=2),
                    symbol="circle",
                ),
            )
        )

    # 4. Centroid annotations
    for topic_id, t in TOPICS.items():
        c = t["centroid_3d"]
        fig.add_trace(
            go.Scatter3d(
                x=[c["x"]],
                y=[c["y"]],
                z=[c["z"] + 18],
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
                "<b>Weather & Commuting Disruption: Causal Knowledge Graph (3D)</b><br>"
                "<sup>Step 3: Directed Causal Induction (A, B ➔ C ➔ D Influence Backbone)</sup>"
            ),
            font=dict(size=18, color="#0F172A"),
            x=0.5,
            xanchor="center",
            y=0.95,
        ),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        legend=dict(
            title=dict(text="<b>Graph Components</b>", font=dict(color="#0F172A")),
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
                eye=dict(x=1.65, y=1.4, z=1.55),
            ),
        ),
        margin=dict(l=60, r=60, b=60, t=90),
    )

    return fig.to_html(include_plotlyjs="cdn", full_html=True)


def generate_step3_threejs_viewer_html() -> str:
    """Generate rich 3D WebGL viewer with 3D directed Bezier tubes, cone arrowheads, and 3-step transition (NO edge labels)."""
    graph_json = json.dumps(generate_step3_json_export())

    template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D Causal Graph - Step 3: Directed Causal Induction</title>
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
            max-width: 440px;
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
            color: #64748B;
            line-height: 1.5;
            margin-bottom: 12px;
        }
        .callout-box {
            font-size: 11px;
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            padding: 7px 10px;
            margin-bottom: 12px;
            color: #475569;
            line-height: 1.4;
        }
        .causal-blueprint {
            background: #F8FAFC;
            border-radius: 8px;
            padding: 10px 12px;
            margin-bottom: 14px;
            border-left: 3px solid #0284C7;
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
        .step-toggle-group {
            display: flex;
            gap: 4px;
            margin-bottom: 12px;
            background: #F1F5F9;
            padding: 3px;
            border-radius: 8px;
        }
        .step-tab {
            flex: 1;
            text-align: center;
            padding: 6px 4px;
            font-size: 11px;
            font-weight: 600;
            color: #64748B;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            border: none;
            background: none;
        }
        .step-tab.active {
            background: #FFFFFF;
            color: #0F172A;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        .controls-group {
            display: flex;
            gap: 6px;
        }
        .btn {
            flex: 1;
            background: #F1F5F9;
            border: 1px solid #CBD5E1;
            color: #334155;
            padding: 7px 10px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn:hover {
            background: #E2E8F0;
        }
        .btn.active {
            background: #0284C7;
            border-color: #0284C7;
            color: #FFFFFF;
        }
        #node-details {
            position: absolute;
            bottom: 20px;
            right: 20px;
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
            font-size: 17px;
            color: #0F172A;
            margin-bottom: 2px;
        }
        #node-details .role-badge {
            display: inline-block;
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 4px;
            margin-bottom: 12px;
            color: #FFFFFF;
        }
        #node-details .meta-row {
            font-size: 12px;
            color: #475569;
            margin-bottom: 8px;
            line-height: 1.45;
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
    </style>
</head>
<body>
    <div id="3d-graph"></div>

    <div class="hud-panel">
        <div class="hud-title">
            <span>Causal Knowledge Graph</span>
            <span class="badge" id="hud-badge-3d">Step 3 • 3D Causal Graph</span>
        </div>
        <div class="hud-desc" id="hud-desc-3d">
            3D directed causal vectors (A, B ➔ C ➔ D) linking clusters without edge text labels.
        </div>

        <div class="callout-box">
            <strong>Key Visual Principle:</strong> The 16 node 3D coordinates are 100% stationary. Clean 3D tubes and cones show causal direction.
        </div>

        <!-- 3-Step Mode Toggle -->
        <div class="step-toggle-group">
            <button class="step-tab" id="tab-3d-step1" onclick="setStepMode3D(1)">1. Dispersed</button>
            <button class="step-tab" id="tab-3d-step2" onclick="setStepMode3D(2)">2. Clusters</button>
            <button class="step-tab active" id="tab-3d-step3" onclick="setStepMode3D(3)">3. Causal Graph</button>
        </div>

        <div class="causal-blueprint">
            <div style="font-weight: 700; margin-bottom: 6px; color: #0F172A;">Causal DAG Architecture:</div>
            <div class="blueprint-row">
                <span style="color: #0284C7; font-weight:700;">Topic A (Heavy Rain)</span>
                <span>──➔</span>
                <span style="color: #EA580C; font-weight:700;">Topic C (Traffic)</span>
            </div>
            <div class="blueprint-row">
                <span style="color: #0D9488; font-weight:700;">Topic B (High Winds)</span>
                <span>──➔</span>
                <span style="color: #EA580C; font-weight:700;">Topic C (Traffic)</span>
            </div>
            <div class="blueprint-row">
                <span style="color: #EA580C; font-weight:700;">Topic C (Traffic)</span>
                <span>──➔</span>
                <span style="color: #7C3AED; font-weight:700;">Topic D (Delays)</span>
            </div>
        </div>

        <div class="cluster-pill-list">
            <div class="cluster-pill-item" onclick="focusCluster3D('A')">
                <div class="cluster-color-circle" style="background: #0284C7;"></div>
                <span>A: Heavy Rain</span>
            </div>
            <div class="cluster-pill-item" onclick="focusCluster3D('B')">
                <div class="cluster-color-circle" style="background: #0D9488;"></div>
                <span>B: High Winds</span>
            </div>
            <div class="cluster-pill-item" onclick="focusCluster3D('C')">
                <div class="cluster-color-circle" style="background: #EA580C;"></div>
                <span>C: Traffic Gridlock</span>
            </div>
            <div class="cluster-pill-item" onclick="focusCluster3D('D')">
                <div class="cluster-color-circle" style="background: #7C3AED;"></div>
                <span>D: Daily Delays</span>
            </div>
        </div>

        <div class="controls-group">
            <button class="btn active" id="btn-toggle-vectors" onclick="toggleVectors3D()">Causal Tubes</button>
            <button class="btn active" id="btn-toggle-labels" onclick="toggleLabels3D()">Labels</button>
            <button class="btn" onclick="resetCamera()">Reset View</button>
        </div>
    </div>

    <!-- Details Panel -->
    <div id="node-details">
        <button class="close-btn" onclick="document.getElementById('node-details').style.display='none'">&times;</button>
        <h3 id="det-word">Term Name</h3>
        <span class="role-badge" id="det-role-badge">Topic Cluster</span>
        <div class="meta-row"><strong>Topic Cluster:</strong> <span id="det-cluster">Cluster</span></div>
        <div class="meta-row"><strong>Causal Role:</strong> <span id="det-role">Role</span></div>
        <div class="meta-row" id="det-context-row"><strong>Description:</strong> <span id="det-context">Context</span></div>
        <div class="meta-row" id="det-coords-row"><strong>Coordinates:</strong> <span id="det-coords">(x, y, z)</span></div>
    </div>

    <script>
        const graphData = __GRAPH_JSON__;
        let showLabels = true;
        let showVectors3D = true;
        let currentStep3D = 3;

        const nodeSpheres = [];
        const boundaryMeshes = [];
        const causalMeshes = [];
        const clusterBillboards = [];

        // Prepare nodes and links for 3D force graph
        const gData = {
            nodes: graphData.nodes.map(n => ({
                id: n.id,
                name: n.word,
                topic_id: n.topic_id,
                cluster_label: n.cluster_label,
                causal_role: n.causal_role,
                context: n.context,
                fx: n.x,
                fy: n.y,
                fz: n.z,
                color: n.color
            })),
            links: graphData.intra_cluster_links.map(l => ({
                source: l.source,
                target: l.target,
                color: l.color
            }))
        };

        // Add Centroid Cluster Header Billboard Sprites in 3D
        Object.entries(graphData.topics).forEach(([id, t]) => {
            const centroidNode = {
                id: `centroid_${id}`,
                isClusterBadge: true,
                topic_id: id,
                name: t.short_label,
                causal_role: t.causal_role,
                color: t.color,
                fx: t.centroid_3d.x,
                fy: t.centroid_3d.y + 20,
                fz: t.centroid_3d.z
            };
            gData.nodes.push(centroidNode);
        });

        const Graph = ForceGraph3D()
            (document.getElementById('3d-graph'))
            .backgroundColor('#FFFFFF')
            .showNavInfo(false)
            .graphData(gData)
            .nodeRelSize(5)
            .nodeOpacity(0.95)
            .linkOpacity(0.35)
            .linkColor(link => link.color || '#CBD5E1')
            .linkWidth(1.2)
            .nodeThreeObject(node => {
                const group = new THREE.Group();

                if (node.isClusterBadge) {
                    const sprite = new SpriteText(node.name);
                    sprite.color = node.color;
                    sprite.textHeight = 4.8;
                    sprite.fontWeight = 'bold';
                    sprite.backgroundColor = 'rgba(255, 255, 255, 0.96)';
                    sprite.borderColor = node.color;
                    sprite.borderWidth = 1.2;
                    sprite.padding = 3.5;
                    sprite.borderRadius = 4;
                    group.add(sprite);
                    clusterBillboards.push(sprite);
                    return group;
                }

                // Core Sphere
                const geom = new THREE.SphereGeometry(3.6, 24, 24);
                const mat = new THREE.MeshLambertMaterial({
                    color: node.color,
                    transparent: true,
                    opacity: 0.95
                });
                const sphere = new THREE.Mesh(geom, mat);
                group.add(sphere);

                // Text Billboard Sprite
                const labelSprite = new SpriteText(node.name);
                labelSprite.color = '#0F172A';
                labelSprite.textHeight = 3.2;
                labelSprite.fontWeight = '600';
                labelSprite.backgroundColor = 'rgba(255, 255, 255, 0.95)';
                labelSprite.borderColor = node.color;
                labelSprite.borderWidth = 1.0;
                labelSprite.padding = 2.5;
                labelSprite.borderRadius = 3;
                labelSprite.position.y = 8;
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
                const badge = document.getElementById("det-role-badge");
                badge.innerText = currentStep3D === 1 ? "Dispersed Word" : node.cluster_label;
                badge.style.background = currentStep3D === 1 ? "#475569" : node.color;
                document.getElementById('det-cluster').innerText = node.cluster_label;
                document.getElementById('det-role').innerText = node.causal_role;
                document.getElementById('det-context').innerText = node.context;
                document.getElementById('det-coords').innerText = `(${node.fx}, ${node.fy}, ${node.fz})`;
                document.getElementById("det-context-row").style.display = "block";
                document.getElementById("det-coords-row").style.display = "block";
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

        // Add 3D Directed Causal Flow Vectors (A -> C, B -> C, C -> D)
        // STRICT REQUIREMENT: NO LABELS ON EDGES.
        graphData.causal_edges.forEach(edge => {
            const s = graphData.topics[edge.source].centroid_3d;
            const t = graphData.topics[edge.target].centroid_3d;

            const p1 = new THREE.Vector3(s.x, s.y, s.z);
            const p2 = new THREE.Vector3(t.x, t.y, t.z);

            // Curve control point
            const mid = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5);
            mid.z += (edge.source === "A" ? 18 : (edge.source === "B" ? -18 : 10));

            const curve = new THREE.QuadraticBezierCurve3(p1, mid, p2);
            const tubeGeo = new THREE.TubeGeometry(curve, 32, 1.4, 8, false);
            const tubeMat = new THREE.MeshLambertMaterial({
                color: edge.color,
                transparent: true,
                opacity: 0.82
            });
            const tubeMesh = new THREE.Mesh(tubeGeo, tubeMat);
            Graph.scene().add(tubeMesh);
            causalMeshes.push(tubeMesh);

            // Arrowhead Cone at target
            const dir = new THREE.Vector3().subVectors(p2, mid).normalize();
            const coneGeo = new THREE.ConeGeometry(3.5, 9, 16);
            const coneMat = new THREE.MeshLambertMaterial({ color: edge.color });
            const coneMesh = new THREE.Mesh(coneGeo, coneMat);

            const arrowPos = p2.clone().sub(dir.clone().multiplyScalar(16));
            coneMesh.position.copy(arrowPos);
            coneMesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
            Graph.scene().add(coneMesh);
            causalMeshes.push(coneMesh);
        });

        Graph.cameraPosition({ x: 210, y: 170, z: 230 });

        // 3-Step Mode Transition Function in 3D
        function setStepMode3D(step) {
            currentStep3D = step;
            document.querySelectorAll(".step-tab").forEach(t => t.classList.remove("active"));
            document.getElementById(`tab-3d-step${step}`).classList.add("active");

            const badge = document.getElementById("hud-badge-3d");
            const desc = document.getElementById("hud-desc-3d");

            if (step === 1) {
                badge.textContent = "Step 1 • Initial Positions";
                badge.style.background = "#475569";
                desc.textContent = "16 everyday words positioned across 3D space (unclustered baseline).";

                clusterBillboards.forEach(b => b.visible = false);
                boundaryMeshes.forEach(m => m.visible = false);
                causalMeshes.forEach(m => m.visible = false);
                Graph.linkOpacity(0);

                nodeSpheres.forEach(item => {
                    item.sphere.material.color.set("#475569");
                    if (item.labelSprite) item.labelSprite.borderColor = "#CBD5E1";
                });
            } else if (step === 2) {
                badge.textContent = "Step 2 • Thematic Clusters";
                badge.style.background = "#D97706";
                desc.textContent = "16 nodes grouped into 4 distinct thematic topics with 3D boundary wireframes and billboards.";

                clusterBillboards.forEach(b => b.visible = true);
                boundaryMeshes.forEach(m => m.visible = true);
                causalMeshes.forEach(m => m.visible = false);
                Graph.linkOpacity(0.35);

                nodeSpheres.forEach(item => {
                    item.sphere.material.color.set(item.node.color);
                    if (item.labelSprite) item.labelSprite.borderColor = item.node.color;
                });
            } else if (step === 3) {
                badge.textContent = "Step 3 • 3D Causal Graph";
                badge.style.background = "#0284C7";
                desc.textContent = "3D directed causal vectors (A, B ➔ C ➔ D) linking clusters without edge text labels.";

                clusterBillboards.forEach(b => b.visible = true);
                boundaryMeshes.forEach(m => m.visible = true);
                causalMeshes.forEach(m => m.visible = showVectors3D);
                Graph.linkOpacity(0.35);

                nodeSpheres.forEach(item => {
                    item.sphere.material.color.set(item.node.color);
                    if (item.labelSprite) item.labelSprite.borderColor = item.node.color;
                });
            }
        }

        function focusCluster3D(topicId) {
            const t = graphData.topics[topicId];
            if (!t) return;
            const c = t.centroid_3d;
            Graph.cameraPosition(
                { x: c.x * 2.0, y: c.y * 2.0, z: c.z + 120 },
                { x: c.x, y: c.y, z: c.z },
                1800
            );
        }

        function toggleLabels3D() {
            showLabels = !showLabels;
            document.getElementById('btn-toggle-labels').classList.toggle('active', showLabels);
            nodeSpheres.forEach(item => {
                if (item.labelSprite) {
                    item.labelSprite.visible = showLabels;
                }
            });
        }

        function toggleVectors3D() {
            showVectors3D = !showVectors3D;
            document.getElementById('btn-toggle-vectors').classList.toggle('active', showVectors3D);
            if (currentStep3D === 3) {
                causalMeshes.forEach(m => m.visible = showVectors3D);
            }
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


def export_step3_formats(output_dir: Path) -> Dict[str, Path]:
    """
    Generate all Step 3 causal graph representations.
    Files created:
    - create_graph.cypher
    - graph_data.json
    - graph_2d_viewer.html (D3.js with directed causal vectors, animated flow, and 3-step transition)
    - graph_2d_plotly.html
    - graph_3d_viewer.html (Three.js with 3D causal tubes, arrowheads, and 3-step transition)
    - graph_3d_plotly.html
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    results: Dict[str, Path] = {}

    # 1. Cypher script
    cypher_path = output_dir / "create_graph.cypher"
    cypher_path.write_text(generate_step3_cypher_script(), encoding="utf-8")
    results["cypher"] = cypher_path

    # 2. JSON data
    json_path = output_dir / "graph_data.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(generate_step3_json_export(), f, indent=2, ensure_ascii=False)
    results["json"] = json_path

    # 3. 2D D3.js Interactive Viewer
    d3_2d_path = output_dir / "graph_2d_viewer.html"
    d3_2d_path.write_text(generate_step3_d3_2d_viewer_html(), encoding="utf-8")
    results["d3_2d"] = d3_2d_path

    # 4. 2D Plotly
    plotly_2d_path = output_dir / "graph_2d_plotly.html"
    plotly_2d_path.write_text(generate_step3_plotly_2d_html(), encoding="utf-8")
    results["plotly_2d"] = plotly_2d_path

    # 5. 3D Three.js WebGL Viewer
    threejs_3d_path = output_dir / "graph_3d_viewer.html"
    threejs_3d_path.write_text(generate_step3_threejs_viewer_html(), encoding="utf-8")
    results["threejs_3d"] = threejs_3d_path

    # 6. 3D Plotly
    plotly_3d_path = output_dir / "graph_3d_plotly.html"
    plotly_3d_path.write_text(generate_step3_plotly_3d_html(), encoding="utf-8")
    results["plotly_3d"] = plotly_3d_path

    return results


def connect_and_upload_neo4j_step3(
    uri: str = "bolt://localhost:7687",
    user: str = "neo4j",
    password: str = "password",
) -> Dict[str, Any]:
    """
    Connect to a running Neo4j instance and upload the Step 3 Causal Graph:
    - 4 TopicCluster nodes
    - 16 StrikeWord nodes
    - 16 [:BELONGS_TO] relationships
    - 3 [:CAUSES] directed macro causal relationships
    - 7 [:LEADS_TO] micro causal word links
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
                        step: 3
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
            nodes = get_step3_nodes()
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
                        step: 3,
                        status: 'causally_linked'
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

            # Insert Macro Directed Causal Links (without edge labels)
            for edge in CAUSAL_EDGES:
                session.run(
                    """
                    MATCH (src:TopicCluster {topic_id: $src_id}), (tgt:TopicCluster {topic_id: $tgt_id})
                    CREATE (src)-[:CAUSES {
                        id: $id,
                        causal_type: $causal_type,
                        relationship: $relationship,
                        mechanism: $mechanism,
                        weight: $weight,
                        step: 3
                    }]->(tgt)
                    """,
                    src_id=edge["source"],
                    tgt_id=edge["target"],
                    id=edge["id"],
                    causal_type=edge["causal_type"],
                    relationship=edge["relationship"],
                    mechanism=edge["mechanism"],
                    weight=edge["weight"],
                )

            # Insert Micro Causal Links
            for link in WORD_CAUSAL_LINKS:
                session.run(
                    """
                    MATCH (w1:StrikeWord {id: $src}), (w2:StrikeWord {id: $tgt})
                    CREATE (w1)-[:LEADS_TO {mechanism: $mechanism, type: $type}]->(w2)
                    """,
                    src=link["source"],
                    tgt=link["target"],
                    mechanism=link["mechanism"],
                    type=link["type"],
                )

            # Verification
            w_res = session.run("MATCH (w:StrikeWord) RETURN count(w) AS total")
            w_total = w_res.single()["total"]
            c_res = session.run("MATCH (c:TopicCluster) RETURN count(c) AS total")
            c_total = c_res.single()["total"]
            caus_res = session.run("MATCH ()-[r:CAUSES]->() RETURN count(r) AS total")
            caus_total = caus_res.single()["total"]
            micro_res = session.run("MATCH ()-[r:LEADS_TO]->() RETURN count(r) AS total")
            micro_total = micro_res.single()["total"]

        driver.close()
        return {
            "status": "success",
            "message": f"Successfully uploaded Step 3 Causal Graph to Neo4j: {w_total} words, {c_total} clusters, {caus_total} CAUSES edges, {micro_total} LEADS_TO links.",
            "total_words": w_total,
            "total_clusters": c_total,
            "total_causal_edges": caus_total,
            "total_micro_links": micro_total,
            "uri": uri,
        }
    except Exception as e:
        return {
            "status": "failed_connection",
            "message": f"Could not connect to Neo4j at {uri}: {e}",
            "hint": "Ensure Neo4j is running and credentials are valid, or load create_graph.cypher manually.",
        }
