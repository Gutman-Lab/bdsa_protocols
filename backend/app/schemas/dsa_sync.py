"""Schemas for DSA/Girder sync endpoint."""
from pydantic import BaseModel, Field


class DsaSyncRequest(BaseModel):
    """Body for POST sync from Girder."""

    girder_folder_id: str = Field(
        ...,
        description="Girder folder ID (root folder whose subfolders are patient/case folders)",
    )


class DsaSyncResponse(BaseModel):
    """Response after syncing from Girder."""

    success: bool = True
    collection_id: str
    girder_folder_id: str
    total_items: int
    case_count: int
