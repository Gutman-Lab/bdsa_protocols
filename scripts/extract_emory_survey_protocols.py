#!/usr/bin/env python3
"""Backward-compatible wrapper — use: python scripts/extract_adrc_survey_protocols.py --institution emory"""
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    script = Path(__file__).resolve().parent / "extract_adrc_survey_protocols.py"
    raise SystemExit(
        subprocess.call(
            [sys.executable, str(script), "--institution", "emory", *sys.argv[1:]],
        )
    )
