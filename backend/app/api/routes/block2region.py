"""API routes for block->region map per case."""
from fastapi import APIRouter, HTTPException

from app.db.repositories import (
    get_block2region,
    set_block2region,
    get_all_block2region_for_collection,
    get_block2region_stats,
    get_block2region_versions,
    get_block2region_by_version,
    restore_block2region_from_version,
)
from app.schemas.block2region import (
    Block2RegionPayload,
    Block2RegionResponse,
    Block2RegionCollectionResponse,
    Block2RegionCaseEntry,
    Block2RegionVersionEntry,
    Block2RegionVersionsResponse,
    Block2RegionRestoreRequest,
)

router = APIRouter(
    prefix="/collections/{collection_id}",
    tags=["block2region"],
)


@router.get("/cases/{case_id}/block2region", response_model=Block2RegionResponse)
async def get_case_block2region(collection_id: str, case_id: str) -> Block2RegionResponse:
    """Get block->region map for a given case (case_id can be localCaseId or bdsaCaseId)."""
    data = await get_block2region(collection_id, case_id)
    if data is None:
        return Block2RegionResponse(
            collection_id=collection_id,
            case_id=case_id,
            block2region=None,
        )
    payload = Block2RegionPayload(
        case_id=case_id,
        block2region=data.get("block2region", {}),
        mapping_source=data.get("mapping_source"),
        validated=data.get("validated", False),
        case_status=data.get("case_status"),
        lastUpdated=data.get("lastUpdated"),
        source=data.get("source", "BDSA-Schema-Wrangler"),
        version=data.get("version", "1.0"),
    )
    return Block2RegionResponse(
        collection_id=collection_id,
        case_id=case_id,
        block2region=payload,
    )


@router.put("/cases/{case_id}/block2region", response_model=Block2RegionResponse)
async def put_case_block2region(
    collection_id: str, case_id: str, body: Block2RegionPayload
) -> Block2RegionResponse:
    """Store or replace block->region map for a case. Case-level: case_status = SKIP / NEEDS_RESEARCH / NOT_SCANNED. Optional: mapping_source, validated (bool)."""
    stored = await set_block2region(
        collection_id,
        case_id,
        body.block2region,
        mapping_source=body.mapping_source,
        validated=body.validated,
        case_status=body.case_status,
    )
    payload = Block2RegionPayload(
        case_id=case_id,
        block2region=stored.get("block2region", {}),
        mapping_source=stored.get("mapping_source"),
        validated=stored.get("validated", False),
        case_status=stored.get("case_status"),
        lastUpdated=stored.get("lastUpdated"),
        source=stored.get("source", "BDSA-Schema-Wrangler"),
        version=stored.get("version", "1.0"),
    )
    return Block2RegionResponse(
        collection_id=collection_id,
        case_id=case_id,
        block2region=payload,
    )


@router.get("/block2region/stats")
async def get_collection_block2region_stats(collection_id: str) -> dict:
    """Return counts for this collection: casesWithMaps, totalPairs, validatedCount, caseIds."""
    return await get_block2region_stats(collection_id)


@router.get("/block2region", response_model=Block2RegionCollectionResponse)
async def get_collection_block2region(collection_id: str) -> Block2RegionCollectionResponse:
    """Get block->region maps for all cases in the collection.
    Returns by_case: { case_id: { block2region, mapping_source?, validated?, lastUpdated? } }.
    """
    raw = await get_all_block2region_for_collection(collection_id)
    by_case = {
        cid: Block2RegionCaseEntry(
            block2region=ent.get("block2region", {}),
            mapping_source=ent.get("mapping_source"),
            validated=ent.get("validated", False),
            case_status=ent.get("case_status"),
            lastUpdated=ent.get("lastUpdated"),
        )
        for cid, ent in raw.items()
    }
    return Block2RegionCollectionResponse(
        collection_id=collection_id,
        by_case=by_case,
    )


@router.get("/cases/{case_id}/block2region/versions", response_model=Block2RegionVersionsResponse)
async def list_block2region_versions(collection_id: str, case_id: str) -> Block2RegionVersionsResponse:
    """List versioned snapshots for this case (newest first). Each PUT creates a new version."""
    raw = await get_block2region_versions(collection_id, case_id)
    versions = [
        Block2RegionVersionEntry(
            version=d["version"],
            block2region=d.get("block2region", {}),
            mapping_source=d.get("mapping_source"),
            validated=d.get("validated", False),
            case_status=d.get("case_status"),
            createdAt=d.get("createdAt"),
        )
        for d in raw
    ]
    return Block2RegionVersionsResponse(
        collection_id=collection_id,
        case_id=case_id,
        versions=versions,
    )


@router.get("/cases/{case_id}/block2region/versions/{version:int}")
async def get_block2region_version(
    collection_id: str, case_id: str, version: int
) -> dict:
    """Get a single version snapshot (full payload)."""
    data = await get_block2region_by_version(collection_id, case_id, version)
    if data is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return {"success": True, "collection_id": collection_id, "case_id": case_id, "version": version, **data}


@router.post("/cases/{case_id}/block2region/restore", response_model=Block2RegionResponse)
async def restore_block2region(
    collection_id: str, case_id: str, body: Block2RegionRestoreRequest
) -> Block2RegionResponse:
    """Restore current block2region for this case to a previous version (creates a new version entry)."""
    result = await restore_block2region_from_version(collection_id, case_id, body.version)
    if result is None:
        raise HTTPException(status_code=404, detail="Version not found")
    payload = Block2RegionPayload(
        case_id=case_id,
        block2region=result.get("block2region", {}),
        mapping_source=result.get("mapping_source"),
        validated=result.get("validated", False),
        case_status=result.get("case_status"),
        lastUpdated=result.get("lastUpdated"),
        source=result.get("source", "BDSA-Schema-Wrangler"),
        version=result.get("version", "1.0"),
    )
    return Block2RegionResponse(
        collection_id=collection_id,
        case_id=case_id,
        block2region=payload,
    )
