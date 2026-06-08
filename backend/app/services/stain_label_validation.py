"""Validation helpers for STAINO text -> stainProtocolId mappings."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.region_label_validation import normalize_region_label


@dataclass
class StainLabelMappingConflict:
    kind: str
    message: str
    stain_label: str | None = None
    normalized: str | None = None
    stain_protocol_id: str | None = None
    existing_stain_protocol_id: str | None = None
    requested_stain_protocol_id: str | None = None

    def to_conflict_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"kind": self.kind}
        if self.stain_label is not None:
            data["stainLabel"] = self.stain_label
        if self.normalized is not None:
            data["normalized"] = self.normalized
        if self.stain_protocol_id is not None:
            data["stainProtocolId"] = self.stain_protocol_id
        if self.existing_stain_protocol_id is not None:
            data["existingStainProtocolId"] = self.existing_stain_protocol_id
        if self.requested_stain_protocol_id is not None:
            data["requestedStainProtocolId"] = self.requested_stain_protocol_id
        return data


class StainLabelMappingError(Exception):
    http_status: int = 409

    def __init__(self, message: str, conflict: StainLabelMappingConflict | None = None):
        super().__init__(message)
        self.message = message
        self.conflict = conflict.to_conflict_dict() if conflict else None


class StainLabelMappingConflictError(StainLabelMappingError):
    http_status = 409


class StainLabelMappingValidationError(StainLabelMappingError):
    http_status = 422


def normalize_stain_label(label: str) -> str:
    """Normalize STAINO text (same rules as REGIONO labels)."""
    return normalize_region_label(label)


def prepare_mapping_row(row: dict[str, Any]) -> dict[str, Any]:
    """Ensure normalized key and display label are present."""
    stain_label = (row.get("stainLabel") or "").strip()
    normalized = (row.get("normalized") or "").strip()
    if not normalized and stain_label:
        normalized = normalize_stain_label(stain_label)
    if not stain_label and normalized:
        stain_label = normalized
    if not normalized:
        raise StainLabelMappingValidationError(
            "stainLabel is required",
            StainLabelMappingConflict(kind="invalid_stain_label"),
        )
    prepared = dict(row)
    prepared["stainLabel"] = stain_label
    prepared["normalized"] = normalized
    if "validated" not in prepared:
        prepared["validated"] = True
    if not (prepared.get("sourceField") or "").strip():
        prepared["sourceField"] = "STAINO"
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


def validate_stain_protocol_ids(
    mappings: list[dict[str, Any]],
    valid_protocol_ids: set[str],
) -> list[StainLabelMappingConflict]:
    conflicts: list[StainLabelMappingConflict] = []
    for row in mappings:
        protocol_id = row.get("stainProtocolId")
        if not protocol_id:
            conflicts.append(
                StainLabelMappingConflict(
                    kind="invalid_stain_label",
                    message="stainProtocolId is required",
                    stain_label=row.get("stainLabel"),
                    normalized=row.get("normalized"),
                )
            )
            continue
        if protocol_id not in valid_protocol_ids:
            conflicts.append(
                StainLabelMappingConflict(
                    kind="unknown_stain_protocol",
                    message="stainProtocolId not found in collection stainProtocols",
                    stain_label=row.get("stainLabel"),
                    normalized=row.get("normalized"),
                    stain_protocol_id=protocol_id,
                    requested_stain_protocol_id=protocol_id,
                )
            )
    return conflicts


def validate_payload_internal(
    mappings: list[dict[str, Any]],
    valid_protocol_ids: set[str],
) -> list[StainLabelMappingConflict]:
    conflicts: list[StainLabelMappingConflict] = []
    prepared_rows: list[dict[str, Any]] = []
    for row in mappings:
        try:
            prepared_rows.append(prepare_mapping_row(row))
        except StainLabelMappingValidationError as exc:
            if exc.conflict:
                conflicts.append(
                    StainLabelMappingConflict(
                        kind=exc.conflict["kind"],
                        message=exc.message,
                    )
                )

    conflicts.extend(validate_stain_protocol_ids(prepared_rows, valid_protocol_ids))

    by_normalized: dict[str, dict[str, Any]] = {}
    for row in prepared_rows:
        normalized = row["normalized"]
        protocol_id = row.get("stainProtocolId")
        if normalized in by_normalized:
            existing = by_normalized[normalized]
            if existing.get("stainProtocolId") != protocol_id:
                conflicts.append(
                    StainLabelMappingConflict(
                        kind="duplicate_stain_label",
                        message="Duplicate normalized label with different stainProtocolId in payload",
                        stain_label=row.get("stainLabel"),
                        normalized=normalized,
                        existing_stain_protocol_id=existing.get("stainProtocolId"),
                        requested_stain_protocol_id=protocol_id,
                    )
                )
        by_normalized[normalized] = row

    return conflicts


def validate_merge_against_existing(
    existing_mappings: list[dict[str, Any]],
    proposed_mappings: list[dict[str, Any]],
    valid_protocol_ids: set[str],
) -> list[StainLabelMappingConflict]:
    prepared = [prepare_mapping_row(row) for row in proposed_mappings]
    conflicts = validate_payload_internal(prepared, valid_protocol_ids)
    if conflicts:
        return conflicts

    existing_by_norm = build_mapping_indexes(existing_mappings)
    for row in prepared:
        normalized = row["normalized"]
        protocol_id = row.get("stainProtocolId")
        existing = existing_by_norm.get(normalized)
        if existing is not None and existing.get("stainProtocolId") != protocol_id:
            conflicts.append(
                StainLabelMappingConflict(
                    kind="stain_label_reassigned",
                    message="normalized stain label already mapped",
                    stain_label=row.get("stainLabel"),
                    normalized=normalized,
                    existing_stain_protocol_id=existing.get("stainProtocolId"),
                    requested_stain_protocol_id=protocol_id,
                )
            )
    return conflicts


def raise_on_conflicts(conflicts: list[StainLabelMappingConflict]) -> None:
    if not conflicts:
        return
    first = conflicts[0]
    status = 422 if first.kind == "unknown_stain_protocol" else 409
    exc_cls = (
        StainLabelMappingValidationError
        if status == 422
        else StainLabelMappingConflictError
    )
    raise exc_cls(first.message, first)
