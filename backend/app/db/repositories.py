"""MongoDB repositories for protocols, case mappings, and slides."""
from datetime import datetime, timezone
from typing import Any

from app.db.mongodb import get_db


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def get_protocols(collection_id: str) -> dict[str, Any] | None:
    """Get protocols for a collection. Returns None if not found."""
    db = await get_db()
    doc = await db.protocols.find_one({"collection_id": collection_id})
    if doc is None:
        return None
    doc.pop("_id", None)
    doc.pop("collection_id", None)
    return doc


async def set_protocols(collection_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Set (replace) protocols for a collection. Returns stored document."""
    db = await get_db()
    payload["lastUpdated"] = _now_iso()
    doc = {"collection_id": collection_id, **payload}
    await db.protocols.update_one(
        {"collection_id": collection_id},
        {"$set": doc},
        upsert=True,
    )
    return await get_protocols(collection_id) or doc


async def merge_protocols(
    collection_id: str,
    stain_protocols: list[dict],
    region_protocols: list[dict],
    block_protocols: list[dict] | None = None,
) -> dict[str, Any]:
    """Merge new protocols with existing (by id). Returns merged payload."""
    existing = await get_protocols(collection_id)
    stain = list(existing.get("stainProtocols", [])) if existing else []
    region = list(existing.get("regionProtocols", [])) if existing else []
    block = list(existing.get("blockProtocols", [])) if existing else []
    existing_stain_ids = {p.get("id") for p in stain if p.get("id")}
    existing_region_ids = {p.get("id") for p in region if p.get("id")}
    existing_block_ids = {p.get("id") for p in block if p.get("id")}
    for p in stain_protocols or []:
        if p.get("id") and p["id"] not in existing_stain_ids:
            stain.append(p)
            existing_stain_ids.add(p["id"])
    for p in region_protocols or []:
        if p.get("id") and p["id"] not in existing_region_ids:
            region.append(p)
            existing_region_ids.add(p["id"])
    for p in block_protocols or []:
        if p.get("id") and p["id"] not in existing_block_ids:
            block.append(p)
            existing_block_ids.add(p["id"])
    payload = {
        "stainProtocols": stain,
        "regionProtocols": region,
        "blockProtocols": block,
        "source": "BDSA-Schema-Wrangler",
        "version": "1.0",
    }
    return await set_protocols(collection_id, payload)


async def get_case_id_mappings(collection_id: str) -> dict[str, Any] | None:
    """Get case ID mappings for a collection. Returns None if not found."""
    db = await get_db()
    doc = await db.case_id_mappings.find_one({"collection_id": collection_id})
    if doc is None:
        return None
    doc.pop("_id", None)
    doc.pop("collection_id", None)
    return doc


async def set_case_id_mappings(
    collection_id: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Set (replace) case ID mappings for a collection."""
    db = await get_db()
    payload["lastUpdated"] = _now_iso()
    if "mappings" in payload:
        payload["totalMappings"] = len(payload["mappings"])
    doc = {"collection_id": collection_id, **payload}
    await db.case_id_mappings.update_one(
        {"collection_id": collection_id},
        {"$set": doc},
        upsert=True,
    )
    for m in payload.get("mappings", []):
        local = m.get("localCaseId")
        if local is not None:
            await register_case_in_collection(collection_id, local)
    return await get_case_id_mappings(collection_id) or doc


async def merge_case_id_mappings(
    collection_id: str,
    mappings: list[dict],
    institution_id: str = "001",
    *,
    source: str = "BDSA-Schema-Wrangler",
    version: str = "1.0",
    skip_validation: bool = False,
) -> dict[str, Any]:
    """Merge new mappings with existing (by localCaseId). Returns merged payload."""
    from app.services.case_id_validation import (
        build_mapping_indexes,
        raise_on_conflicts,
        validate_merge_against_existing,
        validate_payload_internal,
    )

    existing = await get_case_id_mappings(collection_id)
    existing_list = list(existing.get("mappings", [])) if existing else []
    proposed = [m for m in (mappings or []) if m.get("localCaseId")]

    if not skip_validation:
        conflicts = validate_merge_against_existing(
            existing_list, proposed, institution_id
        )
        raise_on_conflicts(conflicts)

    from app.services.case_id_validation import simulate_case_id_merge

    merged = simulate_case_id_merge(existing_list, proposed)
    payload = {
        "institutionId": institution_id,
        "mappings": merged,
        "totalMappings": len(merged),
        "source": source,
        "version": version,
    }
    return await set_case_id_mappings(collection_id, payload)


async def replace_case_id_mappings_validated(
    collection_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Replace case ID mappings after validating the full payload."""
    from app.services.case_id_validation import (
        raise_on_conflicts,
        validate_payload_internal,
    )

    institution_id = payload.get("institutionId", "001")
    mappings = list(payload.get("mappings", []))
    conflicts = validate_payload_internal(mappings, institution_id)
    raise_on_conflicts(conflicts)
    return await set_case_id_mappings(collection_id, payload)


async def validate_case_id_mappings_merge(
    collection_id: str,
    mappings: list[dict],
    institution_id: str = "001",
) -> list[dict[str, Any]]:
    """Dry-run merge validation; returns conflict dicts without writing."""
    from app.services.case_id_validation import validate_merge_against_existing

    existing = await get_case_id_mappings(collection_id)
    existing_list = list(existing.get("mappings", [])) if existing else []
    proposed = [m for m in (mappings or []) if m.get("localCaseId")]
    conflicts = validate_merge_against_existing(
        existing_list, proposed, institution_id
    )
    return [c.to_conflict_dict() for c in conflicts]


def _find_case_mapping_row(
    mappings: list[dict],
    *,
    local_case_id: str | None = None,
    bdsa_case_id: str | None = None,
) -> dict | None:
    for row in mappings:
        if local_case_id is not None and row.get("localCaseId") == local_case_id:
            return dict(row)
        if bdsa_case_id is not None and row.get("bdsaCaseId") == bdsa_case_id:
            return dict(row)
    return None


async def get_case_id_mapping_by_bdsa(
    collection_id: str,
    bdsa_case_id: str,
) -> dict[str, str] | None:
    """Look up a single mapping by bdsaCaseId."""
    data = await get_case_id_mappings(collection_id)
    if not data:
        return None
    return _find_case_mapping_row(data.get("mappings", []), bdsa_case_id=bdsa_case_id)


async def get_case_id_mapping_by_local(
    collection_id: str,
    local_case_id: str,
) -> dict[str, str] | None:
    """Look up a single mapping by localCaseId."""
    data = await get_case_id_mappings(collection_id)
    if not data:
        return None
    return _find_case_mapping_row(data.get("mappings", []), local_case_id=local_case_id)


async def get_case_id_mapping_by_alternate(
    collection_id: str,
    system: str,
    value: str,
) -> dict[str, str] | None:
    """Look up a single mapping by alternate ID system + value (e.g. nacc)."""
    from app.services.case_id_validation import (
        CaseIdMappingValidationError,
        normalize_alternate_ids,
    )

    data = await get_case_id_mappings(collection_id)
    if not data:
        return None
    try:
        target_system, target_value = next(
            iter(normalize_alternate_ids({system: value}).items())
        )
    except (CaseIdMappingValidationError, StopIteration):
        return None
    for row in data.get("mappings", []):
        alternates = normalize_alternate_ids(row.get("alternateIds"))
        if alternates.get(target_system) == target_value:
            return dict(row)
    return None


async def allocate_case_id_mapping(
    collection_id: str,
    local_case_id: str,
    institution_id: str = "001",
    *,
    source: str = "BDSA-Schema-Wrangler",
    max_attempts: int = 8,
) -> tuple[dict[str, str], bool]:
    """Allocate or return an existing localCaseId -> bdsaCaseId mapping."""
    from app.services.case_id_validation import (
        format_bdsa_case_id,
        lowest_unused_sequence,
        used_sequences_for_institution,
        validate_bdsa_case_id_for_institution,
    )

    for _ in range(max_attempts):
        existing = await get_case_id_mappings(collection_id)
        mappings = list(existing.get("mappings", [])) if existing else []
        for row in mappings:
            if row.get("localCaseId") == local_case_id:
                bdsa = row.get("bdsaCaseId")
                if bdsa:
                    return dict(row), False

        used = used_sequences_for_institution(mappings, institution_id)
        seq = lowest_unused_sequence(used)
        bdsa_case_id = format_bdsa_case_id(institution_id, seq)
        validate_bdsa_case_id_for_institution(bdsa_case_id, institution_id)

        try:
            await merge_case_id_mappings(
                collection_id,
                [{"localCaseId": local_case_id, "bdsaCaseId": bdsa_case_id}],
                institution_id,
                source=source,
            )
            created = _find_case_mapping_row(
                (await get_case_id_mappings(collection_id) or {}).get("mappings", []),
                local_case_id=local_case_id,
            )
            if created:
                return created, True
            return {"localCaseId": local_case_id, "bdsaCaseId": bdsa_case_id}, True
        except Exception:
            fresh = await get_case_id_mappings(collection_id)
            fresh_mappings = list(fresh.get("mappings", [])) if fresh else []
            found = _find_case_mapping_row(fresh_mappings, local_case_id=local_case_id)
            if found and found.get("bdsaCaseId"):
                return found, False
            continue

    raise RuntimeError(
        f"Failed to allocate bdsaCaseId for {local_case_id} after {max_attempts} attempts"
    )


async def allocate_case_id_mappings_batch(
    collection_id: str,
    local_case_ids: list[str],
    institution_id: str = "001",
    *,
    source: str = "BDSA-Schema-Wrangler",
) -> list[dict[str, Any]]:
    """Allocate mappings for multiple local case IDs (all-or-nothing)."""
    from app.services.case_id_validation import (
        CaseIdMappingConflict,
        CaseIdMappingConflictError,
        build_mapping_indexes,
        format_bdsa_case_id,
        lowest_unused_sequence,
        used_sequences_for_institution,
        validate_bdsa_case_id_for_institution,
    )

    unique_locals = list(dict.fromkeys(local_case_ids))
    existing = await get_case_id_mappings(collection_id)
    mappings = list(existing.get("mappings", [])) if existing else []
    by_local, by_bdsa = build_mapping_indexes(mappings)

    results: list[dict[str, Any]] = []
    new_rows: list[dict[str, str]] = []
    used = used_sequences_for_institution(mappings, institution_id)

    for local in unique_locals:
        existing_bdsa = by_local.get(local)
        if existing_bdsa:
            results.append(
                {
                    "localCaseId": local,
                    "bdsaCaseId": existing_bdsa,
                    "allocated": False,
                }
            )
            continue

        seq = lowest_unused_sequence(used)
        used.add(seq)
        bdsa = format_bdsa_case_id(institution_id, seq)
        validate_bdsa_case_id_for_institution(bdsa, institution_id)

        if bdsa in by_bdsa and by_bdsa[bdsa] != local:
            conflict = CaseIdMappingConflict(
                kind="duplicate_bdsa_case_id",
                message="bdsaCaseId already assigned",
                bdsa_case_id=bdsa,
                existing_local_case_id=by_bdsa[bdsa],
                requested_local_case_id=local,
            )
            raise CaseIdMappingConflictError(conflict.message, conflict)

        new_rows.append({"localCaseId": local, "bdsaCaseId": bdsa})
        by_local[local] = bdsa
        by_bdsa[bdsa] = local
        results.append(
            {"localCaseId": local, "bdsaCaseId": bdsa, "allocated": True}
        )

    if new_rows:
        await merge_case_id_mappings(
            collection_id,
            new_rows,
            institution_id,
            source=source,
        )

    return results


async def _region_protocol_ids(collection_id: str) -> set[str]:
    protocols = await get_protocols(collection_id)
    if not protocols:
        return set()
    return {
        p.get("id")
        for p in protocols.get("regionProtocols", [])
        if p.get("id")
    }


async def get_region_label_mappings(collection_id: str) -> dict[str, Any] | None:
    """Get REGIONO label mappings for a collection."""
    db = await get_db()
    doc = await db.region_label_mappings.find_one({"collection_id": collection_id})
    if doc is None:
        return None
    doc.pop("_id", None)
    doc.pop("collection_id", None)
    return doc


async def set_region_label_mappings(
    collection_id: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Set (replace) region label mappings for a collection."""
    db = await get_db()
    payload["lastUpdated"] = _now_iso()
    if "mappings" in payload:
        payload["totalMappings"] = len(payload["mappings"])
    doc = {"collection_id": collection_id, **payload}
    await db.region_label_mappings.update_one(
        {"collection_id": collection_id},
        {"$set": doc},
        upsert=True,
    )
    return await get_region_label_mappings(collection_id) or doc


async def merge_region_label_mappings(
    collection_id: str,
    mappings: list[dict],
    *,
    source: str = "BDSA-Schema-Wrangler",
    version: str = "1.0",
) -> dict[str, Any]:
    """Merge region label mappings with existing (by normalized)."""
    from app.services.region_label_validation import (
        build_mapping_indexes,
        prepare_mapping_row,
        raise_on_conflicts,
        validate_merge_against_existing,
    )

    valid_ids = await _region_protocol_ids(collection_id)
    existing = await get_region_label_mappings(collection_id)
    existing_list = list(existing.get("mappings", [])) if existing else []
    proposed = [prepare_mapping_row(m) for m in (mappings or []) if m.get("regionLabel") or m.get("normalized")]

    conflicts = validate_merge_against_existing(
        existing_list, proposed, valid_ids
    )
    raise_on_conflicts(conflicts)

    existing_by_norm = build_mapping_indexes(existing_list)
    merged_by_norm = dict(existing_by_norm)
    for row in proposed:
        if not row.get("source"):
            row["source"] = source
        merged_by_norm[row["normalized"]] = row

    merged = sorted(
        merged_by_norm.values(),
        key=lambda r: r.get("normalized") or "",
    )
    payload = {
        "mappings": merged,
        "totalMappings": len(merged),
        "source": source,
        "version": version,
    }
    return await set_region_label_mappings(collection_id, payload)


async def replace_region_label_mappings_validated(
    collection_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Replace region label mappings after validating the full payload."""
    from app.services.region_label_validation import (
        prepare_mapping_row,
        raise_on_conflicts,
        validate_payload_internal,
    )

    valid_ids = await _region_protocol_ids(collection_id)
    mappings = [
        prepare_mapping_row(m)
        for m in payload.get("mappings", [])
        if m.get("regionLabel") or m.get("normalized")
    ]
    conflicts = validate_payload_internal(mappings, valid_ids)
    raise_on_conflicts(conflicts)
    payload = dict(payload)
    payload["mappings"] = sorted(
        mappings,
        key=lambda r: r.get("normalized") or "",
    )
    return await set_region_label_mappings(collection_id, payload)


async def validate_region_label_mappings_merge(
    collection_id: str,
    mappings: list[dict],
) -> list[dict[str, Any]]:
    """Dry-run merge validation; returns conflict dicts without writing."""
    from app.services.region_label_validation import (
        prepare_mapping_row,
        validate_merge_against_existing,
    )

    valid_ids = await _region_protocol_ids(collection_id)
    existing = await get_region_label_mappings(collection_id)
    existing_list = list(existing.get("mappings", [])) if existing else []
    proposed = [
        prepare_mapping_row(m)
        for m in (mappings or [])
        if m.get("regionLabel") or m.get("normalized")
    ]
    conflicts = validate_merge_against_existing(
        existing_list, proposed, valid_ids
    )
    return [c.to_conflict_dict() for c in conflicts]


async def get_region_label_mapping_by_normalized(
    collection_id: str,
    normalized: str,
    *,
    validated_only: bool = True,
) -> dict[str, Any] | None:
    """Look up a mapping by normalized label (validated rows only by default)."""
    from app.services.region_label_validation import (
        build_mapping_indexes,
        normalize_region_label,
    )

    key = normalize_region_label(normalized)
    if not key:
        return None
    data = await get_region_label_mappings(collection_id)
    if not data:
        return None
    by_norm = build_mapping_indexes(data.get("mappings", []))
    row = by_norm.get(key)
    if row is None:
        return None
    if validated_only and not row.get("validated", True):
        return None
    return row


async def _stain_protocol_ids(collection_id: str) -> set[str]:
    protocols = await get_protocols(collection_id)
    if not protocols:
        return set()
    return {
        p.get("id")
        for p in protocols.get("stainProtocols", [])
        if p.get("id")
    }


async def get_stain_label_mappings(collection_id: str) -> dict[str, Any] | None:
    """Get STAINO label mappings for a collection."""
    db = await get_db()
    doc = await db.stain_label_mappings.find_one({"collection_id": collection_id})
    if doc is None:
        return None
    doc.pop("_id", None)
    doc.pop("collection_id", None)
    return doc


async def set_stain_label_mappings(
    collection_id: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Set (replace) stain label mappings for a collection."""
    db = await get_db()
    payload["lastUpdated"] = _now_iso()
    if "mappings" in payload:
        payload["totalMappings"] = len(payload["mappings"])
    doc = {"collection_id": collection_id, **payload}
    await db.stain_label_mappings.update_one(
        {"collection_id": collection_id},
        {"$set": doc},
        upsert=True,
    )
    return await get_stain_label_mappings(collection_id) or doc


async def merge_stain_label_mappings(
    collection_id: str,
    mappings: list[dict],
    *,
    source: str = "BDSA-Schema-Wrangler",
    version: str = "1.0",
) -> dict[str, Any]:
    """Merge stain label mappings with existing (by normalized)."""
    from app.services.stain_label_validation import (
        build_mapping_indexes,
        prepare_mapping_row,
        raise_on_conflicts,
        validate_merge_against_existing,
    )

    valid_ids = await _stain_protocol_ids(collection_id)
    existing = await get_stain_label_mappings(collection_id)
    existing_list = list(existing.get("mappings", [])) if existing else []
    proposed = [
        prepare_mapping_row(m)
        for m in (mappings or [])
        if m.get("stainLabel") or m.get("normalized")
    ]

    conflicts = validate_merge_against_existing(
        existing_list, proposed, valid_ids
    )
    raise_on_conflicts(conflicts)

    existing_by_norm = build_mapping_indexes(existing_list)
    merged_by_norm = dict(existing_by_norm)
    for row in proposed:
        if not row.get("source"):
            row["source"] = source
        merged_by_norm[row["normalized"]] = row

    merged = sorted(
        merged_by_norm.values(),
        key=lambda r: r.get("normalized") or "",
    )
    payload = {
        "mappings": merged,
        "totalMappings": len(merged),
        "source": source,
        "version": version,
    }
    return await set_stain_label_mappings(collection_id, payload)


async def replace_stain_label_mappings_validated(
    collection_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Replace stain label mappings after validating the full payload."""
    from app.services.stain_label_validation import (
        prepare_mapping_row,
        raise_on_conflicts,
        validate_payload_internal,
    )

    valid_ids = await _stain_protocol_ids(collection_id)
    mappings = [
        prepare_mapping_row(m)
        for m in payload.get("mappings", [])
        if m.get("stainLabel") or m.get("normalized")
    ]
    conflicts = validate_payload_internal(mappings, valid_ids)
    raise_on_conflicts(conflicts)
    payload = dict(payload)
    payload["mappings"] = sorted(
        mappings,
        key=lambda r: r.get("normalized") or "",
    )
    return await set_stain_label_mappings(collection_id, payload)


async def validate_stain_label_mappings_merge(
    collection_id: str,
    mappings: list[dict],
) -> list[dict[str, Any]]:
    """Dry-run merge validation; returns conflict dicts without writing."""
    from app.services.stain_label_validation import (
        prepare_mapping_row,
        validate_merge_against_existing,
    )

    valid_ids = await _stain_protocol_ids(collection_id)
    existing = await get_stain_label_mappings(collection_id)
    existing_list = list(existing.get("mappings", [])) if existing else []
    proposed = [
        prepare_mapping_row(m)
        for m in (mappings or [])
        if m.get("stainLabel") or m.get("normalized")
    ]
    conflicts = validate_merge_against_existing(
        existing_list, proposed, valid_ids
    )
    return [c.to_conflict_dict() for c in conflicts]


async def get_stain_label_mapping_by_normalized(
    collection_id: str,
    normalized: str,
    *,
    validated_only: bool = True,
) -> dict[str, Any] | None:
    """Look up a mapping by normalized label (validated rows only by default)."""
    from app.services.stain_label_validation import (
        build_mapping_indexes,
        normalize_stain_label,
    )

    key = normalize_stain_label(normalized)
    if not key:
        return None
    data = await get_stain_label_mappings(collection_id)
    if not data:
        return None
    by_norm = build_mapping_indexes(data.get("mappings", []))
    row = by_norm.get(key)
    if row is None:
        return None
    if validated_only and not row.get("validated", True):
        return None
    return row


async def get_slides(collection_id: str) -> dict[str, Any] | None:
    """Get slides payload for a collection. Returns None if not found."""
    db = await get_db()
    doc = await db.slides.find_one({"collection_id": collection_id})
    if doc is None:
        return None
    doc.pop("_id", None)
    doc.pop("collection_id", None)
    return doc


async def set_slides(collection_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Set (replace) slides for a collection."""
    db = await get_db()
    payload["lastUpdated"] = _now_iso()
    doc = {"collection_id": collection_id, **payload}
    await db.slides.update_one(
        {"collection_id": collection_id},
        {"$set": doc},
        upsert=True,
    )
    return await get_slides(collection_id) or doc


async def get_patient_id_mappings(collection_id: str) -> dict[str, Any] | None:
    """Get patient ID mappings (localPatientId -> bdsaPatientId?) for a collection."""
    db = await get_db()
    doc = await db.patient_id_mappings.find_one({"collection_id": collection_id})
    if doc is None:
        return None
    doc.pop("_id", None)
    doc.pop("collection_id", None)
    return doc


async def set_patient_id_mappings(
    collection_id: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Set (replace) patient ID mappings for a collection."""
    db = await get_db()
    payload["lastUpdated"] = _now_iso()
    if "mappings" in payload:
        payload["totalMappings"] = len(payload["mappings"])
    doc = {"collection_id": collection_id, **payload}
    await db.patient_id_mappings.update_one(
        {"collection_id": collection_id},
        {"$set": doc},
        upsert=True,
    )
    return await get_patient_id_mappings(collection_id) or doc


async def merge_patient_id_mappings(
    collection_id: str,
    mappings: list[dict],
    institution_id: str = "001",
) -> dict[str, Any]:
    """Merge new patient mappings with existing (by localPatientId)."""
    existing = await get_patient_id_mappings(collection_id)
    existing_list = list(existing.get("mappings", [])) if existing else []
    by_local: dict[str, str | None] = {
        m["localPatientId"]: m.get("bdsaPatientId") for m in existing_list
    }
    for m in mappings or []:
        local = m.get("localPatientId")
        if local is not None:
            by_local[local] = m.get("bdsaPatientId")
    merged = [
        {"localPatientId": k, "bdsaPatientId": v} for k, v in by_local.items()
    ]
    payload = {
        "institutionId": institution_id,
        "mappings": merged,
        "totalMappings": len(merged),
        "source": "BDSA-Schema-Wrangler",
        "version": "1.0",
    }
    return await set_patient_id_mappings(collection_id, payload)


async def get_block2region(
    collection_id: str, case_id: str
) -> dict[str, Any] | None:
    """Get block2region map for a case. Returns None if not found.
    Includes block2region, mapping_source, validated, lastUpdated, source, version.
    """
    db = await get_db()
    doc = await db.block2region.find_one(
        {"collection_id": collection_id, "case_id": case_id}
    )
    if doc is None:
        return None
    doc.pop("_id", None)
    doc.pop("collection_id", None)
    doc.pop("case_id", None)
    return doc


async def ensure_case_in_mappings(
    collection_id: str,
    local_case_id: str,
    bdsa_case_id: str | None = None,
    institution_id: str = "001",
) -> None:
    """Ensure this case exists in case_id_mappings for the collection.
    If already present, keeps existing bdsaCaseId unless a non-null bdsa_case_id is given.
    """
    existing = await get_case_id_mappings(collection_id)
    existing_list = list(existing.get("mappings", [])) if existing else []
    by_local: dict[str, str | None] = {
        m["localCaseId"]: m.get("bdsaCaseId") for m in existing_list
    }
    current = by_local.get(local_case_id)
    if local_case_id not in by_local:
        by_local[local_case_id] = bdsa_case_id
    elif bdsa_case_id is not None and current != bdsa_case_id:
        pass
    else:
        by_local[local_case_id] = current
    merged = [{"localCaseId": k, "bdsaCaseId": v} for k, v in by_local.items()]
    payload = {
        "institutionId": institution_id,
        "mappings": merged,
        "totalMappings": len(merged),
        "source": "BDSA-Schema-Wrangler",
        "version": "1.0",
    }
    await set_case_id_mappings(collection_id, payload)


async def register_case_in_collection(collection_id: str, case_id: str) -> None:
    """Record that this case is associated with this collection (for future lookups)."""
    db = await get_db()
    await db.case_collection_registry.update_one(
        {"collection_id": collection_id, "case_id": case_id},
        {"$set": {"collection_id": collection_id, "case_id": case_id}},
        upsert=True,
    )


async def get_collections_for_case(case_id: str) -> list[str]:
    """Return collection_ids that this case is associated with."""
    db = await get_db()
    cursor = db.case_collection_registry.find({"case_id": case_id}, {"collection_id": 1})
    return sorted({doc["collection_id"] async for doc in cursor})


async def get_cases_for_collection(collection_id: str) -> list[str]:
    """Return case_ids associated with this collection."""
    db = await get_db()
    cursor = db.case_collection_registry.find(
        {"collection_id": collection_id}, {"case_id": 1}
    )
    return sorted({doc["case_id"] async for doc in cursor})


async def _next_block2region_version(
    collection_id: str, case_id: str
) -> int:
    """Return the next version number for this (collection_id, case_id)."""
    db = await get_db()
    doc = await db.block2region_versions.find_one(
        {"collection_id": collection_id, "case_id": case_id},
        sort=[("version", -1)],
        projection={"version": 1},
    )
    return (doc["version"] + 1) if doc else 1


async def set_block2region(
    collection_id: str,
    case_id: str,
    block2region: dict[str, str],
    mapping_source: str | None = None,
    validated: bool = False,
    case_status: str | None = None,
) -> dict[str, Any]:
    """Set (replace) block2region map for a case.
    Values in block2region can be a region id or status (SKIP etc.).
    case_status is case-level: SKIP / NEEDS_RESEARCH / NOT_SCANNED.
    Saves a versioned snapshot before updating. Also ensures the case is in
    case_id_mappings and in case_collection_registry.
    """
    db = await get_db()
    now = _now_iso()
    version = await _next_block2region_version(collection_id, case_id)
    await db.block2region_versions.insert_one({
        "collection_id": collection_id,
        "case_id": case_id,
        "version": version,
        "block2region": block2region,
        "mapping_source": mapping_source,
        "validated": validated,
        "case_status": case_status,
        "createdAt": now,
    })
    doc = {
        "collection_id": collection_id,
        "case_id": case_id,
        "block2region": block2region,
        "mapping_source": mapping_source,
        "validated": validated,
        "case_status": case_status,
        "lastUpdated": now,
        "source": "BDSA-Schema-Wrangler",
        "version": "1.0",
    }
    await db.block2region.update_one(
        {"collection_id": collection_id, "case_id": case_id},
        {"$set": doc},
        upsert=True,
    )
    await ensure_case_in_mappings(collection_id, case_id, bdsa_case_id=None)
    await register_case_in_collection(collection_id, case_id)
    return await get_block2region(collection_id, case_id) or doc


async def get_block2region_versions(
    collection_id: str, case_id: str
) -> list[dict[str, Any]]:
    """List versioned snapshots for this case (newest first)."""
    db = await get_db()
    cursor = db.block2region_versions.find(
        {"collection_id": collection_id, "case_id": case_id}
    ).sort("version", -1)
    out: list[dict[str, Any]] = []
    async for d in cursor:
        d.pop("_id", None)
        d.pop("collection_id", None)
        d.pop("case_id", None)
        out.append(d)
    return out


async def get_block2region_by_version(
    collection_id: str, case_id: str, version: int
) -> dict[str, Any] | None:
    """Get a single version snapshot."""
    db = await get_db()
    doc = await db.block2region_versions.find_one(
        {"collection_id": collection_id, "case_id": case_id, "version": version}
    )
    if doc is None:
        return None
    doc.pop("_id", None)
    doc.pop("collection_id", None)
    doc.pop("case_id", None)
    return doc


async def restore_block2region_from_version(
    collection_id: str, case_id: str, version: int
) -> dict[str, Any] | None:
    """Set current block2region to the given version (creates a new version entry)."""
    snap = await get_block2region_by_version(collection_id, case_id, version)
    if snap is None:
        return None
    return await set_block2region(
        collection_id,
        case_id,
        snap.get("block2region", {}),
        mapping_source=snap.get("mapping_source"),
        validated=snap.get("validated", False),
        case_status=snap.get("case_status"),
    )


async def get_block2region_stats(
    collection_id: str,
) -> dict[str, Any]:
    """Return counts for this collection's block2region (no full payload)."""
    db = await get_db()
    cursor = db.block2region.find(
        {"collection_id": collection_id},
        {"case_id": 1, "block2region": 1, "validated": 1},
    )
    cases_with_maps = 0
    total_pairs = 0
    validated_count = 0
    case_ids: list[str] = []
    async for doc in cursor:
        cases_with_maps += 1
        case_ids.append(doc["case_id"])
        m = doc.get("block2region") or {}
        total_pairs += len(m)
        if doc.get("validated"):
            validated_count += 1
    return {
        "casesWithMaps": cases_with_maps,
        "totalPairs": total_pairs,
        "validatedCount": validated_count,
        "caseIds": case_ids,
    }


async def get_all_block2region_for_collection(
    collection_id: str,
) -> dict[str, dict[str, Any]]:
    """Get block2region for all cases. Returns { case_id: { block2region, mapping_source?, validated?, lastUpdated? } }."""
    db = await get_db()
    result: dict[str, dict[str, Any]] = {}
    cursor = db.block2region.find({"collection_id": collection_id})
    async for doc in cursor:
        cid = doc["case_id"]
        result[cid] = {
            "block2region": doc.get("block2region", {}),
            "mapping_source": doc.get("mapping_source"),
            "validated": doc.get("validated", False),
            "case_status": doc.get("case_status"),
            "lastUpdated": doc.get("lastUpdated"),
        }
    return result


async def replace_dsa_items_for_collection(
    collection_id: str, items: list[dict[str, Any]]
) -> dict[str, Any]:
    """Replace all DSA items for a collection. Each item must have case_fld_id (and girder _id)."""
    db = await get_db()
    await db.dsa_items.delete_many({"collection_id": collection_id})
    docs = []
    for item in items:
        doc = {k: v for k, v in item.items() if k != "_id"}
        doc["collection_id"] = collection_id
        doc["case_fld_id"] = item.get("case_fld_id")
        doc["girder_id"] = item.get("_id")
        docs.append(doc)
    if docs:
        await db.dsa_items.insert_many(docs)
    return {"collection_id": collection_id, "count": len(docs)}


async def get_dsa_items_for_collection(
    collection_id: str, case_fld_id: str | None = None
) -> list[dict[str, Any]]:
    """Get stored DSA items for a collection, optionally filtered by case_fld_id."""
    db = await get_db()
    q: dict[str, Any] = {"collection_id": collection_id}
    if case_fld_id is not None:
        q["case_fld_id"] = case_fld_id
    cursor = db.dsa_items.find(q)
    out = []
    async for doc in cursor:
        doc.pop("_id", None)
        doc.pop("collection_id", None)
        out.append(doc)
    return out


async def get_dsa_items_stats(collection_id: str) -> dict[str, Any]:
    """Return total item count and list of case_fld_ids (patient folders) for a collection."""
    db = await get_db()
    total = await db.dsa_items.count_documents({"collection_id": collection_id})
    pipeline = [
        {"$match": {"collection_id": collection_id}},
        {"$group": {"_id": "$case_fld_id", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    by_case: list[dict[str, Any]] = []
    async for doc in db.dsa_items.aggregate(pipeline):
        by_case.append({"case_fld_id": doc["_id"], "count": doc["count"]})
    return {"collection_id": collection_id, "totalItems": total, "byCase": by_case}


async def get_dsa_case_folders(collection_id: str) -> list[dict[str, Any]]:
    """Return distinct case folders for a collection: case_fld_id and folder_name (patient/case)."""
    db = await get_db()
    pipeline = [
        {"$match": {"collection_id": collection_id}},
        {"$group": {
            "_id": "$case_fld_id",
            "folder_name": {"$first": "$case_fld_name"},
        }},
        {"$sort": {"_id": 1}},
    ]
    out: list[dict[str, Any]] = []
    async for doc in db.dsa_items.aggregate(pipeline):
        if doc["_id"] is not None:
            out.append({
                "case_fld_id": str(doc["_id"]),
                "folder_name": doc.get("folder_name") or "",
            })
    return out


async def get_dsa_items_count_for_case(
    collection_id: str, case_fld_id: str
) -> int:
    """Return the number of items (slides) for a given case_fld_id in a collection."""
    db = await get_db()
    return await db.dsa_items.count_documents(
        {"collection_id": collection_id, "case_fld_id": case_fld_id}
    )


COLLECTION_SCOPED_COLLECTIONS = (
    "protocols",
    "case_id_mappings",
    "region_label_mappings",
    "stain_label_mappings",
    "slides",
    "patient_id_mappings",
    "block2region",
    "block2region_versions",
    "case_collection_registry",
    "dsa_items",
)

# All Mongo collections exported by admin backup (includes global metadata).
BACKUP_COLLECTION_NAMES = (
    "collection_metadata",
    *COLLECTION_SCOPED_COLLECTIONS,
    "clinical_by_nacc",
)


async def export_database_backup() -> dict[str, Any]:
    """Export every BDSA collection document for JSON backup."""
    from app.core.config import settings

    db = await get_db()
    collections: dict[str, list[dict[str, Any]]] = {}
    counts: dict[str, int] = {}

    for name in BACKUP_COLLECTION_NAMES:
        docs: list[dict[str, Any]] = []
        async for doc in db[name].find({}):
            docs.append(doc)
        collections[name] = docs
        counts[name] = len(docs)

    return {
        "exportedAt": _now_iso(),
        "database": settings.mongodb_db,
        "service": settings.app_name,
        "counts": counts,
        "collections": collections,
    }


async def save_database_backup_to_disk(backup_dir: str) -> dict[str, Any]:
    """Write a timestamped JSON backup file under backup_dir. Returns path metadata."""
    import json
    from pathlib import Path

    from bson import json_util

    backup = await export_database_backup()
    out_dir = Path(backup_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"bdsa-backup-{stamp}.json"
    path = out_dir / filename
    path.write_text(
        json.dumps(backup, default=json_util.default, indent=2),
        encoding="utf-8",
    )
    return {
        "savedAt": _now_iso(),
        "path": str(path.resolve()),
        "filename": filename,
        "counts": backup["counts"],
    }


async def list_collection_ids() -> list[str]:
    """List all collection_id values that have at least one resource."""
    db = await get_db()
    ids = set()
    for coll_name in COLLECTION_SCOPED_COLLECTIONS:
        cursor = db[coll_name].find({}, {"collection_id": 1})
        async for doc in cursor:
            ids.add(doc["collection_id"])
    return sorted(ids)


async def get_collection_display_name(collection_id: str) -> str | None:
    db = await get_db()
    doc = await db.collection_metadata.find_one({"collection_id": collection_id})
    if not doc:
        return None
    name = (doc.get("display_name") or "").strip()
    return name or None


async def set_collection_display_name(collection_id: str, display_name: str) -> dict[str, Any]:
    db = await get_db()
    display_name = display_name.strip()
    if not display_name:
        raise ValueError("display_name is required")
    doc = {
        "collection_id": collection_id,
        "display_name": display_name,
        "updated_at": _now_iso(),
    }
    await db.collection_metadata.update_one(
        {"collection_id": collection_id},
        {"$set": doc},
        upsert=True,
    )
    return doc


async def list_collections_enriched() -> list[dict[str, Any]]:
    """Collections with stable # (sort order) and display_name."""
    ids = await list_collection_ids()
    db = await get_db()
    meta_by_id: dict[str, dict[str, Any]] = {}
    async for doc in db.collection_metadata.find({}):
        meta_by_id[doc["collection_id"]] = doc

    out: list[dict[str, Any]] = []
    for number, collection_id in enumerate(ids, start=1):
        meta = meta_by_id.get(collection_id, {})
        display_name = (meta.get("display_name") or "").strip()
        if not display_name:
            display_name = f"Collection {number}"
        out.append(
            {
                "collection_id": collection_id,
                "display_name": display_name,
                "number": number,
            }
        )
    return out


async def delete_collection(collection_id: str) -> dict[str, Any]:
    """Permanently delete all data for this collection from every collection-scoped collection."""
    db = await get_db()
    deleted: dict[str, int] = {}
    for coll_name in COLLECTION_SCOPED_COLLECTIONS:
        result = await db[coll_name].delete_many({"collection_id": collection_id})
        deleted[coll_name] = result.deleted_count
    meta = await db.collection_metadata.delete_one({"collection_id": collection_id})
    deleted["collection_metadata"] = meta.deleted_count
    return {"deleted": deleted, "collection_id": collection_id }


async def rename_collection(collection_id: str, new_collection_id: str) -> dict[str, Any]:
    """Rename collection_id to new_collection_id across all collection-scoped collections."""
    if collection_id == new_collection_id:
        return {"updated": {}, "collection_id": collection_id, "new_collection_id": new_collection_id}
    db = await get_db()
    updated: dict[str, int] = {}
    for coll_name in COLLECTION_SCOPED_COLLECTIONS:
        result = await db[coll_name].update_many(
            {"collection_id": collection_id},
            {"$set": {"collection_id": new_collection_id}},
        )
        updated[coll_name] = result.modified_count
    await db.collection_metadata.update_one(
        {"collection_id": collection_id},
        {"$set": {"collection_id": new_collection_id}},
    )
    return {"updated": updated, "collection_id": collection_id, "new_collection_id": new_collection_id}
