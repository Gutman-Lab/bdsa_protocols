"""Serve Pitt BDSA split JSON schemas via the API."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse

from app.schemas.bdsa_schema import CombinedSchemaResponse, SchemaSummary, SchemasListResponse

router = APIRouter(prefix="/schemas", tags=["schemas"])

_SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "data" / "schemas"

_SCHEMA_REGISTRY: dict[str, tuple[str, str]] = {
    "clinical": ("clinical-metadata.json", "Clinical metadata"),
    "region": ("region-metadata.json", "Region metadata"),
    "stain": ("stain-metadata.json", "Stain metadata"),
    "slide": ("slide-level-metadata.json", "Slide-level metadata"),
    "case-id-mappings": ("case-id-mappings.json", "Case ID mappings registry"),
}

_COMBINED_KEYS = {
    "clinical": "clinicalMetadata",
    "region": "regionMetadata",
    "stain": "stainMetadata",
    "slide": "slideLevelMetadata",
}


def _schema_path(schema_id: str) -> Path:
    entry = _SCHEMA_REGISTRY.get(schema_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Unknown schema id: {schema_id}")
    path = _SCHEMAS_DIR / entry[0]
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"Schema file not found: {entry[0]}")
    return path


def _load_schema(schema_id: str) -> dict[str, Any]:
    path = _schema_path(schema_id)
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("", response_model=SchemasListResponse)
async def list_schemas() -> SchemasListResponse:
    """List available BDSA JSON schema documents."""
    summaries = [
        SchemaSummary(
            id=schema_id,
            filename=filename,
            title=title,
            url=f"/api/schemas/{schema_id}",
        )
        for schema_id, (filename, title) in _SCHEMA_REGISTRY.items()
    ]
    return SchemasListResponse(schemas=summaries)


@router.get("/combined", response_model=CombinedSchemaResponse)
async def get_combined_schema() -> CombinedSchemaResponse:
    """Return all split schemas merged for flattened / CDE views."""
    parts = {key: _load_schema(schema_id) for schema_id, key in _COMBINED_KEYS.items()}
    return CombinedSchemaResponse(
        clinicalMetadata=parts["clinicalMetadata"],
        regionMetadata=parts["regionMetadata"],
        stainMetadata=parts["stainMetadata"],
        slideLevelMetadata=parts["slideLevelMetadata"],
    )


@router.get("/{schema_id}", response_model=None)
async def get_schema(
    schema_id: str,
    download: bool = Query(False, description="If true, return as attachment download"),
) -> JSONResponse | FileResponse:
    """Get one BDSA JSON schema by id (clinical, region, stain, slide)."""
    path = _schema_path(schema_id)
    if download:
        return FileResponse(
            path,
            media_type="application/json",
            filename=path.name,
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    return JSONResponse(content=data)
