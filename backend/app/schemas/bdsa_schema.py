"""Pydantic models for BDSA JSON schema API responses."""
from typing import Any

from pydantic import BaseModel, Field


class SchemaSummary(BaseModel):
    id: str = Field(description="Short schema id (clinical, region, stain, slide)")
    filename: str
    title: str
    url: str = Field(description="GET path under /api/schemas/{id}")


class SchemasListResponse(BaseModel):
    schemas: list[SchemaSummary]
    combined_url: str = "/api/schemas/combined"
    source: str = "pitt-bdsa/bdsa girder_bdsa/schemas"


class CombinedSchemaResponse(BaseModel):
    clinicalMetadata: dict[str, Any]
    regionMetadata: dict[str, Any]
    stainMetadata: dict[str, Any]
    slideLevelMetadata: dict[str, Any]
