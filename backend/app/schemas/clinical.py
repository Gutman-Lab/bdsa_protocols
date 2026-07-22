"""Pydantic schemas for NACC clinical records (clinical-metadata subset)."""
from pydantic import BaseModel, Field


class ClinicalVisitMeta(BaseModel):
    naccvnum: int | None = None
    visitDate: str | None = None


class ClinicalFields(BaseModel):
    """Fields aligned with clinical-metadata.json (all optional on read)."""

    NACCID: str | None = None
    NPSEX: int | None = None
    EDUC: int | None = None
    HISPANIC: int | None = None
    RACE: int | None = None
    NACCDAGE: int | None = None
    NACCUDSD: int | None = None
    NPPMIH: float | None = None
    NPADNC: int | None = None
    NPWBRWT: int | None = None

    model_config = {"extra": "allow"}


class ClinicalByNaccResponse(BaseModel):
    naccid: str
    clinical: ClinicalFields
    source: str | None = None
    visitMeta: ClinicalVisitMeta | None = None
    lastUpdated: str | None = None


class ClinicalStatsResponse(BaseModel):
    count: int = Field(description="Number of NACCID clinical records stored")
