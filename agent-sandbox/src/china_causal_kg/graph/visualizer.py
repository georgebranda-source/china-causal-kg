"""
Generators for Neo4j Cypher scripts, JSON graph exports, Plotly 3D graphs,
and interactive WebGL 3D visualizations.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from .data import TOPICS, STRIKE_NODES


def generate_cypher_script() -> str:
    """Generate Cypher commands to populate Neo4j with the 16 dispersed word nodes."""
    lines = [
        "// ====================================================================",
        "// 1920s Chinese Labor Strike Causal Knowledge Graph (Step 1)",
        "// Visual Representation: 16 Dispersed Words from 1920s Newspaper Press",
        "// Causal Target Structure: (A: Economic) -> (C: Strike) <- (B: Union)",
        "//                          (C: Strike) -> (D: Paralysis)",
        "// ====================================================================",
        "",
        "// 1. Schema Constraints & Indexes",
        "CREATE CONSTRAINT word_id_unique IF NOT EXISTS",
        "FOR (w:StrikeWord) REQUIRE w.id IS UNIQUE;",
        "",
        "CREATE INDEX word_topic_idx IF NOT EXISTS",
        "FOR (w:StrikeWord) REQUIRE w.topic_id;",
        "",
        "// 2. Clear existing demonstration nodes",
        "MATCH (w:StrikeWord) DETACH DELETE w;",
        "",
        "// 3. Create 16 Dispersed Nodes (Pre-clustered)",
    ]

    for node in STRIKE_NODES:
        causal_role = TOPICS[node["topic_id"]]["causal_role"]
        cypher_node = (
            f"CREATE (:{node['topic_id']}_Group:StrikeWord:Word {{\n"
            f'    id: "{node["id"]}",\n'
            f'    word: "{node["word"]}",\n'
            f'    chinese: "{node["chinese"]}",\n'
            f'    topic_id: "{node["topic_id"]}",\n'
            f'    topic_name: "{node["topic_name"]}",\n'
            f'    causal_role: "{causal_role}",\n'
            f'    historical_source: "{node["historical_source"]}",\n'
            f'    context: "{node["context"]}",\n'
            f'    x: {node["x"]}, y: {node["y"]}, z: {node["z"]},\n'
            f"    step: 1,\n"
            f'    status: "dispersed_unclustered"\n'
            f"}});"
        )
        lines.append(cypher_node)

    lines.extend([
        "",
        "// ====================================================================",
        "// Step 1 Query: Retrieve all 16 dispersed nodes with 3D coordinates",
        "// ====================================================================",
        "MATCH (w:StrikeWord)",
        "RETURN w.id AS id, w.word AS word, w.chinese AS chinese,",
        "       w.topic_id AS topic_id, w.topic_name AS topic_name,",
        "       w.x AS x, w.y AS y, w.z AS z, w.causal_role AS causal_role;",
        "",
    ])
    return "\n".join(lines)


def generate_json_export() -> Dict[str, Any]:
    """Generate structured JSON representation of the graph."""
    return {
        "metadata": {
            "title": "1920s Chinese Strike Causal Knowledge Graph",
            "step": 1,
            "description": "Visual representation of 16 dispersed words from 1920s newspaper press before clustering.",
            "total_nodes": len(STRIKE_NODES),
            "total_edges": 0,
            "causal_blueprint": {
                "chain": ["Topic A -> Topic C", "Topic B -> Topic C", "Topic C -> Topic D"],
                "topics": TOPICS,
            },
        },
        "topics": TOPICS,
        "nodes": STRIKE_NODES,
        "edges": [],
    }


def generate_plotly_3d_html() -> str:
    """Generate a self-contained, interactive Plotly 3D scatter graph HTML."""
    import plotly.graph_objects as go

    fig = go.Figure()

    # Add traces for each topic so they can be toggled via legend
    for topic_id, topic_info in TOPICS.items():
        topic_nodes = [n for n in STRIKE_NODES if n["topic_id"] == topic_id]
        xs = [n["x"] for n in topic_nodes]
        ys = [n["y"] for n in topic_nodes]
        zs = [n["z"] for n in topic_nodes]
        labels = [f"<b>{n['word']}</b><br>({n['chinese']})" for n in topic_nodes]
        hover_texts = [
            f"<b>{n['word']}</b> ({n['chinese']})<br>"
            f"<b>Future Topic:</b> {n['topic_name']}<br>"
            f"<b>Causal Role:</b> {topic_info['causal_role']}<br>"
            f"<b>Source:</b> {n['historical_source']}<br>"
            f"<b>Context:</b> {n['context']}<br>"
            f"<b>Coordinates:</b> ({n['x']}, {n['y']}, {n['z']})"
            for n in topic_nodes
        ]

        fig.add_trace(
            go.Scatter3d(
                x=xs,
                y=ys,
                z=zs,
                mode="markers+text",
                name=f"{topic_info['name']} ({topic_info['causal_role']})",
                text=labels,
                textposition="top center",
                textfont=dict(size=11, color="#F0F4F8"),
                hoverinfo="text",
                hovertext=hover_texts,
                marker=dict(
                    size=9,
                    color=topic_info["color"],
                    opacity=0.9,
                    line=dict(color="#FFFFFF", width=1.5),
                    symbol="circle",
                ),
            )
        )

    fig.update_layout(
        title=dict(
            text=(
                "<b>1920s Chinese Newspaper Labor Strike: Causal Knowledge Graph</b><br>"
                "<sup>Step 1: 16 Dispersed Vocabulary Nodes (Latent Causal Blueprint: A & B → C → D)</sup>"
            ),
            font=dict(size=18, color="#FFFFFF"),
            x=0.5,
            xanchor="center",
            y=0.95,
        ),
        paper_bgcolor="#0E131F",
        plot_bgcolor="#0E131F",
        legend=dict(
            title=dict(text="<b>Latent Topic Clusters (Causal Blueprint)</b>", font=dict(color="#FFFFFF")),
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


def generate_threejs_viewer_html() -> str:
    """Generate a rich, interactive 3D WebGL viewer using Three.js and 3d-force-graph."""
    graph_json = json.dumps(generate_json_export())

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D Causal Graph - 1920s Chinese Strike Press</title>
    <script src="https://unpkg.com/three@0.160.0/build/three.min.js"></script>
    <script src="https://unpkg.com/three-spritetext@1.8.2/dist/three-spritetext.min.js"></script>
    <script src="https://unpkg.com/3d-force-graph@1.73.3/dist/3d-force-graph.min.js"></script>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            background: radial-gradient(circle at center, #111827 0%, #030712 100%);
            color: #F3F4F6;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            overflow: hidden;
            width: 100vw;
            height: 100vh;
        }}
        #3d-graph {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 1;
        }}
        .hud-panel {{
            position: absolute;
            top: 20px;
            left: 20px;
            z-index: 10;
            background: rgba(17, 24, 39, 0.85);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 12px;
            padding: 20px 24px;
            max-width: 420px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
        }}
        .hud-title {{
            font-size: 18px;
            font-weight: 700;
            color: #F9FAFB;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .badge {{
            display: inline-block;
            background: #2563EB;
            color: #EFF6FF;
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 999px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }}
        .hud-desc {{
            font-size: 13px;
            color: #9CA3AF;
            line-height: 1.5;
            margin-bottom: 16px;
        }}
        .causal-blueprint {{
            background: rgba(31, 41, 55, 0.8);
            border-radius: 8px;
            padding: 12px 14px;
            margin-bottom: 16px;
            border-left: 3px solid #3B82F6;
        }}
        .blueprint-title {{
            font-size: 12px;
            text-transform: uppercase;
            font-weight: 700;
            letter-spacing: 0.5px;
            color: #93C5FD;
            margin-bottom: 6px;
        }}
        .blueprint-formula {{
            font-family: "SF Mono", Consolas, monospace;
            font-size: 13px;
            color: #E5E7EB;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        .blueprint-step {{
            color: #10B981;
            font-weight: 600;
        }}
        .topic-legend {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 8px;
            margin-bottom: 16px;
        }}
        .topic-pill {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 12px;
            color: #D1D5DB;
        }}
        .topic-color-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            flex-shrink: 0;
            box-shadow: 0 0 8px currentColor;
        }}
        .controls-group {{
            display: flex;
            gap: 8px;
            margin-top: 12px;
        }}
        .btn {{
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
        }}
        .btn:hover {{
            background: #4B5563;
            border-color: #6B7280;
        }}
        .btn.active {{
            background: #2563EB;
            border-color: #3B82F6;
            color: #FFFFFF;
        }}
        #node-details {{
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
        }}
        #node-details h3 {{
            font-size: 18px;
            color: #F9FAFB;
            margin-bottom: 4px;
        }}
        #node-details .chinese {{
            font-size: 14px;
            color: #9CA3AF;
            margin-bottom: 12px;
        }}
        #node-details .meta-row {{
            font-size: 12px;
            color: #D1D5DB;
            margin-bottom: 6px;
            line-height: 1.4;
        }}
        #node-details .meta-row strong {{
            color: #93C5FD;
        }}
    </style>
</head>
<body>
    <div id="3d-graph"></div>

    <div class="hud-panel">
        <div class="hud-title">
            <span>China Strike Causal KG</span>
            <span class="badge">Step 1</span>
        </div>
        <div class="hud-desc">
            16 disconnected words extracted from 1920s newspaper press (e.g. <i>The China Mail</i>, Hong Kong MMIS).
        </div>

        <div class="causal-blueprint">
            <div class="blueprint-title">Latent Causal Blueprint</div>
            <div class="blueprint-formula">
                <div>(A) Economic Grievances ➔ (C) General Strike</div>
                <div>(B) Union Mobilization ➔ (C) General Strike</div>
                <div>(C) General Strike ➔ (D) Harbor Paralysis</div>
                <div class="blueprint-step">Current Step: 16 Disconnected Words</div>
            </div>
        </div>

        <div class="topic-legend" id="legend-container"></div>

        <div class="controls-group">
            <button class="btn active" id="btn-toggle-colors" onclick="toggleColorMode()">Color by Topic</button>
            <button class="btn" id="btn-toggle-labels" onclick="toggleLabels()">Toggle Labels</button>
            <button class="btn" onclick="resetCamera()">Reset View</button>
        </div>
    </div>

    <div id="node-details">
        <h3 id="det-word">Word</h3>
        <div class="chinese" id="det-chinese">中文</div>
        <div class="meta-row"><strong>Topic Cluster:</strong> <span id="det-topic"></span></div>
        <div class="meta-row"><strong>Causal Role:</strong> <span id="det-role"></span></div>
        <div class="meta-row"><strong>Historical Source:</strong> <span id="det-source"></span></div>
        <div class="meta-row"><strong>Context:</strong> <span id="det-context"></span></div>
        <div class="meta-row"><strong>3D Coordinates:</strong> <span id="det-coords"></span></div>
    </div>

    <script>
        const graphData = {graph_json};
        let colorMode = 'topic'; // 'topic' or 'uniform'
        let showLabels = true;

        // Render legend
        const legendContainer = document.getElementById('legend-container');
        Object.entries(graphData.topics).forEach(([id, t]) => {{
            const row = document.createElement('div');
            row.className = 'topic-pill';
            row.innerHTML = `
                <div class="topic-color-dot" style="background-color: ${{t.color}}; color: ${{t.color}};"></div>
                <span><strong>Topic ${{id}}:</strong> ${{t.name}}</span>
            `;
            legendContainer.appendChild(row);
        }});

        // Format nodes for 3d-force-graph
        const gData = {{
            nodes: graphData.nodes.map(n => ({{
                id: n.id,
                name: n.word,
                chinese: n.chinese,
                topic_id: n.topic_id,
                topic_name: n.topic_name,
                historical_source: n.historical_source,
                context: n.context,
                fx: n.x,
                fy: n.y,
                fz: n.z,
                color: graphData.topics[n.topic_id].color,
                causal_role: graphData.topics[n.topic_id].causal_role
            }})),
            links: []
        }};

        const Graph = ForceGraph3D()(document.getElementById('3d-graph'))
            .graphData(gData)
            .backgroundColor('#030712')
            .showNavInfo(false)
            .nodeRelSize(7)
            .nodeColor(node => colorMode === 'topic' ? node.color : '#60A5FA')
            .nodeThreeObject(node => {{
                const group = new THREE.Group();

                // Glowing Sphere
                const sphereGeometry = new THREE.SphereGeometry(3.5, 24, 24);
                const sphereMaterial = new THREE.MeshLambertMaterial({{
                    color: colorMode === 'topic' ? node.color : '#60A5FA',
                    transparent: true,
                    opacity: 0.9
                }});
                const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
                group.add(sphere);

                // Billboard Sprite Text Label
                if (showLabels) {{
                    const sprite = new SpriteText(`${{node.name}}\\n(${{node.chinese}})`);
                    sprite.color = '#F3F4F6';
                    sprite.textHeight = 3.2;
                    sprite.position.y = 7;
                    sprite.backgroundColor = 'rgba(15, 23, 42, 0.75)';
                    sprite.padding = 2;
                    sprite.borderRadius = 3;
                    group.add(sprite);
                }}

                return group;
            }})
            .onNodeClick(node => {{
                // Aim camera at node
                const distance = 80;
                const distRatio = 1 + distance/Math.hypot(node.fx, node.fy, node.fz);
                Graph.cameraPosition(
                    {{ x: node.fx * distRatio, y: node.fy * distRatio, z: node.fz * distRatio }},
                    {{ x: node.fx, y: node.fy, z: node.fz }},
                    2000
                );

                // Show details card
                document.getElementById('node-details').style.display = 'block';
                document.getElementById('det-word').innerText = node.name;
                document.getElementById('det-chinese').innerText = node.chinese;
                document.getElementById('det-topic').innerText = `${{node.topic_id}}: ${{node.topic_name}}`;
                document.getElementById('det-role').innerText = node.causal_role;
                document.getElementById('det-source').innerText = node.historical_source;
                document.getElementById('det-context').innerText = node.context;
                document.getElementById('det-coords').innerText = `(${{node.fx}}, ${{node.fy}}, ${{node.fz}})`;
            }})
            .onBackgroundClick(() => {{
                document.getElementById('node-details').style.display = 'none';
            }});

        // Adjust camera
        Graph.cameraPosition({{ x: 180, y: 140, z: 200 }});

        function toggleColorMode() {{
            colorMode = colorMode === 'topic' ? 'uniform' : 'topic';
            const btn = document.getElementById('btn-toggle-colors');
            if (colorMode === 'topic') {{
                btn.classList.add('active');
                btn.innerText = 'Color by Topic';
            }} else {{
                btn.classList.remove('active');
                btn.innerText = 'Uniform Color';
            }}
            Graph.nodeColor(Graph.nodeColor());
            Graph.refresh();
        }}

        function toggleLabels() {{
            showLabels = !showLabels;
            const btn = document.getElementById('btn-toggle-labels');
            btn.classList.toggle('active', showLabels);
            Graph.refresh();
        }}

        function resetCamera() {{
            Graph.cameraPosition({{ x: 180, y: 140, z: 200 }}, {{ x: 0, y: 0, z: 0 }}, 1500);
            document.getElementById('node-details').style.display = 'none';
        }}
    </script>
</body>
</html>
"""
    return html_content


def export_all_formats(output_dir: Optional[Path] = None) -> Dict[str, Path]:
    """
    Generate all graph representations and save them to output_dir.
    Files created:
    - create_graph.cypher
    - graph_data.json
    - graph_3d_plotly.html
    - graph_3d_viewer.html
    """
    if output_dir is None:
        # Default to agent-sandbox/artifacts
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
    plotly_path = output_dir / "graph_3d_plotly.html"
    plotly_path.write_text(generate_plotly_3d_html(), encoding="utf-8")
    results["plotly"] = plotly_path

    # 4. WebGL Three.js HTML Viewer
    threejs_path = output_dir / "graph_3d_viewer.html"
    threejs_path.write_text(generate_threejs_viewer_html(), encoding="utf-8")
    results["threejs"] = threejs_path

    return results


def connect_and_upload_neo4j(
    uri: str = "bolt://localhost:7687",
    user: str = "neo4j",
    password: str = "password",
) -> Dict[str, Any]:
    """
    Connect to a running Neo4j instance and upload the 16 nodes.
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

            # Insert nodes in batch
            query = """
            UNWIND $batch AS item
            CREATE (w:StrikeWord:Word {
                id: item.id,
                word: item.word,
                chinese: item.chinese,
                topic_id: item.topic_id,
                topic_name: item.topic_name,
                causal_role: item.causal_role,
                historical_source: item.historical_source,
                context: item.context,
                x: item.x,
                y: item.y,
                z: item.z,
                step: 1,
                status: 'dispersed_unclustered'
            })
            """
            batch = []
            for n in STRIKE_NODES:
                item = dict(n)
                item["causal_role"] = TOPICS[n["topic_id"]]["causal_role"]
                batch.append(item)

            session.run(query, batch=batch)

            # Count created nodes
            result = session.run("MATCH (w:StrikeWord) RETURN count(w) AS total")
            total = result.single()["total"]

        driver.close()
        return {
            "status": "success",
            "message": f"Successfully connected to Neo4j and created {total} nodes.",
            "total_nodes": total,
            "uri": uri,
        }
    except Exception as e:
        return {
            "status": "failed_connection",
            "message": f"Could not connect to Neo4j at {uri}: {e}",
            "hint": "Ensure Neo4j is running and credentials are valid, or load create_graph.cypher manually.",
        }
