"""API routes for REGIONO text -> regionProtocolId mappings."""
from typing import Any

from fastapi import APIRouter, HTTPException

from app.db.repositories import (
    get_region_label_mapping_by_normalized,
    get_region_label_mappings,
    merge_region_label_mappings,
    replace_region_label_mappings_validated,
    validate_region_label_mappings_merge,
)
from app.schemas.region_label_mappings import (
    RegionLabelLookupResponse,
    RegionLabelMappingConflictDetail,
    RegionLabelMappingItem,
    RegionLabelMappingsPayload,
    RegionLabelMappingsResponse,
    RegionLabelValidateResponse,
)
from app.services.region_label_validation import normalize_region_label

router = APIRouter(
    prefix="/collections/{collection_id}/region-label-mappings",
    tags=["region-label-mappings"],
)


def _payload_from_stored(data: dict[str, Any]) -> RegionLabelMappingsPayload:
    return RegionLabelMappingsPayload(
        mappings=data.get("mappings", []),
        lastUpdated=data.get("lastUpdated"),
        source=data.get("source", "BDSA-Schema-Wrangler"),
        version=data.get("version", "1.0"),
        totalMappings=data.get("totalMappings", len(data.get("mappings", []))),
    )


def _response(collection_id: str, stored: dict[str, Any]) -> RegionLabelMappingsResponse:
    return RegionLabelMappingsResponse(
        collection_id=collection_id,
        regionLabelMappings=_payload_from_stored(stored),
    )


def _mapping_item(row: dict[str, Any]) -> RegionLabelMappingItem:
    return RegionLabelMappingItem(
        regionLabel=row.get("regionLabel") or row.get("normalized") or "",
        normalized=row.get("normalized"),
        regionProtocolId=row["regionProtocolId"],
        validated=row.get("validated", True),
        sourceField=row.get("sourceField", "REGIONO"),
        source=row.get("source"),
    )


@router.get("", response_model=RegionLabelMappingsResponse)
async def get_collection_region_label_mappings(
    collection_id: str,
) -> RegionLabelMappingsResponse:
    """Get REGIONO label -> regionProtocolId mappings for a collection."""
    data = await get_region_label_mappings(collection_id)
    if data is None:
        return RegionLabelMappingsResponse(
            collection_id=collection_id,
            regionLabelMappings=None,
        )
    return RegionLabelMappingsResponse(
        collection_id=collection_id,
        regionLabelMappings=_payload_from_stored(data),
    )


@router.get("/by-label/{normalized_label}", response_model=RegionLabelLookupResponse)
async def get_region_label_mapping_by_label_route(
    collection_id: str,
    normalized_label: str,
) -> RegionLabelLookupResponse:
    """Look up a validated mapping by normalized REGIONO label."""
    key = normalize_region_label(normalized_label)
    row = await get_region_label_mapping_by_normalized(collection_id, key)
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={
                "detail": "region label not found",
                "normalized": key or normalized_label,
            },
        )
    return RegionLabelLookupResponse(
        collection_id=collection_id,
        mapping=_mapping_item(row),
    )


@router.put("", response_model=RegionLabelMappingsResponse)
async def put_collection_region_label_mappings(
    collection_id: str, body: RegionLabelMappingsPayload
) -> RegionLabelMappingsResponse:
    """Replace region label mappings for a collection (full replace)."""
    payload: dict[str, Any] = {
        "mappings": [m.model_dump(exclude_none=True) for m in body.mappings],
        "totalMappings": len(body.mappings),
        "source": body.source,
        "version": body.version,
    }
    stored = await replace_region_label_mappings_validated(collection_id, payload)
    return _response(collection_id, stored)


@router.post("/merge", response_model=RegionLabelMappingsResponse)
async def merge_collection_region_label_mappings(
    collection_id: str, body: RegionLabelMappingsPayload
) -> RegionLabelMappingsResponse:
    """Merge region label mappings with existing (by normalized)."""
    stored = await merge_region_label_mappings(
        collection_id,
        [m.model_dump(exclude_none=True) for m in body.mappings],
        source=body.source,
        version=body.version,
    )
    return _response(collection_id, stored)


@router.post("/validate", response_model=RegionLabelValidateResponse)
async def validate_collection_region_label_mappings(
    collection_id: str, body: RegionLabelMappingsPayload
) -> RegionLabelValidateResponse:
    """Dry-run merge validation without writing."""
    conflicts = await validate_region_label_mappings_merge(
        collection_id,
        [m.model_dump(exclude_none=True) for m in body.mappings],
    )
    return RegionLabelValidateResponse(
        valid=len(conflicts) == 0,
        conflicts=[RegionLabelMappingConflictDetail(**c) for c in conflicts],
    )
