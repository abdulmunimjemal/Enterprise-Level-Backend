import pytest
from src.server.controllers.ai.models.model_controller import ModelController
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Session, select, delete

from db.models import (
    User,
    AiModel
)
from src.server.controllers.ai.models.schemas import (
    CreateModel,
)

@pytest.mark.asyncio
async def test_create_model(session: AsyncSession):
    create_model: CreateModel = CreateModel(name="test", description="test", url_or_path="http://test.com/test")

    model_response = await ModelController.create_model(session, create_model)
    print(model_response)
    assert model_response is not None
    assert model_response.name == "test"
    assert model_response.description == "test"
    assert model_response.url_or_path == "http://test.com/test"

    query = select(AiModel).where(AiModel.name == create_model.name)
    resp = await session.exec(query)
    model = resp.first()
    assert model is not None
    assert model.name == "test"
    assert model.description == "test"
    assert model.url_or_path == "http://test.com/test"

@pytest.mark.asyncio
async def test_duplicate_model_with_same_version(session: AsyncSession, aimodel: AiModel):
    create_model: CreateModel = CreateModel(name="test", description="test", url_or_path="test", version="0.0.1")
    with pytest.raises(Exception):
        await ModelController.create_model(session, create_model)
    
    with pytest.raises(Exception):
        await ModelController.create_model(session, CreateModel(
            name="test",
            description="test",
            url_or_path="\\bob",
            version="0.0.1"
        ))
    
@pytest.mark.asyncio
async def test_get_models(session: AsyncSession, aimodel: AiModel, user: User):
    models = await ModelController.get_models(session, user)
    assert len(models) == 1
    assert models[0].name == "test"
    await ModelController.create_model(session, CreateModel(
        name="test2",
        description="test2",
        url_or_path="http://test2.com/test2",
        version="0.0.1"
    ))
    models = await ModelController.get_models(session, user)
    assert len(models) == 2
    assert models[1].name == "test2"

@pytest.mark.asyncio
async def test_delete_model(session: AsyncSession, aimodel: AiModel):
    print(f"aimodel: {aimodel}")
    await ModelController.delete_model(session, aimodel.name)
    query = select(AiModel).where(AiModel.name == aimodel.name)
    resp = await session.exec(query)
    model = resp.first()
    assert model is None

