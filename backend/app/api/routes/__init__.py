from .protocols import router as protocols_router
from .case_mappings import router as case_mappings_router
from .region_label_mappings import router as region_label_mappings_router
from .stain_label_mappings import router as stain_label_mappings_router
from .slides import router as slides_router
from .collections import router as collections_router
from .patient_mappings import router as patient_mappings_router
from .block2region import router as block2region_router
from .dsa_sync import router as dsa_sync_router
from .admin import router as admin_router
from .schemas import router as schemas_router
from .clinical import router as clinical_router

__all__ = [
    "protocols_router",
    "case_mappings_router",
    "region_label_mappings_router",
    "stain_label_mappings_router",
    "slides_router",
    "collections_router",
    "patient_mappings_router",
    "block2region_router",
    "dsa_sync_router",
    "admin_router",
    "schemas_router",
    "clinical_router",
]
