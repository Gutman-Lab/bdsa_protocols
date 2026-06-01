"""Pydantic schemas for localPatientId <-> BDSA-Patient-ID mappings."""
from pydantic import BaseModel, Field


class PatientIdMappingItem(BaseModel):
    """Single localPatientId with optional BDSA-Patient-ID (key assigned later)."""

    localPatientId: str
    bdsaPatientId: str | None = None


class PatientIdMappingsPayload(BaseModel):
    """Patient ID mappings payload (collection-scoped)."""

    institutionId: str = "001"
    mappings: list[PatientIdMappingItem] = Field(default_factory=list)
    lastUpdated: str | None = None
    source: str = "BDSA-Schema-Wrangler"
    version: str = "1.0"
    totalMappings: int = 0

    class Config:
        extra = "allow"


class PatientIdMappingsResponse(BaseModel):
    """Response for GET patient-id-mappings."""

    success: bool = True
    collection_id: str
    patientIdMappings: PatientIdMappingsPayload | None
