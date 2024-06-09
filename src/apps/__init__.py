from fastapi import APIRouter

from .health.router import router as health_router
from .auth.router import router as auth_router
from .v1.router import router as v1_router

router = APIRouter()
router.include_router(v1_router)
router.include_router(health_router)
router.include_router(auth_router)