from fastapi import APIRouter

from app.api.v1.endpoints.briefs import router as briefs_router
from app.api.v1.endpoints.health import router as health_router

router = APIRouter()

router.include_router(health_router)
router.include_router(briefs_router)

