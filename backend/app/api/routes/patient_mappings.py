"""API routes for localPatientId <-> BDSA-Patient-ID mappings."""
from typing import Any

from fastapi import APIRouter, Query

from app.db.repositories import (
    get_patient_id_mappings,
    set_patient_id_mappings,
    merge_patient_id_mappings,
)
from app.schemas.patient_mappings import (
    PatientIdMappingsPayload,
    PatientIdMappingsResponse,
)

router = APIRouter(
    prefix="/collections/{collection_id}/patient-id-mappings",
    tags=["patient-id-mappings"],
)


@router.get("", response_model=PatientIdMappingsResponse)
async def get_collection_patient_id_mappings(
    collection_id: str,
    local_patient_id: str | None = Query(
        None,
        alias="localPatientId",
        description="If set, return only the mapping for this localPatientId",
    ),
) -> PatientIdMappingsResponse:
    """Get patient ID mappings (localPatientId with optional bdsaPatientId) for a collection.
    Use ?localPatientId=xyz to look up a single mapping.
    """
    data = await get_patient_id_mappings(collection_id)
    if data is None:
        return PatientIdMappingsResponse(
            collection_id=collection_id,
            patientIdMappings=None,
        )
    mappings = data.get("mappings", [])
    if local_patient_id is not None:
        mappings = [m for m in mappings if m.get("localPatientId") == local_patient_id]
    payload = PatientIdMappingsPayload(
        institutionId=data.get("institutionId", "001"),
        mappings=mappings,
        lastUpdated=data.get("lastUpdated"),
        source=data.get("source", "BDSA-Schema-Wrangler"),
        version=data.get("version", "1.0"),
        totalMappings=len(mappings),
    )
    return PatientIdMappingsResponse(
        collection_id=collection_id,
        patientIdMappings=payload,
    )


@router.put("", response_model=PatientIdMappingsResponse)
async def put_collection_patient_id_mappings(
    collection_id: str, body: PatientIdMappingsPayload
) -> PatientIdMappingsResponse:
    """Replace all patient ID mappings for a collection."""
    payload: dict[str, Any] = {
        "institutionId": body.institutionId,
        "mappings": [m.model_dump() for m in body.mappings],
        "totalMappings": len(body.mappings),
        "source": body.source,
        "version": body.version,
    }
    stored = await set_patient_id_mappings(collection_id, payload)
    return PatientIdMappingsResponse(
        collection_id=collection_id,
        patientIdMappings=PatientIdMappingsPayload(
            institutionId=stored.get("institutionId", "001"),
            mappings=stored.get("mappings", []),
            lastUpdated=stored.get("lastUpdated"),
            source=stored.get("source", "BDSA-Schema-Wrangler"),
            version=stored.get("version", "1.0"),
            totalMappings=stored.get("totalMappings", 0),
        ),
    )


@router.post("/merge", response_model=PatientIdMappingsResponse)
async def merge_collection_patient_id_mappings(
    collection_id: str, body: PatientIdMappingsPayload
) -> PatientIdMappingsResponse:
    """Merge patient ID mappings with existing (by localPatientId)."""
    stored = await merge_patient_id_mappings(
        collection_id,
        [m.model_dump() for m in body.mappings],
        body.institutionId,
    )
    return PatientIdMappingsResponse(
        collection_id=collection_id,
        patientIdMappings=PatientIdMappingsPayload(
            institutionId=stored.get("institutionId", "001"),
            mappings=stored.get("mappings", []),
            lastUpdated=stored.get("lastUpdated"),
            source=stored.get("source", "BDSA-Schema-Wrangler"),
            version=stored.get("version", "1.0"),
            totalMappings=stored.get("totalMappings", 0),
        ),
    )
