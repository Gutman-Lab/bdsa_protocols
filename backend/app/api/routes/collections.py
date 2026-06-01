"""API routes for listing collections and case–collection association."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.repositories import (
    list_collection_ids,
    list_collections_enriched,
    set_collection_display_name,
    get_collections_for_case,
    get_cases_for_collection,
    delete_collection,
    rename_collection,
)
from app.schemas.collections import CollectionMetadataBody, CollectionsListResponse

router = APIRouter(prefix="/collections", tags=["collections"])


class RenameCollectionBody(BaseModel):
    new_collection_id: str


@router.get("", response_model=CollectionsListResponse)
async def list_collections() -> CollectionsListResponse:
    """List collections with auto-assigned # and display names."""
    items = await list_collections_enriched()
    return CollectionsListResponse(
        collection_ids=[c["collection_id"] for c in items],
        collections=items,
    )


@router.put("/{collection_id}/metadata")
async def put_collection_metadata(
    collection_id: str, body: CollectionMetadataBody
) -> dict:
    """Set human-readable display name for a collection (ID unchanged)."""
    name = (body.display_name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="display_name is required.")
    try:
        doc = await set_collection_display_name(collection_id, name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"collection_id": collection_id, "display_name": doc["display_name"]}


@router.get("/cases/{case_id}/collections")
async def list_collections_for_case(case_id: str) -> dict[str, list[str]]:
    """List collection IDs this case is associated with (via block2region or case-id-mappings)."""
    ids = await get_collections_for_case(case_id)
    return {"case_id": case_id, "collection_ids": ids}


@router.get("/{collection_id}/cases")
async def list_cases_in_collection(collection_id: str) -> dict[str, list[str]]:
    """List case IDs associated with this collection (via block2region or case-id-mappings)."""
    ids = await get_cases_for_collection(collection_id)
    return {"collection_id": collection_id, "case_ids": ids}


@router.delete("/{collection_id}")
async def delete_collection_route(collection_id: str, confirm: bool = False) -> dict:
    """Permanently delete all data for this collection. Requires query param: ?confirm=true."""
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Deletion requires query param: confirm=true",
        )
    return await delete_collection(collection_id)


@router.put("/{collection_id}/rename")
async def rename_collection_route(collection_id: str, body: RenameCollectionBody) -> dict:
    """Rename collection_id to new_collection_id across all resources."""
    new_id = (body.new_collection_id or "").strip()
    if not new_id:
        raise HTTPException(status_code=400, detail="new_collection_id is required.")
    return await rename_collection(collection_id, new_id)
