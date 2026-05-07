from fastapi import APIRouter

from app.api.v1.endpoints.briefs import router as briefs_router
from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.users import router as users_router
from app.api.v1.sources import router as sources_router
from app.api.v1.research_scopes import router as research_scopes_router

router = APIRouter()

router.include_router(health_router)
router.include_router(briefs_router)
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(sources_router)
router.include_router(research_scopes_router)

