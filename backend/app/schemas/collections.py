"""Schemas for collection listing and display metadata."""
from pydantic import BaseModel, Field


class CollectionSummary(BaseModel):
    collection_id: str
    display_name: str
    number: int = Field(ge=1, description="Auto-assigned index in sorted list order")


class CollectionsListResponse(BaseModel):
    collection_ids: list[str] = Field(default_factory=list)
    collections: list[CollectionSummary] = Field(default_factory=list)


class CollectionMetadataBody(BaseModel):
    display_name: str
