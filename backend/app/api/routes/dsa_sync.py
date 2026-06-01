"""API routes for syncing and listing DSA/Girder items keyed by collection."""
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.db.repositories import (
    replace_dsa_items_for_collection,
    get_dsa_items_for_collection,
    get_dsa_items_stats,
    get_dsa_case_folders,
    get_dsa_items_count_for_case,
)
from app.schemas.dsa_sync import DsaSyncRequest, DsaSyncResponse
from app.services.girder_sync import (
    get_authenticated_client,
    fetch_collection_from_girder,
)

router = APIRouter(
    prefix="/collections/{collection_id}",
    tags=["dsa-sync"],
)


@router.post("/dsa-sync", response_model=DsaSyncResponse)
async def sync_dsa_collection(collection_id: str, body: DsaSyncRequest) -> DsaSyncResponse:
    """
    Pull all items from the given Girder folder and store them locally keyed by collection_id.
    The folder's subfolders are treated as patient/case folders; items are fetched recursively
    per patient and stored with case_fld_id. Requires DSA_API_URL and DSA_API_KEY in .env.
    """
    if not settings.dsa_api_url or not settings.dsa_api_key:
        raise HTTPException(
            status_code=503,
            detail="DSA sync not configured: set DSA_API_URL and DSA_API_KEY in .env",
        )
    gc = await get_authenticated_client()
    if gc is None:
        raise HTTPException(status_code=503, detail="DSA authentication failed")

    items = await fetch_collection_from_girder(gc, body.girder_folder_id)
    result = await replace_dsa_items_for_collection(collection_id, items)
    case_ids = {item.get("case_fld_id") for item in items if item.get("case_fld_id")}

    return DsaSyncResponse(
        success=True,
        collection_id=collection_id,
        girder_folder_id=body.girder_folder_id,
        total_items=result["count"],
        case_count=len(case_ids),
    )


@router.get("/dsa-items")
async def list_dsa_items(collection_id: str, case_fld_id: str | None = None) -> dict:
    """List stored DSA items for this collection. Optional query: case_fld_id to filter by patient folder."""
    items = await get_dsa_items_for_collection(collection_id, case_fld_id=case_fld_id)
    return {"success": True, "collection_id": collection_id, "items": items, "count": len(items)}


@router.get("/dsa-items/stats")
async def dsa_items_stats(collection_id: str) -> dict:
    """Return total item count and per-case counts for stored DSA items."""
    return await get_dsa_items_stats(collection_id)


@router.get("/dsa-items/cases")
async def list_dsa_cases(collection_id: str) -> dict:
    """List all cases (patient folders) for this collection: case_fld_id and folder_name."""
    cases = await get_dsa_case_folders(collection_id)
    return {
        "success": True,
        "collection_id": collection_id,
        "cases": cases,
    }


@router.get("/dsa-items/cases/{case_fld_id}/count")
async def dsa_items_count_for_case(collection_id: str, case_fld_id: str) -> dict:
    """Return the number of slides/items associated with the given case_fld_id."""
    count = await get_dsa_items_count_for_case(collection_id, case_fld_id)
    return {
        "success": True,
        "collection_id": collection_id,
        "case_fld_id": case_fld_id,
        "count": count,
    }
