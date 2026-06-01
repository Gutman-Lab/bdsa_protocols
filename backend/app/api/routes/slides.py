"""API routes for slide/item BDSA metadata (wrangler-compatible)."""
from typing import Any

from fastapi import APIRouter

from app.db.repositories import get_slides, set_slides
from app.schemas.slides import SlidesPayload, SlidesResponse

router = APIRouter(
    prefix="/collections/{collection_id}/slides",
    tags=["slides"],
)


@router.get("", response_model=SlidesResponse)
async def get_collection_slides(collection_id: str) -> SlidesResponse:
    """Get slide metadata (BDSA per-slide info) for a collection.
    Returns null if the collection has no slides stored.
    """
    data = await get_slides(collection_id)
    if data is None:
        return SlidesResponse(
            collection_id=collection_id,
            slides=None,
        )
    payload = SlidesPayload(
        slides=data.get("slides", []),
        lastUpdated=data.get("lastUpdated"),
        source=data.get("source", "BDSA-Schema-Wrangler"),
        version=data.get("version", "1.0"),
    )
    return SlidesResponse(
        collection_id=collection_id,
        slides=payload,
    )


@router.put("", response_model=SlidesResponse)
async def put_collection_slides(
    collection_id: str, body: SlidesPayload
) -> SlidesResponse:
    """Replace all slide metadata for a collection (full replace).
    Body should match wrangler processedData items (id, BDSA.bdsaLocal, etc.).
    """
    payload: dict[str, Any] = {
        "slides": body.slides,
        "source": body.source,
        "version": body.version,
    }
    stored = await set_slides(collection_id, payload)
    return SlidesResponse(
        collection_id=collection_id,
        slides=SlidesPayload(
            slides=stored.get("slides", []),
            lastUpdated=stored.get("lastUpdated"),
            source=stored.get("source", "BDSA-Schema-Wrangler"),
            version=stored.get("version", "1.0"),
        ),
    )
