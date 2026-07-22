#!/usr/bin/env python3
"""
Extract ADRC Neuropath Survey rows and emit Pitt-schema-aligned protocol JSON.

Institutions: Emory, U. Kentucky, UC Davis, Pittsburgh.

Usage:
  python scripts/extract_adrc_survey_protocols.py --all
  python scripts/extract_adrc_survey_protocols.py --institution pittsburgh
  python scripts/extract_adrc_survey_protocols.py --all --import --api http://localhost:8000
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = REPO_ROOT / "docs" / "ADRC_Neuropath_Survey2026-06-01_14_41_40.csv"
OUT_DIR = REPO_ROOT / "docs" / "protocols"

ADRC_COLUMN = "What ADRC are you affiliated with?"

INSTITUTIONS: dict[str, dict[str, Any]] = {
    "emory": {
        "match": lambda adrc: "emory" in adrc.lower(),
        "slug": "emory",
        "display": "Emory University",
        "collection_id": "emory",
    },
    "kentucky": {
        "match": lambda adrc: "kentucky" in adrc.lower(),
        "slug": "kentucky",
        "display": "U. Kentucky",
        "collection_id": "kentucky",
    },
    "uc-davis": {
        "match": lambda adrc: "uc davis" in adrc.lower(),
        "slug": "uc-davis",
        "display": "UC Davis",
        "collection_id": "uc-davis",
    },
    "pittsburgh": {
        "match": lambda adrc: adrc.lower() in ("pittsburgh", "university of pittsburgh")
            or adrc.lower().startswith("pittsburgh"),
        "slug": "pittsburgh",
        "display": "Pittsburgh",
        "collection_id": "pittsburgh",
    },
}

LANDMARK_MAP: dict[str, str] = {
    "Corpus Callosum": "Corpus callosum",
    "Superior Frontal": "Superior frontal",
    "CA1-4 with dentate gyrus": "CA1-4 with dentate gyrus",
    "Parahippocampal Gyrus": "Parahippocampal gyrus",
    "Tail of caudate": "Tail of caudate",
    "Lateral Geniculate Nucleus": "Lateral geniculate nucleus",
    "Occipital Temporal Gyrus": "Occipital temporal gyrus",
    "Entorhinal Cortex": "Entorhinal cortex",
    "3rd Cranial Nerve": "3rd cranial nerve",
    "Substantia Nigra": "Substantia nigra",
    "Red Nucleus": "Red nucleus",
    "Superior Colliculus": "Superior colliculus",
    "Superior Cerebellar Peduncle": "Superior cerebellar peduncle",
    "Inferior Colliculus": "Inferior colliculus",
    "Locus Coeruleus": "Locus coeruleus",
    "Pontine Base / Fibers": "Pontine base / fibers",
    "Dorsal Motor Nucleus of the Vagus": "Dorsal motor nucleus of vagus",
    "Hypoglossal Nucleus": "Hypoglossal nucleus",
    "Inferior Olive": "Inferior olive",
    "Medullary Velum": "Medullary velum",
    "Pyramid": "Pyramid",
    "Superior": "Superior",
    "Middle": "Middle",
    "MIddle": "Middle",
    "Inferior": "Inferior",
    "Angular gyrus": "Angular gyrus",
    "Supramarginal gyrus": "Supramarginal gyrus",
    "Mammillary Body": "Mammillary body",
    "Subthalamic Nucleus": "Subthalamic nucleus",
    "Mammilo-thalamic Tract": "Mammilo-thalmaic tract",
    "Anterior Nucleus of the thalamus": "Anterior nucleus of thalamus",
    "Pulvinar": "Pulvinar",
    "Dentate": "Dentate",
    "Vermis": "Vermis",
    "Cortex": "Cortex",
    "Pre": "Pre",
    "Post": "Post",
    "Anterior Commissure": "Anterior Commissure",
    "Nucleus Basalis of Meynert": "Nucleus Basalis of Meynert",
    "Globus Pallidus": "Globus Pallidus",
    "Caudate": "Caudate",
    "Caudate Head": "Caudate head",
    "Caudate head": "Caudate head",
    "Internal Capsule": "Internal Capsule",
    "External Capsule": "External Capsule",
    "Putamen": "Putamen",
    "Nucleus Accumbens": "Nucleus Accumbens",
    "Line of Gennari (BA17)": "Line of Gennari (BA17)",
    "Line of Gennari": "Line of Gennari (BA17)",
    "BA17": "BA17",
    "BA18": "BA18",
    "BA19": "BA19",
    "Super": "Super",
}

REGION_SECTIONS: list[tuple[str, str, str, str]] = [
    ("Posterior Hippocampus Landmarks", "Posterior Hippocampus Stains", "Hippocampus", "Posterior hippocampus"),
    ("Anterior Cingulate Gyrus Landmarks", "Anterior Cingulate Gyrus Stains", "Ant_Cingulate", "Anterior cingulate"),
    ("Amygdala Landmarks", "Amygdala Stains", "Amygdala", "Amygdala"),
    ("Midbrain Landmarks", "Midbrain Stains", "Midbrain", "Midbrain"),
    ("Pons Landmarks", "Pons Stains", "Pons", "Pons"),
    ("Medulla Landmarks", "Medulla Stains", "Medulla", "Medulla"),
    ("Frontal Gyri Landmarks", "Frontal Gyri Stains", "Frontal", "Frontal gyrus"),
    ("Temporal Lobe Landmarks", "Temporal Lobe Stains", "Temporal", "Temporal lobe"),
    ("parietalGyriLandmarks", "Parietal Gyri Stains", "Parietal", "Parietal gyrus"),
    ("Visual Cortex Landmarks", "Visual Cortex Stains", "Occipital", "Visual cortex (occipital)"),
    ("Striatum Landmarks", "Striatum Stains", "Basal_Ganglia", "Striatum (basal ganglia)"),
    ("Thalamus Landmarks", "Thalamus Stains", "Thalamus", "Thalamus"),
    ("Cerebellum Landmarks", "Cerebellum Stains", "Cerebellum", "Cerebellum"),
    ("Central Gyri Landmarks", "Central Gyri Stains", "Motor_cortex", "Central gyri (motor cortex)"),
]

ABETA_ENUM = ["4G8", "6E10", "12F4", "unknown"]
ASYN_ENUM = ["KM51", "5G4", "LB509", "unknown"]
TDP_ENUM = ["pS409/410", "1D3", "unknown"]
TAU_ENUM = ["AT8", "PHF1", "CP13", "unknown"]
PHOSPHO_ONLY = frozenset(
    {"phospho-specific", "phospho specific", "non-phospho specific", "non-phospho specific"}
)


def parse_checked_field(raw: str | None) -> list[str]:
    if not raw:
        return []
    values: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if line.upper().startswith("CHECKED:"):
            label = line.split(":", 1)[1].strip()
            if label.lower() in ("not collected", "other", "region collected"):
                continue
            values.append(label)
    return values


def parse_stain_lines(raw: str | None) -> list[str]:
    if not raw:
        return []
    stains: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.upper().startswith("UNCHECKED:"):
            continue
        if line.lower().startswith("checked:"):
            line = line.split(":", 1)[1].strip()
        stains.append(line)
    return stains


def normalize_landmarks(survey_labels: list[str]) -> list[str]:
    out: list[str] = []
    for label in survey_labels:
        mapped = LANDMARK_MAP.get(label, label)
        if mapped not in out:
            out.append(mapped)
    return out


def vendor_token(raw: str | None) -> str | None:
    if not raw or not raw.strip():
        return None
    token = re.sub(r"[^\w]", "", raw.split(",")[0].split()[0])
    return token or None


def parse_thickness(raw: str | None) -> float:
    if not raw or not str(raw).strip():
        return 8.0
    text = str(raw).strip().replace("μm", "").replace("um", "")
    if "-" in text:
        lo, hi = text.split("-", 1)
        return (float(lo) + float(hi)) / 2.0
    return float(text)


def phospho_from_cell(cell: str | None) -> str | None:
    if not cell:
        return None
    low = cell.strip().lower()
    if low in ("phospho-specific", "phospho specific"):
        return "yes"
    if low in ("non-phospho specific", "non-phospho specific"):
        return "no"
    return None


def pick_enum(
    antibody_cell: str | None,
    vendor_cell: str | None,
    allowed: list[str],
) -> str:
    ab = (antibody_cell or "").strip()
    vendor = (vendor_cell or "").strip()
    combined = f"{ab} {vendor}".upper()

    if ab and ab.lower() not in PHOSPHO_ONLY:
        for item in allowed:
            if ab.lower() == item.lower():
                return item

    for item in allowed:
        if item == "unknown":
            continue
        if item.upper() in combined or item.lower() in vendor.lower():
            return item

    if "NAB228" in combined:
        return "unknown"
    if "4G8" in combined:
        return "4G8"
    if "6E10" in combined:
        return "6E10"
    if "12F4" in combined:
        return "12F4"
    if "LB509" in combined:
        return "LB509"
    if "5G4" in combined:
        return "5G4"
    if "KM51" in combined:
        return "KM51"
    if "1D3" in combined or "1d3" in (antibody_cell or ""):
        return "1D3"
    if "PHF1" in combined:
        return "PHF1"
    if "AT8" in combined:
        return "AT8"
    if "CP13" in combined:
        return "CP13"
    if "P409" in combined or "409" in combined:
        return "pS409/410"

    return "unknown"


def resolve_chromogen(row: dict[str, str]) -> str:
    special = (row.get("Special Preparation / Additional Info, average cost per slide of IHC?") or "").lower()
    if "nova red" in special:
        return "AEC (Red)"
    dab = (
        row.get(
            "How do you currently process / counterstain your IHC slides?  Check all that apply. >> DAB as chromogen (brown) with no enhancement:",
        )
        or ""
    ).strip().lower()
    if dab == "yes":
        return "DAB (Brown)"
    return "DAB (Brown)"


def counterstain_note(row: dict[str, str], chromogen: str) -> str:
    hema = (
        row.get(
            "How do you currently process / counterstain your IHC slides?  Check all that apply. >> Hematoxylin Counter Stain Used",
        )
        or ""
    ).strip()
    nickel = (
        row.get(
            "How do you currently process / counterstain your IHC slides?  Check all that apply. >> DAB as chromogen with nickel enhancement",
        )
        or ""
    ).strip()
    parts = []
    if hema.lower() == "yes":
        parts.append("hematoxylin counterstain")
    parts.append(f"chromogen {chromogen}")
    if nickel.lower() == "yes":
        parts.append("DAB with nickel enhancement")
    special = (row.get("Special Preparation / Additional Info, average cost per slide of IHC?") or "").strip()
    if special:
        parts.append(special[:200])
    return "; ".join(parts)


def row_uses_silver(row: dict[str, str]) -> bool:
    for _lm, stain_col, _rt, _label in REGION_SECTIONS:
        for stain in parse_stain_lines(row.get(stain_col)):
            if "silver" in stain.lower():
                return True
    return False


def load_row(csv_path: Path, matcher: Callable[[str], bool]) -> dict[str, str]:
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            adrc = (row.get(ADRC_COLUMN) or "").strip()
            if matcher(adrc):
                return row
    raise KeyError(f"No matching survey row in {csv_path}")


def build_stain_protocols(row: dict[str, str], slug: str, display: str) -> list[dict[str, Any]]:
    submitted = (row.get("Submission Date") or "").strip()
    chromogen = resolve_chromogen(row)
    processing = counterstain_note(row, chromogen)
    note = f"Derived from {display} ADRC Neuropath Survey ({submitted}). {processing}."

    ab_antibody = pick_enum(row.get("aBeta Antibody"), row.get("aBeta Vendor / Clone Info"), ABETA_ENUM)
    ab_phospho = phospho_from_cell(row.get("aBeta Antibody")) or "no"

    asyn_antibody = pick_enum(
        row.get("Alpha Synuclein Antibody"),
        row.get("Alpha Synuclein Vendor / Clone Info"),
        ASYN_ENUM,
    )
    asyn_phospho = phospho_from_cell(row.get("Alpha Synuclein Antibody")) or (
        "yes" if "phospho" in (row.get("Alpha Synuclein Antibody") or "").lower() else "no"
    )

    tdp_antibody = pick_enum(row.get("TDP43 Antibody"), row.get("TDP43 Vendor / Clone Info"), TDP_ENUM)
    tdp_phospho = phospho_from_cell(row.get("TDP43 Antibody")) or (
        "yes" if "phospho" in (row.get("TDP43 Antibody") or "").lower() else "no"
    )

    tau_antibody = pick_enum(row.get("Tau Antibody"), row.get("Tau Vendor / Clone Info"), TAU_ENUM)
    tau_phospho = phospho_from_cell(row.get("Tau Antibody"))
    if tau_phospho is None and tau_antibody in ("PHF1", "AT8", "CP13"):
        tau_phospho = "yes" if tau_antibody in ("PHF1", "AT8") else "no"
    if tau_phospho is None:
        tau_phospho = "yes"

    protocols: list[dict[str, Any]] = [
        {
            "id": f"{slug}_he",
            "type": "stain",
            "name": f"{display} H&E",
            "description": f"{note} Standard histology.",
            "stainType": "HE",
            "chemistry": "dye binding",
        },
        {
            "id": f"{slug}_abeta",
            "type": "stain",
            "name": f"{display} amyloid beta ({ab_antibody})",
            "description": (
                f"{note} Survey: {row.get('aBeta Antibody', '').strip()} "
                f"{row.get('aBeta Vendor / Clone Info', '').strip()}".strip()
            ),
            "stainType": "aBeta",
            "antibody": ab_antibody,
            "phosphoSpecific": ab_phospho,
            "chromogen": chromogen,
        },
        {
            "id": f"{slug}_tau",
            "type": "stain",
            "name": f"{display} tau ({tau_antibody})",
            "description": (
                f"{note} Survey: {row.get('Tau Antibody', '').strip()} "
                f"{row.get('Tau Vendor / Clone Info', '').strip()}".strip()
            ),
            "stainType": "Tau",
            "antibody": tau_antibody,
            "phosphoSpecific": tau_phospho,
            "chromogen": chromogen,
        },
        {
            "id": f"{slug}_asyn",
            "type": "stain",
            "name": f"{display} alpha-synuclein ({asyn_antibody})",
            "description": (
                f"{note} Survey: {row.get('Alpha Synuclein Antibody', '').strip()} "
                f"{row.get('Alpha Synuclein Vendor / Clone Info', '').strip()}".strip()
            ),
            "stainType": "aSyn",
            "antibody": asyn_antibody,
            "phosphoSpecific": asyn_phospho,
            "chromogen": chromogen,
        },
        {
            "id": f"{slug}_tdp43",
            "type": "stain",
            "name": f"{display} TDP-43 ({tdp_antibody})",
            "description": (
                f"{note} Survey: {row.get('TDP43 Antibody', '').strip()} "
                f"{row.get('TDP43 Vendor / Clone Info', '').strip()}".strip()
            ),
            "stainType": "TDP-43",
            "antibody": tdp_antibody,
            "phosphoSpecific": tdp_phospho,
            "chromogen": chromogen,
        },
    ]

    for proto, vendor_col in (
        (protocols[1], "aBeta Vendor / Clone Info"),
        (protocols[2], "Tau Vendor / Clone Info"),
        (protocols[4], "TDP43 Vendor / Clone Info"),
    ):
        v = vendor_token(row.get(vendor_col))
        ab = str(proto.get("antibody", "")).lower()
        if v and v.lower() not in (ab, "peter", "1d3") and len(v) > 2:
            proto["vendor"] = v

    if row_uses_silver(row):
        protocols.append(
            {
                "id": f"{slug}_silver_bielschowsky",
                "type": "stain",
                "name": f"{display} silver (Bielschowsky)",
                "description": f"{note} Survey label: Silver stain; mapped to Bielschowsky in Pitt schema.",
                "stainType": "Bielschowsky",
                "chemistry": "silver impregnation",
            }
        )

    return protocols


def region_is_collected(landmarks_raw: str | None, stains_raw: str | None) -> bool:
    if parse_checked_field(landmarks_raw):
        return True
    stains = parse_stain_lines(stains_raw)
    return any(
        s and s.lower() not in ("not collected",) and "uncheck" not in s.lower() for s in stains
    )


def normalize_hemisphere(raw: str | None) -> str:
    value = (raw or "").strip().lower()
    if value in ("both", "bilateral"):
        return "bilateral"
    if value in ("left", "right", "unknown"):
        return value
    return "unknown"


def build_region_protocols(row: dict[str, str], slug: str, display: str) -> list[dict[str, Any]]:
    slice_thickness = parse_thickness(row.get("Average Section thickness in μm:"))
    hemisphere = normalize_hemisphere(row.get("Brain Hemisphere"))
    submitted = (row.get("Submission Date") or "").strip()

    protocols: list[dict[str, Any]] = []

    for lm_col, stain_col, region_type, label in REGION_SECTIONS:
        if not region_is_collected(row.get(lm_col), row.get(stain_col)):
            continue

        survey_lm = parse_checked_field(row.get(lm_col))
        landmarks = normalize_landmarks(survey_lm)
        survey_stains = parse_stain_lines(row.get(stain_col))

        region_slug = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
        proto: dict[str, Any] = {
            "id": f"{slug}_region_{region_slug}",
            "type": "region",
            "name": f"{display} — {label}",
            "description": (
                f"From {display} ADRC Neuropath Survey ({submitted}). "
                f"Survey stains: {', '.join(survey_stains) or 'see institution panel'}. "
                "Sampling per survey (typically after coronal slicing when indicated)."
            ),
            "regionType": region_type,
            "hemisphere": hemisphere,
            "sliceOrientation": "coronal",
            "sliceThickness": slice_thickness,
        }
        if landmarks:
            proto["landmarks"] = landmarks
        elif survey_lm:
            proto["description"] += f" Survey landmarks (no Pitt enum): {', '.join(survey_lm)}."
        if region_type in ("Occipital", "Basal_Ganglia", "Motor_cortex") and survey_lm:
            proto["description"] += f" Survey landmarks: {', '.join(survey_lm)}."

        protocols.append(proto)

    return protocols


def build_payload(row: dict[str, str], meta: dict[str, Any]) -> dict[str, Any]:
    slug = meta["slug"]
    display = meta["display"]
    return {
        "institution": row.get(ADRC_COLUMN, display),
        "surveySource": "ADRC_Neuropath_Survey2026-06-01_14_41_40.csv",
        "surveySubmissionDate": row.get("Submission Date", ""),
        "surveyRole": row.get("What is your role in the ADRC?", ""),
        "scanner": row.get(
            "What type of slide scanner does your ADRC primarily have access to/use ?",
            "",
        ),
        "stainProtocols": build_stain_protocols(row, slug, display),
        "regionProtocols": build_region_protocols(row, slug, display),
        "notes": [
            "P62 / CD68 / other survey stains may not have Pitt schema stain types — see region descriptions.",
            "Antibody fields that only say phospho/non-phospho are resolved from vendor/clone columns.",
            "Regions marked Not Collected in the survey are omitted.",
        ],
    }


def api_request(
    api_base: str,
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
) -> None:
    url = f"{api_base.rstrip('/')}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"} if data else {},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            print(f"  {method} {path}: HTTP {resp.status}", file=sys.stderr)
    except urllib.error.HTTPError as e:
        print(e.read().decode(), file=sys.stderr)
        raise SystemExit(1) from e


def import_to_api(
    payload: dict[str, Any],
    collection_id: str,
    api_base: str,
    slug: str,
    display_name: str,
) -> None:
    """PUT protocols and register collection display name so the UI picker lists it."""
    api_request(
        api_base,
        "PUT",
        f"/api/collections/{collection_id}/metadata",
        {"display_name": display_name},
    )
    api_request(
        api_base,
        "PUT",
        f"/api/collections/{collection_id}/protocols",
        {
            "stainProtocols": payload["stainProtocols"],
            "regionProtocols": payload["regionProtocols"],
            "blockProtocols": payload.get("blockProtocols", []),
            "source": f"{slug}-adrc-survey-import",
            "version": "1.0",
        },
    )


def extract_one(
    csv_path: Path,
    key: str,
    *,
    do_import: bool,
    api_base: str,
) -> Path:
    meta = INSTITUTIONS[key]
    row = load_row(csv_path, meta["match"])
    payload = build_payload(row, meta)
    out_path = OUT_DIR / f"{meta['slug']}-adrc-survey-protocols.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(
        f"{meta['display']}: {len(payload['stainProtocols'])} stain + "
        f"{len(payload['regionProtocols'])} region → {out_path.name}"
    )
    if do_import:
        import_to_api(
            payload,
            meta["collection_id"],
            api_base,
            meta["slug"],
            meta["display"],
        )
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract ADRC survey protocols (Pitt schema)")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument(
        "--institution",
        choices=[*INSTITUTIONS.keys(), "all"],
        default="all",
        help="Which institution row to extract (default: all)",
    )
    parser.add_argument("--import", dest="do_import", action="store_true")
    parser.add_argument("--api", default="http://localhost:8000")
    args = parser.parse_args()

    keys = list(INSTITUTIONS.keys()) if args.institution == "all" else [args.institution]
    for key in keys:
        try:
            extract_one(args.csv, key, do_import=args.do_import, api_base=args.api)
        except KeyError as e:
            print(f"SKIP {key}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
