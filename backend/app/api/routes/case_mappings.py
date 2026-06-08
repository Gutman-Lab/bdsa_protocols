"""API routes for case ID mappings (wrangler-compatible)."""
from typing import Any

from fastapi import APIRouter, HTTPException

from app.db.repositories import (
    allocate_case_id_mapping,
    allocate_case_id_mappings_batch,
    get_case_id_mapping_by_alternate,
    get_case_id_mapping_by_bdsa,
    get_case_id_mapping_by_local,
    get_case_id_mappings,
    merge_case_id_mappings,
    replace_case_id_mappings_validated,
    validate_case_id_mappings_merge,
)
from app.schemas.case_mappings import (
    CaseIdAllocateBatchRequest,
    CaseIdAllocateBatchResponse,
    CaseIdAllocateBatchItem,
    CaseIdAllocateRequest,
    CaseIdAllocateResponse,
    CaseIdLookupResponse,
    CaseIdMappingConflictDetail,
    CaseIdMappingItem,
    CaseIdMappingsPayload,
    CaseIdMappingsResponse,
    CaseIdValidateResponse,
)
router = APIRouter(
    prefix="/collections/{collection_id}/case-id-mappings",
    tags=["case-id-mappings"],
)


def _payload_from_stored(data: dict[str, Any]) -> CaseIdMappingsPayload:
    return CaseIdMappingsPayload(
        institutionId=data.get("institutionId", "001"),
        mappings=data.get("mappings", []),
        lastUpdated=data.get("lastUpdated"),
        source=data.get("source", "BDSA-Schema-Wrangler"),
        version=data.get("version", "1.0"),
        totalMappings=data.get("totalMappings", len(data.get("mappings", []))),
    )


def _response(collection_id: str, stored: dict[str, Any]) -> CaseIdMappingsResponse:
    return CaseIdMappingsResponse(
        collection_id=collection_id,
        caseIdMappings=_payload_from_stored(stored),
    )


@router.get("", response_model=CaseIdMappingsResponse)
async def get_collection_case_id_mappings(collection_id: str) -> CaseIdMappingsResponse:
    """Get case ID mappings (localCaseId -> bdsaCaseId) for a collection."""
    data = await get_case_id_mappings(collection_id)
    if data is None:
        return CaseIdMappingsResponse(
            collection_id=collection_id,
            caseIdMappings=None,
        )
    return CaseIdMappingsResponse(
        collection_id=collection_id,
        caseIdMappings=_payload_from_stored(data),
    )


@router.get("/by-bdsa/{bdsa_case_id}", response_model=CaseIdLookupResponse)
async def get_case_id_mapping_by_bdsa_route(
    collection_id: str,
    bdsa_case_id: str,
) -> CaseIdLookupResponse:
    """Look up a single mapping by bdsaCaseId."""
    mapping = await get_case_id_mapping_by_bdsa(collection_id, bdsa_case_id)
    if mapping is None:
        raise HTTPException(
            status_code=404,
            detail={
                "detail": "bdsaCaseId not found",
                "bdsaCaseId": bdsa_case_id,
            },
        )
    return CaseIdLookupResponse(
        collection_id=collection_id,
        mapping=CaseIdMappingItem(**mapping),
    )


@router.get("/by-alternate/{system}/{value}", response_model=CaseIdLookupResponse)
async def get_case_id_mapping_by_alternate_route(
    collection_id: str,
    system: str,
    value: str,
) -> CaseIdLookupResponse:
    """Look up a single mapping by external ID system and value (e.g. nacc / U1234567)."""
    mapping = await get_case_id_mapping_by_alternate(collection_id, system, value)
    if mapping is None:
        raise HTTPException(
            status_code=404,
            detail={
                "detail": "alternate ID not found",
                "alternateIdSystem": system,
                "alternateIdValue": value,
            },
        )
    return CaseIdLookupResponse(
        collection_id=collection_id,
        mapping=CaseIdMappingItem(**mapping),
    )


@router.get("/by-local/{local_case_id}", response_model=CaseIdLookupResponse)
async def get_case_id_mapping_by_local_route(
    collection_id: str,
    local_case_id: str,
) -> CaseIdLookupResponse:
    """Look up a single mapping by localCaseId."""
    mapping = await get_case_id_mapping_by_local(collection_id, local_case_id)
    if mapping is None:
        raise HTTPException(
            status_code=404,
            detail={
                "detail": "localCaseId not found",
                "localCaseId": local_case_id,
            },
        )
    return CaseIdLookupResponse(
        collection_id=collection_id,
        mapping=CaseIdMappingItem(**mapping),
    )


@router.put("", response_model=CaseIdMappingsResponse)
async def put_collection_case_id_mappings(
    collection_id: str, body: CaseIdMappingsPayload
) -> CaseIdMappingsResponse:
    """Replace case ID mappings for a collection (full replace)."""
    payload: dict[str, Any] = {
        "institutionId": body.institutionId,
        "mappings": [m.model_dump() for m in body.mappings],
        "totalMappings": len(body.mappings),
        "source": body.source,
        "version": body.version,
    }
    stored = await replace_case_id_mappings_validated(collection_id, payload)
    return _response(collection_id, stored)


@router.post("/merge", response_model=CaseIdMappingsResponse)
async def merge_collection_case_id_mappings(
    collection_id: str, body: CaseIdMappingsPayload
) -> CaseIdMappingsResponse:
    """Merge case ID mappings with existing (by localCaseId)."""
    stored = await merge_case_id_mappings(
        collection_id,
        [m.model_dump() for m in body.mappings],
        body.institutionId,
        source=body.source,
        version=body.version,
    )
    return _response(collection_id, stored)


@router.post("/validate", response_model=CaseIdValidateResponse)
async def validate_collection_case_id_mappings(
    collection_id: str, body: CaseIdMappingsPayload
) -> CaseIdValidateResponse:
    """Dry-run merge validation without writing."""
    conflicts = await validate_case_id_mappings_merge(
        collection_id,
        [m.model_dump() for m in body.mappings],
        body.institutionId,
    )
    return CaseIdValidateResponse(
        valid=len(conflicts) == 0,
        conflicts=[CaseIdMappingConflictDetail(**c) for c in conflicts],
    )


@router.post("/allocate", response_model=CaseIdAllocateResponse)
async def allocate_collection_case_id_mapping(
    collection_id: str, body: CaseIdAllocateRequest
) -> CaseIdAllocateResponse:
    """Allocate the next free bdsaCaseId for a localCaseId (idempotent)."""
    try:
        mapping, allocated = await allocate_case_id_mapping(
            collection_id,
            body.localCaseId,
            body.institutionId,
            source=body.source,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return CaseIdAllocateResponse(
        collection_id=collection_id,
        mapping=CaseIdMappingItem(**mapping),
        allocated=allocated,
    )


@router.post("/allocate-batch", response_model=CaseIdAllocateBatchResponse)
async def allocate_collection_case_id_mappings_batch(
    collection_id: str, body: CaseIdAllocateBatchRequest
) -> CaseIdAllocateBatchResponse:
    """Allocate mappings for multiple local case IDs in one request."""
    results = await allocate_case_id_mappings_batch(
        collection_id,
        body.localCaseIds,
        body.institutionId,
        source=body.source,
    )
    return CaseIdAllocateBatchResponse(
        collection_id=collection_id,
        mappings=[CaseIdAllocateBatchItem(**row) for row in results],
    )
