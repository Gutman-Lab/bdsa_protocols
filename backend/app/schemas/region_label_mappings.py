"""Pydantic schemas for REGIONO -> regionProtocolId mappings."""
from pydantic import BaseModel, Field


class RegionLabelMappingItem(BaseModel):
    regionLabel: str
    normalized: str | None = None
    regionProtocolId: str
    validated: bool = True
    sourceField: str = "REGIONO"
    source: str | None = None


class RegionLabelMappingsPayload(BaseModel):
    mappings: list[RegionLabelMappingItem] = Field(default_factory=list)
    lastUpdated: str | None = None
    source: str = "BDSA-Schema-Wrangler"
    version: str = "1.0"
    totalMappings: int = 0

    class Config:
        extra = "allow"


class RegionLabelMappingsResponse(BaseModel):
    success: bool = True
    collection_id: str
    regionLabelMappings: RegionLabelMappingsPayload | None


class RegionLabelMappingConflictDetail(BaseModel):
    kind: str
    regionLabel: str | None = None
    normalized: str | None = None
    regionProtocolId: str | None = None
    existingRegionProtocolId: str | None = None
    requestedRegionProtocolId: str | None = None


class RegionLabelValidateResponse(BaseModel):
    success: bool = True
    valid: bool
    conflicts: list[RegionLabelMappingConflictDetail] = Field(default_factory=list)


class RegionLabelLookupResponse(BaseModel):
    success: bool = True
    collection_id: str
    mapping: RegionLabelMappingItem
