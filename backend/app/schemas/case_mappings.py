"""Pydantic schemas for case ID mappings (wrangler-compatible)."""
from pydantic import BaseModel, Field


class CaseIdMappingItem(BaseModel):
    """Single localCaseId -> bdsaCaseId mapping with optional external ID crosswalks."""

    localCaseId: str
    bdsaCaseId: str
    alternateIds: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "External identifier crosswalk keyed by system name (e.g. nacc, ndd). "
            "Keys are normalized to lowercase on write."
        ),
    )

    model_config = {"extra": "allow"}


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


class CaseIdMappingConflictDetail(BaseModel):
    kind: str
    localCaseId: str | None = None
    bdsaCaseId: str | None = None
    existingLocalCaseId: str | None = None
    existingBdsaCaseId: str | None = None
    requestedLocalCaseId: str | None = None
    requestedBdsaCaseId: str | None = None
    alternateIdSystem: str | None = None
    alternateIdValue: str | None = None


class CaseIdValidateResponse(BaseModel):
    success: bool = True
    valid: bool
    conflicts: list[CaseIdMappingConflictDetail] = Field(default_factory=list)


class CaseIdAllocateRequest(BaseModel):
    localCaseId: str
    institutionId: str = "001"
    source: str = "BDSA-Schema-Wrangler"


class CaseIdAllocateResponse(BaseModel):
    success: bool = True
    collection_id: str
    mapping: CaseIdMappingItem
    allocated: bool


class CaseIdAllocateBatchRequest(BaseModel):
    institutionId: str = "001"
    localCaseIds: list[str] = Field(default_factory=list)
    source: str = "BDSA-Schema-Wrangler"


class CaseIdAllocateBatchItem(BaseModel):
    localCaseId: str
    bdsaCaseId: str
    allocated: bool


class CaseIdAllocateBatchResponse(BaseModel):
    success: bool = True
    collection_id: str
    mappings: list[CaseIdAllocateBatchItem]


class CaseIdLookupResponse(BaseModel):
    success: bool = True
    collection_id: str
    mapping: CaseIdMappingItem
