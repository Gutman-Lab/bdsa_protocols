#!/usr/bin/env python3
"""
Sync 2K thumbnails from the UK BDSA Girder collection (convenience wrapper).

Requires: pip install girder-client
  export BDSA_API_KEY=your_uky_api_key

Usage (from repo root):
  python scripts/sync_uk_thumbs.py
  python scripts/sync_uk_thumbs.py --dry-run
  python scripts/sync_uk_thumbs.py --delay 1
  python scripts/sync_uk_thumbs.py --force --output-dir ./my_thumbnails
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
UK_DEFAULTS = [
    "--api-url",
    "https://bdsa.ai.uky.edu/api/v1",
    "--collection-id",
    "693c661493ef0d7395814d2f",
    "--output-dir",
    str(REPO_ROOT / "thumbnails"),
    "--width",
    "2048",
]


def main(argv: list[str] | None = None) -> int:
    # Import sibling module (scripts/ is not a package).
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    from sync_collection_thumbnails import main as sync_main

    user_args = list(argv if argv is not None else sys.argv[1:])
    return sync_main([*UK_DEFAULTS, *user_args])


if __name__ == "__main__":
    raise SystemExit(main())
