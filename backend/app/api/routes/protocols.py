"""API routes for stain and region protocols (wrangler-compatible)."""
from typing import Any

from fastapi import APIRouter

from app.db.repositories import get_protocols, set_protocols, merge_protocols
from app.schemas.protocols import ProtocolsPayload, ProtocolsResponse

router = APIRouter(prefix="/collections/{collection_id}/protocols", tags=["protocols"])


@router.get("", response_model=ProtocolsResponse)
async def get_collection_protocols(collection_id: str) -> ProtocolsResponse:
    """Get stain and region protocols for a collection.
    Returns empty arrays if the collection has no protocols stored.
    """
    data = await get_protocols(collection_id)
    if data is None:
        payload = ProtocolsPayload(
            stainProtocols=[],
            regionProtocols=[],
            blockProtocols=[],
        )
    else:
        payload = ProtocolsPayload(
            stainProtocols=data.get("stainProtocols", []),
            regionProtocols=data.get("regionProtocols", []),
            blockProtocols=data.get("blockProtocols", []),
            lastUpdated=data.get("lastUpdated"),
            source=data.get("source", "BDSA-Schema-Wrangler"),
            version=data.get("version", "1.0"),
        )
    return ProtocolsResponse(collection_id=collection_id, protocols=payload)


@router.put("", response_model=ProtocolsResponse)
async def put_collection_protocols(
    collection_id: str, body: ProtocolsPayload
) -> ProtocolsResponse:
    """Replace protocols for a collection (full replace).
    Compatible with BDSA-Schema-Wrangler push.
    """
    payload: dict[str, Any] = {
        "stainProtocols": body.stainProtocols,
        "regionProtocols": body.regionProtocols,
        "blockProtocols": body.blockProtocols,
        "source": body.source,
        "version": body.version,
    }
    stored = await set_protocols(collection_id, payload)
    return ProtocolsResponse(
        collection_id=collection_id,
        protocols=ProtocolsPayload(
            stainProtocols=stored.get("stainProtocols", []),
            regionProtocols=stored.get("regionProtocols", []),
            blockProtocols=stored.get("blockProtocols", []),
            lastUpdated=stored.get("lastUpdated"),
            source=stored.get("source", "BDSA-Schema-Wrangler"),
            version=stored.get("version", "1.0"),
        ),
    )


@router.post("/merge", response_model=ProtocolsResponse)
async def merge_collection_protocols(
    collection_id: str, body: ProtocolsPayload
) -> ProtocolsResponse:
    """Merge protocols with existing (by id). New protocols are added; existing ids are kept."""
    stored = await merge_protocols(
        collection_id,
        body.stainProtocols,
        body.regionProtocols,
        body.blockProtocols,
    )
    return ProtocolsResponse(
        collection_id=collection_id,
        protocols=ProtocolsPayload(
            stainProtocols=stored.get("stainProtocols", []),
            regionProtocols=stored.get("regionProtocols", []),
            blockProtocols=stored.get("blockProtocols", []),
            lastUpdated=stored.get("lastUpdated"),
            source=stored.get("source", "BDSA-Schema-Wrangler"),
            version=stored.get("version", "1.0"),
        ),
    )
