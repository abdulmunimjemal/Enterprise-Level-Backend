from typing import Tuple
from io import BytesIO
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
import pytest
from httpx import Response
from starlette.testclient import TestClient
from passlib.context import CryptContext
from os import path
from fastapi import UploadFile, File

from db.models.user import User
from db.models.ai_models import AiModel

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def make_request(client: TestClient, endpoint: str) -> Response:
    return client.get(endpoint)


@pytest.fixture(scope="function")
async def user(session: AsyncSession) -> User:
    hashed_password = pwd_context.hash("test")
    session.add(User(
        first_name="Ari",
        last_name="Lerner",
        email="ari@mood-me.com",
        hashed_password=hashed_password
    ))
    await session.commit()
    user = await session.exec(select(User).where(User.email == "ari@mood-me.com"))
    user = user.first()
    return user


@pytest.fixture(scope='function')
def fixture_path() -> str:
    return path.join(path.dirname(__file__), "fixtures")


@pytest.fixture(scope='function')
async def model_file_bytes(fixture_path: str) -> BytesIO:
    with open(path.join(fixture_path, "gender-test.zip"), "rb") as f:
        data = f.read()
    return BytesIO(data)


@pytest.fixture(scope='function')
def model_file(model_file_bytes: BytesIO) -> File:
    return File(model_file_bytes, filename="gender-test.zip", media_type="application/zip")


@pytest.fixture(scope="function")
async def aimodel(session: AsyncSession, model_file: File) -> AiModel:
    session.add(AiModel(
        name="test",
        description="test",
        url_or_path="http://test.com/test",
        version="0.0.1",
        sha256="TODO",
    ))
    await session.commit()
    query = select(AiModel).where(AiModel.name == "test")
    res = await session.exec(query)
    return res.first()
