from .protocols import router as protocols_router
from .case_mappings import router as case_mappings_router
from .slides import router as slides_router
from .collections import router as collections_router
from .patient_mappings import router as patient_mappings_router
from .block2region import router as block2region_router
from .dsa_sync import router as dsa_sync_router
from .admin import router as admin_router

__all__ = [
    "protocols_router",
    "case_mappings_router",
    "slides_router",
    "collections_router",
    "patient_mappings_router",
    "block2region_router",
    "dsa_sync_router",
    "admin_router",
]
