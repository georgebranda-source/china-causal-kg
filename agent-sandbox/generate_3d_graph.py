#!/usr/bin/env python3
"""
Convenience CLI runner for generating the 1920s Chinese Strike Causal Knowledge Graph.

Supports:
- Step 1: 16 Initial vocabulary nodes (unclustered baseline)
  Output: agent-sandbox/artifacts/step1_dispersed/
- Step 2: 16 Nodes visibly clustered into 4 Thematic Topics (A, B, C, D) with boundary capsules & labels
  Output: agent-sandbox/artifacts/step2_clustered/
- Step 3: Directed Causal Induction (Macro & Micro Causal Relationships: A, B ➔ C ➔ D)
  Output: agent-sandbox/artifacts/step3_causal/
- Unified Navigation Index:
  Output: agent-sandbox/artifacts/index.html
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Any

# Resolve agent-sandbox/src
src_dir = Path(__file__).resolve().parent / "src"
if not src_dir.exists():
    src_dir = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(src_dir))

from china_causal_kg.graph.data import (
    TOPICS,
    STRIKE_NODES,
    CAUSAL_EDGES,
    get_step1_nodes,
    get_step2_nodes,
    get_step3_nodes,
)
from china_causal_kg.graph.visualizer import export_all_formats, connect_and_upload_neo4j
from china_causal_kg.graph.visualizer_step2 import export_step2_formats, connect_and_upload_neo4j_step2
from china_causal_kg.graph.visualizer_step3 import export_step3_formats, connect_and_upload_neo4j_step3


def generate_index_html(output_dir: Path) -> Path:
    """Generate a clean unified HTML index linking Step 1, Step 2, and Step 3 graph deliverables."""
    index_file = output_dir / "index.html"
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>1920s Chinese Strike Causal Knowledge Graph - Showcase</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            background-color: #FFFFFF;
            color: #0F172A;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            padding: 40px 24px;
        }
        .container {
            max-width: 1180px;
            margin: 0 auto;
        }
        header {
            margin-bottom: 32px;
            border-bottom: 1px solid #E2E8F0;
            padding-bottom: 24px;
        }
        .badge {
            display: inline-block;
            background: #2563EB;
            color: #FFFFFF;
            font-size: 11px;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 999px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            margin-bottom: 12px;
        }
        h1 {
            font-size: 28px;
            font-weight: 800;
            color: #0F172A;
            letter-spacing: -0.5px;
            margin-bottom: 8px;
        }
        p.subtitle {
            font-size: 15px;
            color: #475569;
            max-width: 860px;
        }
        .causal-blueprint-card {
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-left: 4px solid #2563EB;
            border-radius: 10px;
            padding: 20px 24px;
            margin-bottom: 36px;
        }
        .causal-blueprint-card h3 {
            font-size: 13.5px;
            font-weight: 700;
            color: #1E293B;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
        }
        .flow-diagram {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            font-family: "SF Mono", Consolas, monospace;
            font-size: 13px;
        }
        .flow-node {
            padding: 8px 14px;
            border-radius: 8px;
            font-weight: 600;
        }
        .flow-node.a { background: #FFE4E6; color: #E11D48; border: 1px solid #FDA4AF; }
        .flow-node.b { background: #CCFBF1; color: #0D9488; border: 1px solid #5EEAD4; }
        .flow-node.c { background: #DBEAFE; color: #2563EB; border: 1px solid #93C5FD; }
        .flow-node.d { background: #EDE9FE; color: #7C3AED; border: 1px solid #C4B5FD; }
        .flow-arrow { color: #94A3B8; font-weight: bold; }

        .steps-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
            gap: 24px;
            margin-bottom: 40px;
        }
        .step-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .step-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
        }
        .step-header {
            margin-bottom: 14px;
        }
        .step-tag {
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            padding: 2px 8px;
            border-radius: 6px;
            display: inline-block;
            margin-bottom: 8px;
        }
        .step-tag.step1 { background: #E0F2FE; color: #0284C7; }
        .step-tag.step2 { background: #FEF3C7; color: #D97706; }
        .step-tag.step3 { background: #DBEAFE; color: #1D4ED8; }
        .step-card h2 {
            font-size: 19px;
            font-weight: 700;
            color: #0F172A;
            margin-bottom: 6px;
        }
        .step-card p {
            font-size: 13px;
            color: #64748B;
            margin-bottom: 18px;
            line-height: 1.5;
        }
        .view-links {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .view-btn {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 9px 12px;
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            color: #1E293B;
            text-decoration: none;
            font-size: 12.5px;
            font-weight: 600;
            transition: all 0.15s;
        }
        .view-btn:hover {
            background: #F1F5F9;
            border-color: #CBD5E1;
            color: #2563EB;
        }
        .view-btn .btn-badge {
            font-size: 10px;
            background: #E2E8F0;
            color: #475569;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: normal;
        }
        .file-list {
            margin-top: 14px;
            padding-top: 10px;
            border-top: 1px dashed #E2E8F0;
            font-size: 11.5px;
            color: #64748B;
        }
        .file-list a {
            color: #2563EB;
            text-decoration: none;
            margin-right: 10px;
        }
        .file-list a:hover {
            text-decoration: underline;
        }

        .topics-section {
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 24px;
        }
        .topics-section h3 {
            font-size: 16px;
            font-weight: 700;
            color: #0F172A;
            margin-bottom: 16px;
        }
        .topics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
        }
        .topic-pill {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 14px;
        }
        .topic-pill-header {
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 700;
            font-size: 13px;
            margin-bottom: 4px;
        }
        .topic-indicator {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }
        .topic-role {
            font-size: 11px;
            color: #64748B;
            font-weight: 600;
            margin-bottom: 6px;
        }
        .topic-words {
            font-size: 12px;
            color: #334155;
            line-height: 1.4;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <span class="badge">Hong Kong Press Archives (1920-1925)</span>
            <h1>1920s Chinese Strike Causal Knowledge Graph</h1>
            <p class="subtitle">
                Demonstrating causal knowledge graph induction from archival news text (The China Mail, Canton Gazette, HKPL MMIS).
                Progressing across three unified stages: Initial Vocabulary Positions ➔ Topic Clustering ➔ Directed Causal Graph.
            </p>
        </header>

        <section class="causal-blueprint-card">
            <h3>Latent Causal Blueprint (A, B ➔ C ➔ D)</h3>
            <div class="flow-diagram">
                <div class="flow-node a">Topic A: Economic Grievances</div>
                <span class="flow-arrow">↘</span>
                <div class="flow-node c">Topic C: General Strike Action</div>
                <span class="flow-arrow">➔</span>
                <div class="flow-node d">Topic D: Harbor & Colonial Paralysis</div>
            </div>
            <div class="flow-diagram" style="margin-top: 6px;">
                <div class="flow-node b">Topic B: Labor Organizing</div>
                <span class="flow-arrow">↗</span>
            </div>
        </section>

        <div class="steps-grid">
            <!-- Step 1 Card -->
            <div class="step-card">
                <div>
                    <div class="step-header">
                        <span class="step-tag step1">Step 1 • Baseline</span>
                        <h2>Initial Vocabulary Positions</h2>
                    </div>
                    <p>
                        16 archival terms positioned across embedding coordinates establishing the unclustered baseline. All identifying colors and cluster labels are hidden.
                    </p>
                </div>
                <div>
                    <div class="view-links">
                        <a href="step1_dispersed/graph_2d_viewer.html" class="view-btn">
                            <span>Interactive 2D Viewer</span>
                            <span class="btn-badge">D3.js SVG</span>
                        </a>
                        <a href="step1_dispersed/graph_3d_viewer.html" class="view-btn">
                            <span>Interactive 3D Viewer</span>
                            <span class="btn-badge">Three.js WebGL</span>
                        </a>
                        <a href="step1_dispersed/graph_2d_plotly.html" class="view-btn">
                            <span>Plotly 2D Scatter</span>
                            <span class="btn-badge">Plotly.js</span>
                        </a>
                        <a href="step1_dispersed/graph_3d_plotly.html" class="view-btn">
                            <span>Plotly 3D Scatter</span>
                            <span class="btn-badge">Plotly.js</span>
                        </a>
                    </div>
                    <div class="file-list">
                        Data files:
                        <a href="step1_dispersed/create_graph.cypher">Cypher Script</a>
                        <a href="step1_dispersed/graph_data.json">JSON Export</a>
                    </div>
                </div>
            </div>

            <!-- Step 2 Card -->
            <div class="step-card">
                <div>
                    <div class="step-header">
                        <span class="step-tag step2">Step 2 • Thematic Clusters</span>
                        <h2>Clusters Revealed (Zero Movement)</h2>
                    </div>
                    <p>
                        <strong>Zero Node Movement:</strong> Nodes remain at their exact initial coordinates. Clusters are delineated by colored boundary capsules, palettes, and header labels.
                    </p>
                </div>
                <div>
                    <div class="view-links">
                        <a href="step2_clustered/graph_2d_viewer.html" class="view-btn">
                            <span>Interactive 2D Clustered Viewer</span>
                            <span class="btn-badge">D3.js Hulls</span>
                        </a>
                        <a href="step2_clustered/graph_3d_viewer.html" class="view-btn">
                            <span>Interactive 3D Clustered Viewer</span>
                            <span class="btn-badge">Three.js Billboards</span>
                        </a>
                        <a href="step2_clustered/graph_2d_plotly.html" class="view-btn">
                            <span>Plotly 2D Clustered Scatter</span>
                            <span class="btn-badge">Plotly.js</span>
                        </a>
                        <a href="step2_clustered/graph_3d_plotly.html" class="view-btn">
                            <span>Plotly 3D Clustered Scatter</span>
                            <span class="btn-badge">Plotly.js</span>
                        </a>
                    </div>
                    <div class="file-list">
                        Data files:
                        <a href="step2_clustered/create_graph.cypher">Cypher Script</a>
                        <a href="step2_clustered/graph_data.json">JSON Export</a>
                    </div>
                </div>
            </div>

            <!-- Step 3 Card -->
            <div class="step-card" style="border-color: #93C5FD; box-shadow: 0 4px 20px rgba(37, 99, 235, 0.1);">
                <div>
                    <div class="step-header">
                        <span class="step-tag step3">Step 3 • Final Causal KG</span>
                        <h2>Directed Causal Induction</h2>
                    </div>
                    <p>
                        <strong>Complete Causal Knowledge Graph:</strong> Macro directed causal arrows (A, B ➔ C ➔ D), animated flow pulses, mechanism cards, and micro word links over stationary nodes.
                    </p>
                </div>
                <div>
                    <div class="view-links">
                        <a href="step3_causal/graph_2d_viewer.html" class="view-btn" style="border-color: #BFDBFE; background: #EFF6FF;">
                            <span style="color: #1D4ED8; font-weight: 700;">Interactive 2D Causal Viewer</span>
                            <span class="btn-badge" style="background: #DBEAFE; color: #1D4ED8;">D3.js Animated Vectors</span>
                        </a>
                        <a href="step3_causal/graph_3d_viewer.html" class="view-btn" style="border-color: #BFDBFE; background: #EFF6FF;">
                            <span style="color: #1D4ED8; font-weight: 700;">Interactive 3D Causal Viewer</span>
                            <span class="btn-badge" style="background: #DBEAFE; color: #1D4ED8;">Three.js 3D Tubes</span>
                        </a>
                        <a href="step3_causal/graph_2d_plotly.html" class="view-btn">
                            <span>Plotly 2D Causal Graph</span>
                            <span class="btn-badge">Plotly.js</span>
                        </a>
                        <a href="step3_causal/graph_3d_plotly.html" class="view-btn">
                            <span>Plotly 3D Causal Graph</span>
                            <span class="btn-badge">Plotly.js</span>
                        </a>
                    </div>
                    <div class="file-list">
                        Data files:
                        <a href="step3_causal/create_graph.cypher">Cypher Script</a>
                        <a href="step3_causal/graph_data.json">JSON Export</a>
                    </div>
                </div>
            </div>
        </div>

        <section class="topics-section">
            <h3>4 Thematic Topics (16 Press Vocabulary Terms)</h3>
            <div class="topics-grid">
                <div class="topic-pill" style="border-left: 3px solid #E11D48;">
                    <div class="topic-pill-header" style="color: #E11D48;">
                        <span class="topic-indicator" style="background: #E11D48;"></span>
                        Topic A: Economic Grievances
                    </div>
                    <div class="topic-role">Precondition / Cause (A ➔ C)</div>
                    <div class="topic-words">Wage Depression, Rice Inflation, Ten-Hour Shift, Living Cost Spiral</div>
                </div>
                <div class="topic-pill" style="border-left: 3px solid #0D9488;">
                    <div class="topic-pill-header" style="color: #0D9488;">
                        <span class="topic-indicator" style="background: #0D9488;"></span>
                        Topic B: Labor Organizing
                    </div>
                    <div class="topic-role">Catalyst / Cause (B ➔ C)</div>
                    <div class="topic-words">Seamen's Union, Strike Committee, Picket Corps, Boycott Manifesto</div>
                </div>
                <div class="topic-pill" style="border-left: 3px solid #2563EB;">
                    <div class="topic-pill-header" style="color: #2563EB;">
                        <span class="topic-indicator" style="background: #2563EB;"></span>
                        Topic C: General Strike Action
                    </div>
                    <div class="topic-role">Central Event (A, B ➔ C ➔ D)</div>
                    <div class="topic-words">General Strike, Dockworker Walkout, Work Cessation, Mass Demonstration</div>
                </div>
                <div class="topic-pill" style="border-left: 3px solid #7C3AED;">
                    <div class="topic-pill-header" style="color: #7C3AED;">
                        <span class="topic-indicator" style="background: #7C3AED;"></span>
                        Topic D: Harbor Paralysis
                    </div>
                    <div class="topic-role">Consequence (C ➔ D)</div>
                    <div class="topic-words">Port Paralysis, Shipping Deadlock, Market Interruption, Colonial Concessions</div>
                </div>
            </div>
        </section>
    </div>
</body>
</html>
"""
    index_file.write_text(html_content, encoding="utf-8")
    return index_file


def main():
    parser = argparse.ArgumentParser(
        description="Generate 3D & 2D Causal Knowledge Graph for Neo4j and Viewers."
    )
    parser.add_argument(
        "--step",
        choices=["1", "2", "3", "all"],
        default="all",
        help="Which step to generate: '1' (initial), '2' (clustered), '3' (causal), or 'all' (default).",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default=str(Path(__file__).resolve().parent / "artifacts"),
        help="Directory where output files (Cypher, JSON, HTML) will be generated.",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Attempt uploading directly to a running Neo4j instance.",
    )
    parser.add_argument(
        "--neo4j-uri",
        default=os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
        help="Neo4j connection URI (default: bolt://localhost:7687 or $NEO4J_URI).",
    )
    parser.add_argument(
        "--neo4j-user",
        default=os.environ.get("NEO4J_USER", "neo4j"),
        help="Neo4j user (default: neo4j or $NEO4J_USER).",
    )
    parser.add_argument(
        "--neo4j-pass",
        default=os.environ.get("NEO4J_PASSWORD", "password"),
        help="Neo4j password (default: password or $NEO4J_PASSWORD).",
    )

    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out_base = Path(args.output_dir)

    print("=" * 70)
    print("1920s Chinese Strike Causal Knowledge Graph Generator")
    print("=" * 70)
    print(f"[*] Base Output Directory: {out_base.resolve()}")
    print(f"[*] Total Vocabulary Terms: {len(STRIKE_NODES)}")
    print(f"[*] Thematic Topics:        {len(TOPICS)}")
    print(f"[*] Causal Relationships:   {len(CAUSAL_EDGES)}")
    print(f"[*] Selected Step:          {args.step.upper()}")
    print("-" * 70)
    print("Causal Blueprint Architecture:")
    print("  * Topic A (Economic Grievance)  ──➔  Topic C (General Strike)")
    print("  * Topic B (Labor Organizing)    ──➔  Topic C (General Strike)")
    print("  * Topic C (General Strike)      ──➔  Topic D (Harbor Paralysis)")
    print("-" * 70)

    # 1. Step 1 Generation
    if args.step in ["1", "all"]:
        step1_dir = out_base / "step1_dispersed" if out_base.name != "step1_dispersed" else out_base
        print(f"\n[+] Generating Step 1 (Initial Baseline) in: {step1_dir}")
        res1 = export_all_formats(step1_dir)
        for key, path in res1.items():
            print(f"    - [{key.upper():10}] {path.name}")

    # 2. Step 2 Generation
    if args.step in ["2", "all"]:
        step2_dir = out_base / "step2_clustered" if out_base.name != "step2_clustered" else out_base
        print(f"\n[+] Generating Step 2 (Thematic Clusters & Labels) in: {step2_dir}")
        res2 = export_step2_formats(step2_dir)
        for key, path in res2.items():
            print(f"    - [{key.upper():10}] {path.name}")

    # 3. Step 3 Generation
    if args.step in ["3", "all"]:
        step3_dir = out_base / "step3_causal" if out_base.name != "step3_causal" else out_base
        print(f"\n[+] Generating Step 3 (Directed Causal Graph) in: {step3_dir}")
        res3 = export_step3_formats(step3_dir)
        for key, path in res3.items():
            print(f"    - [{key.upper():10}] {path.name}")

    # 4. Unified Navigation Index
    index_path = generate_index_html(out_base)
    print(f"\n[+] Unified Navigation Index: {index_path.resolve()}")

    # Live Neo4j upload attempt if requested
    if args.upload:
        print("\n[*] Connecting to Neo4j database...")
        if args.step == "1":
            upload_res = connect_and_upload_neo4j(
                uri=args.neo4j_uri,
                user=args.neo4j_user,
                password=args.neo4j_pass,
            )
        elif args.step == "2":
            upload_res = connect_and_upload_neo4j_step2(
                uri=args.neo4j_uri,
                user=args.neo4j_user,
                password=args.neo4j_pass,
            )
        else:
            upload_res = connect_and_upload_neo4j_step3(
                uri=args.neo4j_uri,
                user=args.neo4j_user,
                password=args.neo4j_pass,
            )
        if upload_res.get("status") == "success":
            print(f"[OK] {upload_res['message']}")
        else:
            print(f"[!] {upload_res.get('message')}")
            if "hint" in upload_res:
                print(f"    Hint: {upload_res['hint']}")

    print("\n[*] Complete! Open index.html or any of the viewer files to explore.")


if __name__ == "__main__":
    main()
