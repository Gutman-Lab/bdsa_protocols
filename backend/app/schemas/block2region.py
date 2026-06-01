"""Pydantic schemas for block->region map per case."""
from typing import Any

from pydantic import BaseModel, Field

# Case-level status (like validated): whole case can be set aside or not yet scanned
CASE_STATUS_SKIP = "SKIP"
CASE_STATUS_NEEDS_RESEARCH = "NEEDS_RESEARCH"
CASE_STATUS_NOT_SCANNED = "NOT_SCANNED"
CASE_STATUS_VALUES = (CASE_STATUS_SKIP, CASE_STATUS_NEEDS_RESEARCH, CASE_STATUS_NOT_SCANNED)

# Per-block status in block2region map (value = region id or one of these)
BLOCK2REGION_STATUS_SKIP = "SKIP"
BLOCK2REGION_STATUS_NEEDS_RESEARCH = "NEEDS_RESEARCH"
BLOCK2REGION_STATUS_NOT_SCANNED = "NOT_SCANNED"
BLOCK2REGION_STATUS_VALUES = (
    BLOCK2REGION_STATUS_SKIP,
    BLOCK2REGION_STATUS_NEEDS_RESEARCH,
    BLOCK2REGION_STATUS_NOT_SCANNED,
)


class Block2RegionPayload(BaseModel):
    """Block ID -> region ID or status map for a single case."""

    case_id: str | None = None  # optional on PUT; path provides it
    block2region: dict[str, str] = Field(
        default_factory=dict,
        description="Map of block ID to region id or status: SKIP / NEEDS_RESEARCH (come back later), NOT_SCANNED (not yet scanned)",
    )
    mapping_source: str | None = Field(
        default=None,
        description="Origin of the mapping, e.g. 'LLM', 'manual', 'import'",
    )
    validated: bool = Field(
        default=False,
        description="Whether this mapping has been validated (e.g. by human review)",
    )
    case_status: str | None = Field(
        default=None,
        description="Case-level status: SKIP / NEEDS_RESEARCH / NOT_SCANNED (set aside or not yet scanned)",
    )
    lastUpdated: str | None = None
    source: str = "BDSA-Schema-Wrangler"
    version: str = "1.0"

    class Config:
        extra = "allow"


class Block2RegionCaseEntry(BaseModel):
    """One case's block2region plus metadata (for collection response)."""

    block2region: dict[str, str] = Field(default_factory=dict)
    mapping_source: str | None = None
    validated: bool = False
    case_status: str | None = None
    lastUpdated: str | None = None


class Block2RegionResponse(BaseModel):
    """Response for GET block2region for a case."""

    success: bool = True
    collection_id: str
    case_id: str
    block2region: Block2RegionPayload | None


class Block2RegionCollectionResponse(BaseModel):
    """Response for GET all block2region in a collection."""

    success: bool = True
    collection_id: str
    by_case: dict[str, Block2RegionCaseEntry] = Field(
        default_factory=dict,
        description="case_id -> { block2region, mapping_source?, validated?, lastUpdated? }",
    )


class Block2RegionVersionEntry(BaseModel):
    """One versioned snapshot (for list response)."""

    version: int
    block2region: dict[str, str] = Field(default_factory=dict)
    mapping_source: str | None = None
    validated: bool = False
    case_status: str | None = None
    createdAt: str | None = None

    class Config:
        extra = "allow"


class Block2RegionVersionsResponse(BaseModel):
    """Response for GET block2region/versions."""

    success: bool = True
    collection_id: str
    case_id: str
    versions: list[Block2RegionVersionEntry]


class Block2RegionRestoreRequest(BaseModel):
    """Body for POST block2region/restore."""

    version: int
