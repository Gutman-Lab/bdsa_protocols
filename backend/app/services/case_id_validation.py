"""Validation helpers for localCaseId <-> bdsaCaseId mappings."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

BDSA_CASE_ID_RE = re.compile(r"^BDSA-(\d{3})-(\d{5})$")
ALTERNATE_ID_SYSTEM_RE = re.compile(r"^[a-z][a-z0-9_]*$")

# Documented alternate ID systems (extensible — any matching key is accepted).
KNOWN_ALTERNATE_ID_SYSTEMS = frozenset({"nacc", "ndd", "mimic", "local_patient"})


@dataclass
class CaseIdMappingConflict:
    """A single mapping constraint violation."""

    kind: str
    message: str
    local_case_id: str | None = None
    bdsa_case_id: str | None = None
    existing_local_case_id: str | None = None
    existing_bdsa_case_id: str | None = None
    requested_local_case_id: str | None = None
    requested_bdsa_case_id: str | None = None
    alternate_id_system: str | None = None
    alternate_id_value: str | None = None

    def to_conflict_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"kind": self.kind}
        if self.local_case_id is not None:
            data["localCaseId"] = self.local_case_id
        if self.bdsa_case_id is not None:
            data["bdsaCaseId"] = self.bdsa_case_id
        if self.existing_local_case_id is not None:
            data["existingLocalCaseId"] = self.existing_local_case_id
        if self.existing_bdsa_case_id is not None:
            data["existingBdsaCaseId"] = self.existing_bdsa_case_id
        if self.requested_local_case_id is not None:
            data["requestedLocalCaseId"] = self.requested_local_case_id
        if self.requested_bdsa_case_id is not None:
            data["requestedBdsaCaseId"] = self.requested_bdsa_case_id
        if self.alternate_id_system is not None:
            data["alternateIdSystem"] = self.alternate_id_system
        if self.alternate_id_value is not None:
            data["alternateIdValue"] = self.alternate_id_value
        return data


class CaseIdMappingError(Exception):
    """Base error for case ID mapping validation."""

    http_status: int = 409

    def __init__(self, message: str, conflict: CaseIdMappingConflict | None = None):
        super().__init__(message)
        self.message = message
        self.conflict = conflict.to_conflict_dict() if conflict else None


class CaseIdMappingConflictError(CaseIdMappingError):
    http_status = 409


class CaseIdMappingValidationError(CaseIdMappingError):
    http_status = 422


def normalize_institution_id(institution_id: str) -> str:
    digits = "".join(ch for ch in institution_id if ch.isdigit())
    if not digits:
        raise CaseIdMappingValidationError(
            "institutionId must contain digits",
            CaseIdMappingConflict(kind="invalid_institution_id"),
        )
    return digits.zfill(3)[-3:]


def parse_bdsa_case_id(bdsa_case_id: str) -> tuple[str, int]:
    match = BDSA_CASE_ID_RE.match(bdsa_case_id or "")
    if not match:
        raise CaseIdMappingValidationError(
            f"Invalid bdsaCaseId format: {bdsa_case_id!r}",
            CaseIdMappingConflict(
                kind="invalid_bdsa_case_id",
                bdsa_case_id=bdsa_case_id,
            ),
        )
    return match.group(1), int(match.group(2))


def validate_bdsa_case_id_for_institution(bdsa_case_id: str, institution_id: str) -> None:
    inst = normalize_institution_id(institution_id)
    parsed_inst, _ = parse_bdsa_case_id(bdsa_case_id)
    if parsed_inst != inst:
        raise CaseIdMappingValidationError(
            "bdsaCaseId institution does not match institutionId",
            CaseIdMappingConflict(
                kind="institution_mismatch",
                bdsa_case_id=bdsa_case_id,
                requested_bdsa_case_id=bdsa_case_id,
            ),
        )


def normalize_alternate_ids(raw: dict[str, Any] | None) -> dict[str, str]:
    """Normalize alternateIds keys to lowercase system names with trimmed values."""
    if not raw:
        return {}
    out: dict[str, str] = {}
    for system, value in raw.items():
        if value is None:
            continue
        key = str(system).strip().lower()
        val = str(value).strip()
        if not key or not val:
            continue
        if not ALTERNATE_ID_SYSTEM_RE.match(key):
            raise CaseIdMappingValidationError(
                f"Invalid alternate ID system name: {system!r}",
                CaseIdMappingConflict(
                    kind="invalid_alternate_id_system",
                    alternate_id_system=key,
                ),
            )
        out[key] = val
    return out


def build_alternate_id_index(
    mappings: list[dict[str, Any]],
) -> dict[tuple[str, str], str]:
    """Map (system, value) -> localCaseId for uniqueness checks."""
    index: dict[tuple[str, str], str] = {}
    for row in mappings:
        local = row.get("localCaseId")
        if not local:
            continue
        for system, value in normalize_alternate_ids(row.get("alternateIds")).items():
            index[(system, value)] = local
    return index


def merge_mapping_rows(
    existing: dict[str, Any] | None,
    proposed: dict[str, Any],
) -> dict[str, Any]:
    """Merge a proposed mapping row into an existing row (by localCaseId)."""
    local = proposed["localCaseId"]
    row: dict[str, Any] = dict(existing) if existing else {"localCaseId": local}
    row["localCaseId"] = local

    if proposed.get("bdsaCaseId"):
        row["bdsaCaseId"] = proposed["bdsaCaseId"]
    elif existing and existing.get("bdsaCaseId"):
        row["bdsaCaseId"] = existing["bdsaCaseId"]

    existing_alt = normalize_alternate_ids(
        existing.get("alternateIds") if existing else None
    )
    proposed_alt = normalize_alternate_ids(proposed.get("alternateIds"))
    if proposed_alt:
        existing_alt.update(proposed_alt)
    if existing_alt:
        row["alternateIds"] = existing_alt
    elif "alternateIds" in row:
        row.pop("alternateIds", None)

    return row


def simulate_case_id_merge(
    existing_mappings: list[dict[str, Any]],
    proposed_mappings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Apply proposed merge rows onto existing mappings (in-memory)."""
    by_local: dict[str, dict[str, Any]] = {}
    for row in existing_mappings:
        local = row.get("localCaseId")
        if not local:
            continue
        by_local[local] = dict(row)

    for proposed in proposed_mappings:
        local = proposed.get("localCaseId")
        if not local:
            continue
        by_local[local] = merge_mapping_rows(by_local.get(local), proposed)

    merged: list[dict[str, Any]] = []
    for local in sorted(by_local):
        row = by_local[local]
        if row.get("bdsaCaseId"):
            merged.append(row)
    return merged


def validate_alternate_ids_unique(
    mappings: list[dict[str, Any]],
) -> list[CaseIdMappingConflict]:
    """Ensure each (system, value) pair maps to at most one localCaseId."""
    conflicts: list[CaseIdMappingConflict] = []
    seen: dict[tuple[str, str], str] = {}
    for row in mappings:
        local = row.get("localCaseId")
        if not local:
            continue
        try:
            alternates = normalize_alternate_ids(row.get("alternateIds"))
        except CaseIdMappingValidationError as exc:
            if exc.conflict:
                conflicts.append(
                    CaseIdMappingConflict(
                        kind=exc.conflict["kind"],
                        message=exc.message,
                        local_case_id=local,
                        alternate_id_system=exc.conflict.get("alternateIdSystem"),
                    )
                )
            continue
        for system, value in alternates.items():
            key = (system, value)
            other_local = seen.get(key)
            if other_local is not None and other_local != local:
                conflicts.append(
                    CaseIdMappingConflict(
                        kind="duplicate_alternate_id",
                        message=f"{system} ID already assigned to another case",
                        local_case_id=local,
                        existing_local_case_id=other_local,
                        alternate_id_system=system,
                        alternate_id_value=value,
                    )
                )
            else:
                seen[key] = local
    return conflicts


def build_mapping_indexes(
    mappings: list[dict[str, Any]],
) -> tuple[dict[str, str], dict[str, str]]:
    by_local: dict[str, str] = {}
    by_bdsa: dict[str, str] = {}
    for row in mappings:
        local = row.get("localCaseId")
        bdsa = row.get("bdsaCaseId")
        if not local or not bdsa:
            continue
        by_local[local] = bdsa
        by_bdsa[bdsa] = local
    return by_local, by_bdsa


def validate_payload_internal(
    mappings: list[dict[str, Any]],
    institution_id: str,
) -> list[CaseIdMappingConflict]:
    """Validate a proposed mapping list in isolation (PUT replace / batch)."""
    conflicts: list[CaseIdMappingConflict] = []
    inst = normalize_institution_id(institution_id)
    by_local: dict[str, str] = {}
    by_bdsa: dict[str, str] = {}

    for row in mappings:
        local = row.get("localCaseId")
        bdsa = row.get("bdsaCaseId")
        if not local or not bdsa:
            conflicts.append(
                CaseIdMappingConflict(
                    kind="invalid_mapping",
                    message="localCaseId and bdsaCaseId are required",
                    local_case_id=local,
                    bdsa_case_id=bdsa,
                )
            )
            continue
        try:
            validate_bdsa_case_id_for_institution(bdsa, inst)
        except CaseIdMappingValidationError as exc:
            if exc.conflict:
                conflicts.append(
                    CaseIdMappingConflict(
                        kind=exc.conflict["kind"],
                        message=exc.message,
                        local_case_id=local,
                        bdsa_case_id=bdsa,
                        requested_local_case_id=local,
                        requested_bdsa_case_id=bdsa,
                    )
                )
            continue

        if local in by_local and by_local[local] != bdsa:
            conflicts.append(
                CaseIdMappingConflict(
                    kind="local_case_reassigned",
                    message="Duplicate localCaseId with different bdsaCaseId in payload",
                    local_case_id=local,
                    existing_bdsa_case_id=by_local[local],
                    requested_bdsa_case_id=bdsa,
                )
            )
        if bdsa in by_bdsa and by_bdsa[bdsa] != local:
            conflicts.append(
                CaseIdMappingConflict(
                    kind="duplicate_bdsa_case_id",
                    message="Duplicate bdsaCaseId for different localCaseId in payload",
                    bdsa_case_id=bdsa,
                    existing_local_case_id=by_bdsa[bdsa],
                    requested_local_case_id=local,
                )
            )
        by_local[local] = bdsa
        by_bdsa[bdsa] = local

    conflicts.extend(validate_alternate_ids_unique(mappings))
    return conflicts


def validate_merge_proposals(
    existing_mappings: list[dict[str, Any]],
    proposed_mappings: list[dict[str, Any]],
) -> list[CaseIdMappingConflict]:
    """Validate merge rows before applying (including alternate-only updates)."""
    conflicts: list[CaseIdMappingConflict] = []
    existing_locals = {
        row.get("localCaseId")
        for row in existing_mappings
        if row.get("localCaseId")
    }

    for row in proposed_mappings:
        local = row.get("localCaseId")
        if not local:
            conflicts.append(
                CaseIdMappingConflict(
                    kind="invalid_mapping",
                    message="localCaseId is required",
                )
            )
            continue
        has_bdsa = bool(row.get("bdsaCaseId"))
        has_alternates = bool(row.get("alternateIds"))
        if not has_bdsa and not has_alternates:
            conflicts.append(
                CaseIdMappingConflict(
                    kind="invalid_mapping",
                    message="Merge row must include bdsaCaseId and/or alternateIds",
                    local_case_id=local,
                )
            )
            continue
        if not has_bdsa and local not in existing_locals:
            conflicts.append(
                CaseIdMappingConflict(
                    kind="unknown_local_case",
                    message="Cannot set alternateIds for unknown localCaseId without bdsaCaseId",
                    local_case_id=local,
                )
            )

    return conflicts


def validate_merge_against_existing(
    existing_mappings: list[dict[str, Any]],
    proposed_mappings: list[dict[str, Any]],
    institution_id: str,
) -> list[CaseIdMappingConflict]:
    """Validate merge proposals against stored mappings and within the batch."""
    conflicts = validate_merge_proposals(existing_mappings, proposed_mappings)
    if conflicts:
        return conflicts

    rows_with_bdsa = [r for r in proposed_mappings if r.get("bdsaCaseId")]
    if rows_with_bdsa:
        conflicts = validate_payload_internal(rows_with_bdsa, institution_id)
        if conflicts:
            return conflicts

    existing_by_local, existing_by_bdsa = build_mapping_indexes(existing_mappings)
    batch_by_local, batch_by_bdsa = build_mapping_indexes(
        [r for r in proposed_mappings if r.get("bdsaCaseId")]
    )

    for local, bdsa in batch_by_local.items():
        existing_bdsa = existing_by_local.get(local)
        if existing_bdsa is not None and existing_bdsa != bdsa:
            conflicts.append(
                CaseIdMappingConflict(
                    kind="local_case_reassigned",
                    message="localCaseId already mapped",
                    local_case_id=local,
                    existing_bdsa_case_id=existing_bdsa,
                    requested_bdsa_case_id=bdsa,
                )
            )

        other_local = existing_by_bdsa.get(bdsa)
        if other_local is not None and other_local != local:
            conflicts.append(
                CaseIdMappingConflict(
                    kind="duplicate_bdsa_case_id",
                    message="bdsaCaseId already assigned",
                    bdsa_case_id=bdsa,
                    existing_local_case_id=other_local,
                    requested_local_case_id=local,
                )
            )

    merged = simulate_case_id_merge(existing_mappings, proposed_mappings)
    conflicts.extend(validate_alternate_ids_unique(merged))
    return conflicts


def used_sequences_for_institution(
    mappings: list[dict[str, Any]],
    institution_id: str,
) -> set[int]:
    inst = normalize_institution_id(institution_id)
    used: set[int] = set()
    for row in mappings:
        bdsa = row.get("bdsaCaseId")
        if not bdsa:
            continue
        try:
            parsed_inst, seq = parse_bdsa_case_id(bdsa)
        except CaseIdMappingValidationError:
            continue
        if parsed_inst == inst:
            used.add(seq)
    return used


def lowest_unused_sequence(used: set[int]) -> int:
    seq = 1
    while seq in used:
        seq += 1
    return seq


def format_bdsa_case_id(institution_id: str, sequence: int) -> str:
    inst = normalize_institution_id(institution_id)
    return f"BDSA-{inst}-{sequence:05d}"


def raise_on_conflicts(conflicts: list[CaseIdMappingConflict]) -> None:
    if not conflicts:
        return
    first = conflicts[0]
    raise CaseIdMappingConflictError(first.message, first)
