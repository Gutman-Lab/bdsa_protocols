"""BDSA Protocols API - FastAPI application."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db import close_db, get_db
from app.api.routes import (
    protocols_router,
    case_mappings_router,
    slides_router,
    collections_router,
    patient_mappings_router,
    block2region_router,
    dsa_sync_router,
    admin_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure DB is available on startup and close on shutdown."""
    await get_db()
    yield
    await close_db()


app = FastAPI(
    title=settings.app_name,
    description="Canonical backend for BDSA region/stain protocols, case data, and slide stain info. Compatible with BDSA-Schema-Wrangler.",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(protocols_router, prefix="/api")
app.include_router(case_mappings_router, prefix="/api")
app.include_router(slides_router, prefix="/api")
app.include_router(collections_router, prefix="/api")
app.include_router(patient_mappings_router, prefix="/api")
app.include_router(block2region_router, prefix="/api")
app.include_router(dsa_sync_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


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
