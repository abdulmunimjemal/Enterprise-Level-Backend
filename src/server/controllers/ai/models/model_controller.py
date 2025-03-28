from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from db.models.ai_models import AiModel
from utils.validators import is_valid_path_or_url, validate_uploaded_file
from fastapi import UploadFile, File
from typing import Optional, Dict, Annotated, List

from utils.net_utils import upload_from_file
from .schemas import (
    ModelResponse,
    CreateModel
)


class ModelController:
    @staticmethod
    async def get_models(db: AsyncSession) -> List[ModelResponse]:
        query = select(AiModel)
        models = await db.exec(query)
        return [ModelResponse(**model.model_dump()) for model in models]

    @staticmethod
    async def get_model_info(db: AsyncSession, model_name: str) -> ModelResponse:
        query = select(AiModel).where(AiModel.name == model_name)
        model = await db.exec(query)
        return ModelResponse(**model.model_dump())

    @staticmethod
    async def download_model(db: AsyncSession, model_name: str):
        # Blocking, for now
        pass

    @staticmethod
    async def create_model(db: AsyncSession, create_model: CreateModel, file: Annotated[bytes, File()]) -> ModelResponse:
        await validate_uploaded_file(file)
        query = select(AiModel).where(AiModel.name == create_model.name)
        model_resp = await db.exec(query)
        model = model_resp.first()
        if model and model.version == create_model.version:
            raise Exception("Model version already exists")

        if not is_valid_path_or_url(create_model.url_or_path):
            raise Exception("Invalid path or url")

        # TODO: Hash the file
        try:
            # Upload model first
            await upload_from_file(file, f"{create_model.name}-{create_model.version}.zip")
            model = AiModel(**create_model.model_dump(), sha256="TODO")
            db.add(model)
            await db.commit()
            return ModelResponse(**model.model_dump())
        except Exception as e:
            print(f"Error creating model: {e}")
            raise Exception("Failed to create model") from e

    @staticmethod
    async def delete_model(db: AsyncSession, model_name: str):
        query = select(AiModel).where(AiModel.name == model_name)
        model = await db.exec(query)
        if not model:
            raise Exception("Model not found")
        model = model.first()
        print(f"model: {model}")
        await db.delete(model)
        await db.commit()
        return {"message": "Model deleted"}
