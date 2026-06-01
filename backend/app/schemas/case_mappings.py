"""Pydantic schemas for case ID mappings (wrangler-compatible)."""
from pydantic import BaseModel, Field


class CaseIdMappingItem(BaseModel):
    """Single localCaseId -> bdsaCaseId mapping."""

    localCaseId: str
    bdsaCaseId: str


class CaseIdMappingsPayload(BaseModel):
    """Case ID mappings payload as used by BDSA-Schema-Wrangler."""

    institutionId: str = "001"
    mappings: list[CaseIdMappingItem] = Field(default_factory=list)
    lastUpdated: str | None = None
    source: str = "BDSA-Schema-Wrangler"
    version: str = "1.0"
    totalMappings: int = 0

    class Config:
        extra = "allow"


class CaseIdMappingsResponse(BaseModel):
    """Response for GET case-id-mappings."""

    success: bool = True
    collection_id: str
    caseIdMappings: CaseIdMappingsPayload | None
