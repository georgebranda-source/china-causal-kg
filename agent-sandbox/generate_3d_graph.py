#!/usr/bin/env python3
"""
Convenience CLI runner for generating the 1920s Chinese Strike 3D Causal Knowledge Graph (Step 1).

Outputs:
1. agent-sandbox/artifacts/create_graph.cypher   (Neo4j Cypher ingestion script)
2. agent-sandbox/artifacts/graph_data.json      (Structured graph export)
3. agent-sandbox/artifacts/graph_3d_plotly.html (Standalone interactive 3D HTML)
4. agent-sandbox/artifacts/graph_3d_viewer.html (WebGL / Three.js 3D application)
"""

import os
import sys
import argparse
from pathlib import Path

# Resolve agent-sandbox/src
src_dir = Path(__file__).resolve().parent / "src"
if not src_dir.exists():
    src_dir = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(src_dir))

from china_causal_kg.graph.data import TOPICS, STRIKE_NODES
from china_causal_kg.graph.visualizer import export_all_formats, connect_and_upload_neo4j


def main():
    parser = argparse.ArgumentParser(
        description="Generate 3D Causal Knowledge Graph (Step 1: 16 Dispersed Nodes) for Neo4j and 3D Viewers."
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

    out_path = Path(args.output_dir)

    print("=" * 70)
    print("1920s Chinese Strike 3D Causal Knowledge Graph Generator (Step 1)")
    print("=" * 70)
    print(f"[*] Target Output Directory: {out_path.resolve()}")
    print(f"[*] Total Dispersed Nodes:   {len(STRIKE_NODES)}")
    print(f"[*] Latent Topics:           {len(TOPICS)}")
    print("-" * 70)
    print("Latent Causal Blueprint:")
    print("  * Topic A (Economic Grievance)  -->  Topic C (General Strike)")
    print("  * Topic B (Union Mobilization)  -->  Topic C (General Strike)")
    print("  * Topic C (General Strike)      -->  Topic D (Port & Market Paralysis)")
    print("-" * 70)

    # Export all files
    results = export_all_formats(out_path)
    for key, path in results.items():
        print(f"[OK] Generated ({key.upper():7}): {path.resolve()}")

    # Live Neo4j upload attempt if requested
    if args.upload:
        print("\n[*] Connecting to Neo4j database...")
        upload_res = connect_and_upload_neo4j(
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

    print("\n[*] Generation complete. Open either of the HTML files in a browser to inspect the 3D graph.")


if __name__ == "__main__":
    main()
