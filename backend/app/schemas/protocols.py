"""Pydantic schemas for stain and region protocols (wrangler-compatible)."""
from typing import Any

from pydantic import BaseModel, Field


class StainProtocolIn(BaseModel):
    """Single stain protocol (create/update)."""

    id: str | None = None
    name: str
    description: str | None = None
    stainType: str | None = None
    type: str = "stain"
    _localModified: bool | None = None
    _remoteVersion: str | None = None
    _isDefault: bool | None = None

    class Config:
        extra = "allow"
        populate_by_name = True


class RegionProtocolIn(BaseModel):
    """Single region protocol (create/update)."""

    id: str | None = None
    name: str
    description: str | None = None
    regionType: str | None = None
    type: str = "region"
    _localModified: bool | None = None
    _remoteVersion: str | None = None
    _isDefault: bool | None = None

    class Config:
        extra = "allow"
        populate_by_name = True


class BlockProtocolIn(BaseModel):
    """Block protocol: template mapping block IDs to region protocol ids."""

    id: str | None = None
    name: str
    description: str | None = None
    type: str = "block"
    slots: list[dict[str, str]] = Field(default_factory=list)
    _localModified: bool | None = None
    _remoteVersion: str | None = None
    _isDefault: bool | None = None

    class Config:
        extra = "allow"
        populate_by_name = True


class ProtocolsPayload(BaseModel):
    """Full protocols payload as used by BDSA-Schema-Wrangler."""

    stainProtocols: list[dict[str, Any]] = Field(default_factory=list)
    regionProtocols: list[dict[str, Any]] = Field(default_factory=list)
    blockProtocols: list[dict[str, Any]] = Field(default_factory=list)
    lastUpdated: str | None = None
    source: str = "BDSA-Schema-Wrangler"
    version: str = "1.0"

    class Config:
        extra = "allow"


class ProtocolsResponse(BaseModel):
    """Response for GET protocols."""

    success: bool = True
    collection_id: str
    protocols: ProtocolsPayload
