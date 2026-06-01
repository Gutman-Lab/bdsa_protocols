"""API routes for case ID mappings (wrangler-compatible)."""
from typing import Any

from fastapi import APIRouter

from app.db.repositories import (
    get_case_id_mappings,
    set_case_id_mappings,
    merge_case_id_mappings,
)
from app.schemas.case_mappings import (
    CaseIdMappingsPayload,
    CaseIdMappingsResponse,
)

router = APIRouter(
    prefix="/collections/{collection_id}/case-id-mappings",
    tags=["case-id-mappings"],
)


@router.get("", response_model=CaseIdMappingsResponse)
async def get_collection_case_id_mappings(collection_id: str) -> CaseIdMappingsResponse:
    """Get case ID mappings (localCaseId -> bdsaCaseId) for a collection.
    Returns null if the collection has no mappings stored.
    """
    data = await get_case_id_mappings(collection_id)
    if data is None:
        return CaseIdMappingsResponse(
            collection_id=collection_id,
            caseIdMappings=None,
        )
    payload = CaseIdMappingsPayload(
        institutionId=data.get("institutionId", "001"),
        mappings=data.get("mappings", []),
        lastUpdated=data.get("lastUpdated"),
        source=data.get("source", "BDSA-Schema-Wrangler"),
        version=data.get("version", "1.0"),
        totalMappings=data.get("totalMappings", len(data.get("mappings", []))),
    )
    return CaseIdMappingsResponse(
        collection_id=collection_id,
        caseIdMappings=payload,
    )


@router.put("", response_model=CaseIdMappingsResponse)
async def put_collection_case_id_mappings(
    collection_id: str, body: CaseIdMappingsPayload
) -> CaseIdMappingsResponse:
    """Replace case ID mappings for a collection (full replace).
    Compatible with BDSA-Schema-Wrangler push.
    """
    payload: dict[str, Any] = {
        "institutionId": body.institutionId,
        "mappings": [m.model_dump() for m in body.mappings],
        "totalMappings": len(body.mappings),
        "source": body.source,
        "version": body.version,
    }
    stored = await set_case_id_mappings(collection_id, payload)
    return CaseIdMappingsResponse(
        collection_id=collection_id,
        caseIdMappings=CaseIdMappingsPayload(
            institutionId=stored.get("institutionId", "001"),
            mappings=stored.get("mappings", []),
            lastUpdated=stored.get("lastUpdated"),
            source=stored.get("source", "BDSA-Schema-Wrangler"),
            version=stored.get("version", "1.0"),
            totalMappings=stored.get("totalMappings", 0),
        ),
    )


@router.post("/merge", response_model=CaseIdMappingsResponse)
async def merge_collection_case_id_mappings(
    collection_id: str, body: CaseIdMappingsPayload
) -> CaseIdMappingsResponse:
    """Merge case ID mappings with existing (by localCaseId)."""
    stored = await merge_case_id_mappings(
        collection_id,
        [m.model_dump() for m in body.mappings],
        body.institutionId,
    )
    return CaseIdMappingsResponse(
        collection_id=collection_id,
        caseIdMappings=CaseIdMappingsPayload(
            institutionId=stored.get("institutionId", "001"),
            mappings=stored.get("mappings", []),
            lastUpdated=stored.get("lastUpdated"),
            source=stored.get("source", "BDSA-Schema-Wrangler"),
            version=stored.get("version", "1.0"),
            totalMappings=stored.get("totalMappings", 0),
        ),
    )
