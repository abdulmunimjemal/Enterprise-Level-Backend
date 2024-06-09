from typing import List
from fastapi import APIRouter, status

from .models.router import router as models_router

router = APIRouter(prefix="", tags=["ai"])
router.include_router(models_router)
