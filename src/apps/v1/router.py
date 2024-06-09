from typing import List
from fastapi import APIRouter

from .ai.router import router as ai_router

router = APIRouter(prefix="/ai", tags=["ai"])
router.include_router(ai_router)
