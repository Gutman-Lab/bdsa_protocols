#!/usr/bin/env python3
"""
Stream NACC investigator CSV into Mongo clinical_by_nacc (one doc per NACCID).

Maps only clinical-metadata.json fields:
  NACCID, NPSEX, EDUC, HISPANIC<-NACCHISP, RACE, NACCDAGE, NACCUDSD,
  NPPMIH, NPADNC, NPWBRWT

Visit collapse:
  - UDS fields from the latest visit (max NACCVNUM, then VISITDATE)
  - Neuropath / death fields from the latest visit with a non-missing value

Usage:
  # Prefer docker (pymongo is in the backend image):
  docker compose run --rm \\
    -v \"$(pwd)/docs:/data:ro\" -v \"$(pwd)/scripts:/scripts:ro\" \\
    backend python /scripts/import_nacc_clinical.py \\
    --csv /data/investigator_nacc74.csv \\
    --mongodb-url mongodb://mongodb:27017

  python scripts/import_nacc_clinical.py --dry-run --limit 1000
  python scripts/import_nacc_clinical.py --csv docs/investigator_nacc74.csv
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = REPO_ROOT / "docs" / "investigator_nacc74.csv"
COLLECTION = "clinical_by_nacc"
SOURCE = "investigator_nacc74"

# Columns we need from the dump (CSV has 1700+ columns).
NEEDED_COLS = (
    "NACCID",
    "NACCVNUM",
    "VISITDATE",
    "NPSEX",
    "NACCSEX",
    "EDUC",
    "NACCHISP",
    "RACE",
    "NACCDAGE",
    "NACCUDSD",
    "NPPMIH",
    "NPADNC",
    "NPWBRWT",
)

# UDS / demography fields taken from the latest visit overall.
LATEST_VISIT_FIELDS = ("EDUC", "HISPANIC", "RACE", "NACCUDSD", "NPSEX")

# Prefer non-missing value from the latest visit that has it.
BEST_AVAILABLE_FIELDS = ("NACCDAGE", "NPPMIH", "NPADNC", "NPWBRWT", "NPSEX")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_int(raw: str | None) -> int | None:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def _parse_float(raw: str | None) -> float | None:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _is_missing_int(value: int | None, *, field: str) -> bool:
    if value is None:
        return True
    # Universal NACC "not available / skipped form" codes
    if value in (-4, -9):
        return True
    if field == "NACCDAGE" and value in (888, 999):
        return True
    if field == "EDUC" and value in (88, 99):
        return True
    if field in ("NPSEX", "NACCSEX") and value not in (1, 2):
        return True
    # Keep schema-valid unknowns: HISPANIC=9, RACE=99, NPADNC=8/9, etc.
    return False


def _is_missing_float(value: float | None) -> bool:
    if value is None:
        return True
    # NPPMIH: -4 / -4.4 not available; 99.9 unknown
    if value <= -4 or value >= 99.9:
        return True
    return False


def _visit_key(row: dict[str, str]) -> tuple[int, str]:
    vnum = _parse_int(row.get("NACCVNUM")) or 0
    date = (row.get("VISITDATE") or "").strip()
    return (vnum, date)


def _sex_from_row(row: dict[str, str]) -> int | None:
    npsex = _parse_int(row.get("NPSEX"))
    if not _is_missing_int(npsex, field="NPSEX") and npsex in (1, 2):
        return npsex
    naccsex = _parse_int(row.get("NACCSEX"))
    if not _is_missing_int(naccsex, field="NACCSEX") and naccsex in (1, 2):
        return naccsex
    return None


def _extract_visit_values(row: dict[str, str]) -> dict[str, Any]:
    """Parse clinical-schema values from one CSV visit row (None = missing)."""
    educ = _parse_int(row.get("EDUC"))
    hispanic = _parse_int(row.get("NACCHISP"))
    race = _parse_int(row.get("RACE"))
    naccudsd = _parse_int(row.get("NACCUDSD"))
    naccdage = _parse_int(row.get("NACCDAGE"))
    npadnc = _parse_int(row.get("NPADNC"))
    npwbrwt = _parse_int(row.get("NPWBRWT"))
    nppmih = _parse_float(row.get("NPPMIH"))

    return {
        "NPSEX": _sex_from_row(row),
        "EDUC": None if _is_missing_int(educ, field="EDUC") else educ,
        "HISPANIC": None if _is_missing_int(hispanic, field="HISPANIC") else hispanic,
        "RACE": None if _is_missing_int(race, field="RACE") else race,
        "NACCUDSD": None if _is_missing_int(naccudsd, field="NACCUDSD") else naccudsd,
        "NACCDAGE": None if _is_missing_int(naccdage, field="NACCDAGE") else naccdage,
        "NPADNC": None if _is_missing_int(npadnc, field="NPADNC") else npadnc,
        "NPWBRWT": None if _is_missing_int(npwbrwt, field="NPWBRWT") else npwbrwt,
        "NPPMIH": None if _is_missing_float(nppmih) else nppmih,
    }


def collapse_visits(
    visits: list[tuple[tuple[int, str], dict[str, Any]]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Collapse visit value dicts into one clinical payload + visitMeta.

    visits: list of (visit_key, values) already sorted or unsorted.
    """
    if not visits:
        return {}, {}
    visits_sorted = sorted(visits, key=lambda x: x[0])
    latest_key, latest_vals = visits_sorted[-1]

    clinical: dict[str, Any] = {}
    for field in LATEST_VISIT_FIELDS:
        clinical[field] = latest_vals.get(field)

    for field in BEST_AVAILABLE_FIELDS:
        chosen = None
        for _key, vals in reversed(visits_sorted):
            v = vals.get(field)
            if v is not None:
                chosen = v
                break
        if field == "NPSEX":
            # Prefer best available NPSEX; fall back to latest-visit sex already set
            if chosen is not None:
                clinical["NPSEX"] = chosen
        else:
            clinical[field] = chosen

    visit_meta = {
        "naccvnum": latest_key[0] or None,
        "visitDate": latest_key[1] or None,
    }
    return clinical, visit_meta


def load_env_defaults() -> tuple[str, str]:
    """Read Mongo settings from repo .env if present (BDSA_MONGODB_*)."""
    url = os.environ.get("BDSA_MONGODB_URL") or os.environ.get("MONGODB_URL")
    db = os.environ.get("BDSA_MONGODB_DB") or os.environ.get("MONGODB_DB")
    env_path = REPO_ROOT / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip("'").strip('"')
            if key == "BDSA_MONGODB_URL" and not url:
                url = val
            elif key == "BDSA_MONGODB_DB" and not db:
                db = val
            # Also accept unprefixed forms used in some compose files
            elif key == "MONGODB_URL" and not url:
                url = val
            elif key == "MONGODB_DB" and not db:
                db = val
    return url or "mongodb://localhost:27017", db or "bdsa_protocols"


def stream_and_collapse(
    csv_path: Path,
    *,
    limit_rows: int | None = None,
) -> dict[str, dict[str, Any]]:
    """
    Stream CSV and return naccid -> {clinical, visitMeta}.

    Uses column indices so we do not keep 1700+ unused fields per row.
    Keeps all visits per NACCID in memory for collapse (57k IDs × ~3 visits is fine).
    """
    by_id: dict[str, list[tuple[tuple[int, str], dict[str, Any]]]] = {}
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            raise SystemExit(f"Empty CSV: {csv_path}") from None

        # Strip BOM / quotes already handled by csv.reader
        index = {name: i for i, name in enumerate(header)}
        missing = [c for c in NEEDED_COLS if c not in index]
        if missing:
            raise SystemExit(f"CSV missing required columns: {missing}")

        def cell(row: list[str], name: str) -> str:
            i = index[name]
            return row[i] if i < len(row) else ""

        for i, row in enumerate(reader):
            if limit_rows is not None and i >= limit_rows:
                break
            naccid = cell(row, "NACCID").strip()
            if not naccid:
                continue
            slim = {name: cell(row, name) for name in NEEDED_COLS}
            key = _visit_key(slim)
            vals = _extract_visit_values(slim)
            by_id.setdefault(naccid, []).append((key, vals))
            if (i + 1) % 50000 == 0:
                print(f"  … read {i + 1} visit rows ({len(by_id)} NACC IDs)", file=sys.stderr)

    out: dict[str, dict[str, Any]] = {}
    for naccid, visits in by_id.items():
        clinical, visit_meta = collapse_visits(visits)
        clinical["NACCID"] = naccid
        out[naccid] = {"clinical": clinical, "visitMeta": visit_meta}
    return out


def upsert_docs(
    docs: dict[str, dict[str, Any]],
    *,
    mongodb_url: str,
    mongodb_db: str,
    batch_size: int = 1000,
) -> int:
    from pymongo import MongoClient, UpdateOne

    client = MongoClient(mongodb_url)
    col = client[mongodb_db][COLLECTION]
    col.create_index("naccid", unique=True)

    now = _now_iso()
    ops: list[UpdateOne] = []
    written = 0
    for naccid, payload in docs.items():
        doc = {
            "naccid": naccid,
            "clinical": payload["clinical"],
            "source": SOURCE,
            "visitMeta": payload["visitMeta"],
            "lastUpdated": now,
        }
        ops.append(UpdateOne({"naccid": naccid}, {"$set": doc}, upsert=True))
        if len(ops) >= batch_size:
            result = col.bulk_write(ops, ordered=False)
            written += result.upserted_count + result.modified_count
            ops = []
            print(f"  … upserted batch (running total ops ~{written})", file=sys.stderr)
    if ops:
        result = col.bulk_write(ops, ordered=False)
        written += result.upserted_count + result.modified_count
    client.close()
    return written


def main() -> None:
    default_url, default_db = load_env_defaults()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV,
        help=f"Path to investigator CSV (default: {DEFAULT_CSV})",
    )
    parser.add_argument("--mongodb-url", default=default_url)
    parser.add_argument("--mongodb-db", default=default_db)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and collapse only; do not write Mongo",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only read first N visit rows (for testing)",
    )
    parser.add_argument("--batch-size", type=int, default=1000)
    args = parser.parse_args()

    if not args.csv.is_file():
        raise SystemExit(f"CSV not found: {args.csv}")

    print(f"Reading {args.csv} …", file=sys.stderr)
    docs = stream_and_collapse(args.csv, limit_rows=args.limit)
    print(f"Collapsed to {len(docs)} NACCID records", file=sys.stderr)

    # Show a sample
    sample_id = next(iter(docs))
    print(f"Sample {sample_id}: {docs[sample_id]['clinical']}", file=sys.stderr)

    if args.dry_run:
        print("Dry run — skipping Mongo write", file=sys.stderr)
        return

    print(f"Upserting into {args.mongodb_url} / {args.mongodb_db}.{COLLECTION} …", file=sys.stderr)
    n = upsert_docs(
        docs,
        mongodb_url=args.mongodb_url,
        mongodb_db=args.mongodb_db,
        batch_size=args.batch_size,
    )
    print(f"Done. bulk_write upserted+modified ≈ {n}", file=sys.stderr)


if __name__ == "__main__":
    main()
