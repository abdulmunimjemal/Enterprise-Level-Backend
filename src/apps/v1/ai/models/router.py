from typing import List
from fastapi import APIRouter, status

from .schemas import ShowModel

router = APIRouter(prefix="/models", tags=["ai"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    responses={200: {"description": "List available models", "model": ShowModel}},
    response_model=List[ShowModel],
)
async def list_models() -> List[ShowModel]:
    return []
