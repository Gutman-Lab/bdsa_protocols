"""API routes for NACC clinical data keyed by NACCID."""
from fastapi import APIRouter, HTTPException

from app.db.clinical_repository import get_clinical_by_nacc, get_clinical_stats
from app.schemas.clinical import ClinicalByNaccResponse, ClinicalStatsResponse

router = APIRouter(prefix="/clinical", tags=["clinical"])


@router.get("/stats", response_model=ClinicalStatsResponse)
async def clinical_stats() -> ClinicalStatsResponse:
    """Return count of stored NACC clinical records."""
    stats = await get_clinical_stats()
    return ClinicalStatsResponse(count=stats["count"])


@router.get("/by-nacc/{naccid}", response_model=ClinicalByNaccResponse)
async def get_clinical_for_nacc(naccid: str) -> ClinicalByNaccResponse:
    """Get clinical-schema fields for a NACCID (404 if not loaded)."""
    doc = await get_clinical_by_nacc(naccid)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"No clinical data for NACCID {naccid}")
    return ClinicalByNaccResponse(
        naccid=doc["naccid"],
        clinical=doc.get("clinical") or {},
        source=doc.get("source"),
        visitMeta=doc.get("visitMeta"),
        lastUpdated=doc.get("lastUpdated"),
    )
