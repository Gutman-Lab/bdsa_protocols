"""API routes for STAINO text -> stainProtocolId mappings."""
from typing import Any

from fastapi import APIRouter, HTTPException

from app.db.repositories import (
    get_stain_label_mapping_by_normalized,
    get_stain_label_mappings,
    merge_stain_label_mappings,
    replace_stain_label_mappings_validated,
    validate_stain_label_mappings_merge,
)
from app.schemas.stain_label_mappings import (
    StainLabelLookupResponse,
    StainLabelMappingConflictDetail,
    StainLabelMappingItem,
    StainLabelMappingsPayload,
    StainLabelMappingsResponse,
    StainLabelValidateResponse,
)
from app.services.stain_label_validation import normalize_stain_label

router = APIRouter(
    prefix="/collections/{collection_id}/stain-label-mappings",
    tags=["stain-label-mappings"],
)


def _payload_from_stored(data: dict[str, Any]) -> StainLabelMappingsPayload:
    return StainLabelMappingsPayload(
        mappings=data.get("mappings", []),
        lastUpdated=data.get("lastUpdated"),
        source=data.get("source", "BDSA-Schema-Wrangler"),
        version=data.get("version", "1.0"),
        totalMappings=data.get("totalMappings", len(data.get("mappings", []))),
    )


def _response(collection_id: str, stored: dict[str, Any]) -> StainLabelMappingsResponse:
    return StainLabelMappingsResponse(
        collection_id=collection_id,
        stainLabelMappings=_payload_from_stored(stored),
    )


def _mapping_item(row: dict[str, Any]) -> StainLabelMappingItem:
    return StainLabelMappingItem(
        stainLabel=row.get("stainLabel") or row.get("normalized") or "",
        normalized=row.get("normalized"),
        stainProtocolId=row["stainProtocolId"],
        validated=row.get("validated", True),
        sourceField=row.get("sourceField", "STAINO"),
        source=row.get("source"),
    )


@router.get("", response_model=StainLabelMappingsResponse)
async def get_collection_stain_label_mappings(
    collection_id: str,
) -> StainLabelMappingsResponse:
    """Get STAINO label -> stainProtocolId mappings for a collection."""
    data = await get_stain_label_mappings(collection_id)
    if data is None:
        return StainLabelMappingsResponse(
            collection_id=collection_id,
            stainLabelMappings=None,
        )
    return StainLabelMappingsResponse(
        collection_id=collection_id,
        stainLabelMappings=_payload_from_stored(data),
    )


@router.get("/by-label/{normalized_label}", response_model=StainLabelLookupResponse)
async def get_stain_label_mapping_by_label_route(
    collection_id: str,
    normalized_label: str,
) -> StainLabelLookupResponse:
    """Look up a validated mapping by normalized STAINO label."""
    key = normalize_stain_label(normalized_label)
    row = await get_stain_label_mapping_by_normalized(collection_id, key)
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={
                "detail": "stain label not found",
                "normalized": key or normalized_label,
            },
        )
    return StainLabelLookupResponse(
        collection_id=collection_id,
        mapping=_mapping_item(row),
    )


@router.put("", response_model=StainLabelMappingsResponse)
async def put_collection_stain_label_mappings(
    collection_id: str, body: StainLabelMappingsPayload
) -> StainLabelMappingsResponse:
    """Replace stain label mappings for a collection (full replace)."""
    payload: dict[str, Any] = {
        "mappings": [m.model_dump(exclude_none=True) for m in body.mappings],
        "totalMappings": len(body.mappings),
        "source": body.source,
        "version": body.version,
    }
    stored = await replace_stain_label_mappings_validated(collection_id, payload)
    return _response(collection_id, stored)


@router.post("/merge", response_model=StainLabelMappingsResponse)
async def merge_collection_stain_label_mappings(
    collection_id: str, body: StainLabelMappingsPayload
) -> StainLabelMappingsResponse:
    """Merge stain label mappings with existing (by normalized)."""
    stored = await merge_stain_label_mappings(
        collection_id,
        [m.model_dump(exclude_none=True) for m in body.mappings],
        source=body.source,
        version=body.version,
    )
    return _response(collection_id, stored)


@router.post("/validate", response_model=StainLabelValidateResponse)
async def validate_collection_stain_label_mappings(
    collection_id: str, body: StainLabelMappingsPayload
) -> StainLabelValidateResponse:
    """Dry-run merge validation without writing."""
    conflicts = await validate_stain_label_mappings_merge(
        collection_id,
        [m.model_dump(exclude_none=True) for m in body.mappings],
    )
    return StainLabelValidateResponse(
        valid=len(conflicts) == 0,
        conflicts=[StainLabelMappingConflictDetail(**c) for c in conflicts],
    )
