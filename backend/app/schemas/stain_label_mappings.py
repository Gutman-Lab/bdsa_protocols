"""Pydantic schemas for STAINO -> stainProtocolId mappings."""
from pydantic import BaseModel, Field


class StainLabelMappingItem(BaseModel):
    stainLabel: str
    normalized: str | None = None
    stainProtocolId: str
    validated: bool = True
    sourceField: str = "STAINO"
    source: str | None = None


class StainLabelMappingsPayload(BaseModel):
    mappings: list[StainLabelMappingItem] = Field(default_factory=list)
    lastUpdated: str | None = None
    source: str = "BDSA-Schema-Wrangler"
    version: str = "1.0"
    totalMappings: int = 0

    class Config:
        extra = "allow"


class StainLabelMappingsResponse(BaseModel):
    success: bool = True
    collection_id: str
    stainLabelMappings: StainLabelMappingsPayload | None


class StainLabelMappingConflictDetail(BaseModel):
    kind: str
    stainLabel: str | None = None
    normalized: str | None = None
    stainProtocolId: str | None = None
    existingStainProtocolId: str | None = None
    requestedStainProtocolId: str | None = None


class StainLabelValidateResponse(BaseModel):
    success: bool = True
    valid: bool
    conflicts: list[StainLabelMappingConflictDetail] = Field(default_factory=list)


class StainLabelLookupResponse(BaseModel):
    success: bool = True
    collection_id: str
    mapping: StainLabelMappingItem
