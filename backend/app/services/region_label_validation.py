"""Validation helpers for REGIONO text -> regionProtocolId mappings."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


@dataclass
class RegionLabelMappingConflict:
    kind: str
    message: str
    region_label: str | None = None
    normalized: str | None = None
    region_protocol_id: str | None = None
    existing_region_protocol_id: str | None = None
    requested_region_protocol_id: str | None = None

    def to_conflict_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"kind": self.kind}
        if self.region_label is not None:
            data["regionLabel"] = self.region_label
        if self.normalized is not None:
            data["normalized"] = self.normalized
        if self.region_protocol_id is not None:
            data["regionProtocolId"] = self.region_protocol_id
        if self.existing_region_protocol_id is not None:
            data["existingRegionProtocolId"] = self.existing_region_protocol_id
        if self.requested_region_protocol_id is not None:
            data["requestedRegionProtocolId"] = self.requested_region_protocol_id
        return data


class RegionLabelMappingError(Exception):
    http_status: int = 409

    def __init__(self, message: str, conflict: RegionLabelMappingConflict | None = None):
        super().__init__(message)
        self.message = message
        self.conflict = conflict.to_conflict_dict() if conflict else None


class RegionLabelMappingConflictError(RegionLabelMappingError):
    http_status = 409


class RegionLabelMappingValidationError(RegionLabelMappingError):
    http_status = 422


def normalize_region_label(label: str) -> str:
    """Normalize REGIONO text (NFKD, lowercase, alphanumeric tokens)."""
    if not label:
        return ""
    nfkd = unicodedata.normalize("NFKD", label.strip())
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    lowered = stripped.lower().strip()
    spaced = _NON_ALNUM.sub(" ", lowered)
    return re.sub(r"\s+", " ", spaced).strip()


def prepare_mapping_row(row: dict[str, Any]) -> dict[str, Any]:
    """Ensure normalized key and display label are present."""
    region_label = (row.get("regionLabel") or "").strip()
    normalized = (row.get("normalized") or "").strip()
    if not normalized and region_label:
        normalized = normalize_region_label(region_label)
    if not region_label and normalized:
        region_label = normalized
    if not normalized:
        raise RegionLabelMappingValidationError(
            "regionLabel is required",
            RegionLabelMappingConflict(kind="invalid_region_label"),
        )
    prepared = dict(row)
    prepared["regionLabel"] = region_label
    prepared["normalized"] = normalized
    if "validated" not in prepared:
        prepared["validated"] = True
    if not (prepared.get("sourceField") or "").strip():
        prepared["sourceField"] = "REGIONO"
    else:
        prepared["sourceField"] = str(prepared["sourceField"]).strip()
    return prepared


def build_mapping_indexes(
    mappings: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    by_normalized: dict[str, dict[str, Any]] = {}
    for row in mappings:
        normalized = row.get("normalized")
        if normalized:
            by_normalized[normalized] = row
    return by_normalized


def validate_region_protocol_ids(
    mappings: list[dict[str, Any]],
    valid_protocol_ids: set[str],
) -> list[RegionLabelMappingConflict]:
    conflicts: list[RegionLabelMappingConflict] = []
    for row in mappings:
        protocol_id = row.get("regionProtocolId")
        if not protocol_id:
            conflicts.append(
                RegionLabelMappingConflict(
                    kind="invalid_region_label",
                    message="regionProtocolId is required",
                    region_label=row.get("regionLabel"),
                    normalized=row.get("normalized"),
                )
            )
            continue
        if protocol_id not in valid_protocol_ids:
            conflicts.append(
                RegionLabelMappingConflict(
                    kind="unknown_region_protocol",
                    message="regionProtocolId not found in collection regionProtocols",
                    region_label=row.get("regionLabel"),
                    normalized=row.get("normalized"),
                    region_protocol_id=protocol_id,
                    requested_region_protocol_id=protocol_id,
                )
            )
    return conflicts


def validate_payload_internal(
    mappings: list[dict[str, Any]],
    valid_protocol_ids: set[str],
) -> list[RegionLabelMappingConflict]:
    conflicts: list[RegionLabelMappingConflict] = []
    prepared_rows: list[dict[str, Any]] = []
    for row in mappings:
        try:
            prepared_rows.append(prepare_mapping_row(row))
        except RegionLabelMappingValidationError as exc:
            if exc.conflict:
                conflicts.append(
                    RegionLabelMappingConflict(
                        kind=exc.conflict["kind"],
                        message=exc.message,
                    )
                )

    conflicts.extend(validate_region_protocol_ids(prepared_rows, valid_protocol_ids))

    by_normalized: dict[str, dict[str, Any]] = {}
    for row in prepared_rows:
        normalized = row["normalized"]
        protocol_id = row.get("regionProtocolId")
        if normalized in by_normalized:
            existing = by_normalized[normalized]
            if existing.get("regionProtocolId") != protocol_id:
                conflicts.append(
                    RegionLabelMappingConflict(
                        kind="duplicate_region_label",
                        message="Duplicate normalized label with different regionProtocolId in payload",
                        region_label=row.get("regionLabel"),
                        normalized=normalized,
                        existing_region_protocol_id=existing.get("regionProtocolId"),
                        requested_region_protocol_id=protocol_id,
                    )
                )
        by_normalized[normalized] = row

    return conflicts


def validate_merge_against_existing(
    existing_mappings: list[dict[str, Any]],
    proposed_mappings: list[dict[str, Any]],
    valid_protocol_ids: set[str],
) -> list[RegionLabelMappingConflict]:
    prepared = [prepare_mapping_row(row) for row in proposed_mappings]
    conflicts = validate_payload_internal(prepared, valid_protocol_ids)
    if conflicts:
        return conflicts

    existing_by_norm = build_mapping_indexes(existing_mappings)
    for row in prepared:
        normalized = row["normalized"]
        protocol_id = row.get("regionProtocolId")
        existing = existing_by_norm.get(normalized)
        if existing is not None and existing.get("regionProtocolId") != protocol_id:
            conflicts.append(
                RegionLabelMappingConflict(
                    kind="region_label_reassigned",
                    message="normalized region label already mapped",
                    region_label=row.get("regionLabel"),
                    normalized=normalized,
                    existing_region_protocol_id=existing.get("regionProtocolId"),
                    requested_region_protocol_id=protocol_id,
                )
            )
    return conflicts


def raise_on_conflicts(conflicts: list[RegionLabelMappingConflict]) -> None:
    if not conflicts:
        return
    first = conflicts[0]
    status = 422 if first.kind == "unknown_region_protocol" else 409
    exc_cls = (
        RegionLabelMappingValidationError
        if status == 422
        else RegionLabelMappingConflictError
    )
    raise exc_cls(first.message, first)
