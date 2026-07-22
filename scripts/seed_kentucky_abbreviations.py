#!/usr/bin/env python3
"""
Seed Kentucky protocol abbreviation fields onto the live API.

Patches existing regionProtocols / stainProtocols with abbreviation,
schemaRegionKey/schemaStainKey, and displayName from docs/abbreviation_info.md.

Uses GET + full PUT (merge only adds new ids and would not update fields).

Usage:
  docker compose run --rm \\
    -v "$(pwd)/scripts:/scripts:ro" \\
    -e BDSA_API_KEY \\
    backend python /scripts/seed_kentucky_abbreviations.py \\
    --api http://backend:8000

  python scripts/seed_kentucky_abbreviations.py --api http://localhost:8000 --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

REGION_PATCHES: list[dict[str, str]] = [
    {
        "protocolId": "kentucky_region_posterior_hippocampus",
        "abbreviation": "HIPP",
        "schemaRegionKey": "Hippocampus",
        "displayName": "Posterior hippocampus",
    },
    {
        "protocolId": "kentucky_region_anterior_cingulate",
        "abbreviation": "ACg",
        "schemaRegionKey": "Ant_Cingulate",
        "displayName": "Anterior cingulate",
    },
    {
        "protocolId": "kentucky_region_amygdala",
        "abbreviation": "AMYG",
        "schemaRegionKey": "Amygdala",
        "displayName": "Amygdala",
    },
    {
        "protocolId": "kentucky_region_midbrain",
        "abbreviation": "MB",
        "schemaRegionKey": "Midbrain",
        "displayName": "Midbrain",
    },
    {
        "protocolId": "kentucky_region_pons",
        "abbreviation": "PONS",
        "schemaRegionKey": "Pons",
        "displayName": "Pons",
    },
    {
        "protocolId": "kentucky_region_medulla",
        "abbreviation": "MED",
        "schemaRegionKey": "Medulla",
        "displayName": "Medulla",
    },
    {
        "protocolId": "kentucky_region_frontal_gyrus",
        "abbreviation": "FRCTX",
        "schemaRegionKey": "Frontal",
        "displayName": "Frontal gyrus",
    },
    {
        "protocolId": "kentucky_region_temporal_lobe",
        "abbreviation": "TEMP",
        "schemaRegionKey": "Temporal",
        "displayName": "Temporal lobe",
    },
    {
        "protocolId": "kentucky_region_parietal_gyrus",
        "abbreviation": "PAR",
        "schemaRegionKey": "Parietal",
        "displayName": "Parietal gyrus",
    },
    {
        "protocolId": "kentucky_region_visual_cortex_occipital",
        "abbreviation": "OCC",
        "schemaRegionKey": "Occipital",
        "displayName": "Visual cortex (occipital)",
    },
    {
        "protocolId": "kentucky_region_striatum_basal_ganglia",
        "abbreviation": "BG",
        "schemaRegionKey": "Basal_Ganglia",
        "displayName": "Striatum (basal ganglia)",
    },
    {
        "protocolId": "kentucky_region_thalamus",
        "abbreviation": "THAL",
        "schemaRegionKey": "Thalamus",
        "displayName": "Thalamus",
    },
    {
        "protocolId": "kentucky_region_cerebellum",
        "abbreviation": "CB",
        "schemaRegionKey": "Cerebellum",
        "displayName": "Cerebellum",
    },
    {
        "protocolId": "kentucky_region_central_gyri_motor_cortex",
        "abbreviation": "MC",
        "schemaRegionKey": "Motor_cortex",
        "displayName": "Central gyri (motor cortex)",
    },
]

STAIN_PATCHES: list[dict[str, str]] = [
    {
        "protocolId": "kentucky_he",
        "abbreviation": "HE",
        "schemaStainKey": "HE",
        "displayName": "H&E",
    },
    {
        "protocolId": "kentucky_tau",
        "abbreviation": "Tau",
        "schemaStainKey": "Tau",
        "displayName": "Tau",
    },
    {
        "protocolId": "kentucky_asyn",
        "abbreviation": "aSyn",
        "schemaStainKey": "aSyn",
        "displayName": "aSyn",
    },
    {
        "protocolId": "kentucky_abeta",
        "abbreviation": "aBeta",
        "schemaStainKey": "aBeta",
        "displayName": "aBeta",
    },
    {
        "protocolId": "kentucky_tdp43",
        "abbreviation": "TDP-43",
        "schemaStainKey": "TDP-43",
        "displayName": "TDP-43",
    },
]


def load_api_key() -> str | None:
    key = os.environ.get("BDSA_API_KEY")
    if key:
        return key
    env_path = REPO_ROOT / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("BDSA_API_KEY="):
                return line.partition("=")[2].strip().strip("'").strip('"')
    return None


def request_json(
    method: str,
    url: str,
    *,
    api_key: str | None,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Accept": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"{method} {url} -> HTTP {e.code}: {detail}") from e


def patch_list(
    protocols: list[dict[str, Any]],
    patches: list[dict[str, str]],
    *,
    field_keys: tuple[str, ...],
) -> tuple[int, list[str]]:
    by_id = {str(p.get("id")): p for p in protocols if p.get("id")}
    updated = 0
    missing: list[str] = []
    for patch in patches:
        pid = patch["protocolId"]
        target = by_id.get(pid)
        if target is None:
            missing.append(pid)
            continue
        for key in field_keys:
            target[key] = patch[key]
        updated += 1
    return updated, missing


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--collection", default="kentucky")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    api_key = load_api_key()
    base = args.api.rstrip("/")
    url = f"{base}/api/collections/{args.collection}/protocols"

    print(f"GET {url}", file=sys.stderr)
    data = request_json("GET", url, api_key=api_key)
    protocols = data.get("protocols") or data
    stains = list(protocols.get("stainProtocols") or [])
    regions = list(protocols.get("regionProtocols") or [])
    blocks = list(protocols.get("blockProtocols") or [])

    region_n, region_missing = patch_list(
        regions,
        REGION_PATCHES,
        field_keys=("abbreviation", "schemaRegionKey", "displayName"),
    )
    stain_n, stain_missing = patch_list(
        stains,
        STAIN_PATCHES,
        field_keys=("abbreviation", "schemaStainKey", "displayName"),
    )

    print(f"Patched {region_n} regions, {stain_n} stains", file=sys.stderr)
    if region_missing:
        print(f"Missing region protocol ids: {region_missing}", file=sys.stderr)
    if stain_missing:
        print(f"Missing stain protocol ids: {stain_missing}", file=sys.stderr)

    if args.dry_run:
        sample = next((r for r in regions if r.get("abbreviation")), None)
        print("Dry run — sample region:", json.dumps(sample, indent=2)[:500])
        return

    body = {
        "stainProtocols": stains,
        "regionProtocols": regions,
        "blockProtocols": blocks,
        "source": protocols.get("source", "abbreviation_seed"),
        "version": protocols.get("version", "1.0"),
    }
    print(f"PUT {url}", file=sys.stderr)
    saved = request_json("PUT", url, api_key=api_key, body=body)
    saved_protocols = saved.get("protocols") or saved
    print(
        f"Saved. regions={len(saved_protocols.get('regionProtocols') or [])} "
        f"stains={len(saved_protocols.get('stainProtocols') or [])}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
