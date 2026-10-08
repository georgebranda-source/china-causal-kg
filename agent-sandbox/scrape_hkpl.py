#!/usr/bin/env python3
"""Convenience runner for HKPL scraper."""
import sys
from pathlib import Path

# Add agent-sandbox/src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from china_causal_kg.ingestion.hkpl_scraper import main

if __name__ == "__main__":
    main()