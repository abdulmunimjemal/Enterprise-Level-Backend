from typing import Annotated, Dict, List
from fastapi import APIRouter, Depends, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_async_db
from server.controllers.ai.models.model_controller import ModelController
from server.controllers.ai.models.schemas import CreateModel, ModelResponse

router = APIRouter(prefix="/models", tags=["ai"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    responses={200: {"description": "List available models", "model": ModelResponse}},
    response_model=List[ModelResponse],
)
async def list_models(
    db: Annotated[AsyncSession, Depends(get_async_db)],
) -> List[ModelResponse]:
    return await ModelController.get_models(db)

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses={201: {"description": "Create a new model", "model": ModelResponse}},
    response_model=ModelResponse,
)
async def create_model(
    db: Annotated[AsyncSession, Depends(get_async_db)],
    create_model: CreateModel,
    file: Annotated[bytes, File()],
) -> ModelResponse:
    return await ModelController.create_model(db, create_model, file)

@router.delete(
    "/{model_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={204: {"description": "Delete a model"}},
)
async def delete_model(
    db: Annotated[AsyncSession, Depends(get_async_db)],
    model_id: str,
) -> None:
    return await ModelController.delete_model(db, model_id)
