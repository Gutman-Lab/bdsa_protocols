"""BDSA Protocols API - FastAPI application."""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.security import log_api_key_status, require_api_key
from app.services.case_id_validation import CaseIdMappingError
from app.services.region_label_validation import RegionLabelMappingError
from app.services.stain_label_validation import StainLabelMappingError
from app.db import close_db, get_db
from app.api.routes import (
    protocols_router,
    case_mappings_router,
    region_label_mappings_router,
    stain_label_mappings_router,
    slides_router,
    collections_router,
    patient_mappings_router,
    block2region_router,
    dsa_sync_router,
    admin_router,
    schemas_router,
)

API_ROUTERS = [
    protocols_router,
    case_mappings_router,
    region_label_mappings_router,
    stain_label_mappings_router,
    slides_router,
    collections_router,
    patient_mappings_router,
    block2region_router,
    dsa_sync_router,
    admin_router,
    schemas_router,
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure DB is available on startup and close on shutdown."""
    log_api_key_status()
    await get_db()
    yield
    await close_db()


app = FastAPI(
    title=settings.app_name,
    description="Canonical backend for BDSA region/stain protocols, case data, and slide stain info. Compatible with BDSA-Schema-Wrangler.",
    version="0.1.0",
    lifespan=lifespan,
)


def _mapping_error_response(
    exc: CaseIdMappingError | RegionLabelMappingError | StainLabelMappingError,
) -> JSONResponse:
    content: dict[str, object] = {"detail": exc.message}
    if exc.conflict:
        content["conflict"] = exc.conflict
    return JSONResponse(status_code=exc.http_status, content=content)


@app.exception_handler(CaseIdMappingError)
async def case_id_mapping_error_handler(
    _request: Request, exc: CaseIdMappingError
) -> JSONResponse:
    return _mapping_error_response(exc)


@app.exception_handler(RegionLabelMappingError)
async def region_label_mapping_error_handler(
    _request: Request, exc: RegionLabelMappingError
) -> JSONResponse:
    return _mapping_error_response(exc)


@app.exception_handler(StainLabelMappingError)
async def stain_label_mapping_error_handler(
    _request: Request, exc: StainLabelMappingError
) -> JSONResponse:
    return _mapping_error_response(exc)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in API_ROUTERS:
    app.include_router(router, prefix="/api", dependencies=[Depends(require_api_key)])


@app.get("/")
async def root() -> dict[str, str]:
    """Root redirect to docs."""
    return {
        "service": settings.app_name,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check for Docker/load balancers."""
    return {"status": "ok"}
