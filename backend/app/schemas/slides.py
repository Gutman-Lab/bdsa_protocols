"""Pydantic schemas for slide/item BDSA metadata (wrangler-compatible)."""
from typing import Any

from pydantic import BaseModel, Field


class BdsaLocal(BaseModel):
    """BDSA local fields per slide (wrangler item.BDSA.bdsaLocal)."""

    localCaseId: str | None = None
    bdsaCaseId: str | None = None
    localStainID: str | None = None
    localRegionId: str | None = None

    class Config:
        extra = "allow"


class SlideItem(BaseModel):
    """Single slide/item with BDSA metadata."""

    id: str | None = None
    _id: str | None = None
    dsa_id: str | None = None
    BDSA: dict[str, Any] | None = None

    class Config:
        extra = "allow"


class SlidesPayload(BaseModel):
    """Bulk slides payload for a collection."""

    slides: list[dict[str, Any]] = Field(default_factory=list)
    lastUpdated: str | None = None
    source: str = "BDSA-Schema-Wrangler"
    version: str = "1.0"

    class Config:
        extra = "allow"


class SlidesResponse(BaseModel):
    """Response for GET slides."""

    success: bool = True
    collection_id: str
    slides: SlidesPayload | None
