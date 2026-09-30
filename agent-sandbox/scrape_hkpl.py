#!/usr/bin/env python3
"""Convenience runner for HKPL scraper."""
import sys
from pathlib import Path

# Add src to sys.path
src_dir = Path(__file__).parent / "src"
if not src_dir.exists():
    src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from china_causal_kg.ingestion.hkpl_scraper import main

if __name__ == "__main__":
    main()
