import pytest
from typing import Generator, AsyncGenerator, AsyncIterator
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    create_async_engine,
    AsyncTransaction,
)
from sqlalchemy.orm import sessionmaker
from sqlmodel.pool import StaticPool
from sqlmodel.ext.asyncio.session import AsyncSession
from httpx import AsyncClient, ASGITransport

from starlette.testclient import TestClient

from src import app
from src.core.config import Settings, get_settings
from src.core.models import Base
from src.db.session import get_async_db

from .utils import user, aimodel

# test_async_engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool, echo=False)
test_async_engine = create_async_engine(
    "sqlite+aiosqlite://", 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool,
    echo=False
)

@pytest.fixture(scope="session", params=["asyncio"])
def anyio_backend(request):
    return request.param


@pytest.fixture(scope="function")
async def connection(anyio_backend) -> AsyncGenerator[AsyncConnection, None]:
    async with test_async_engine.connect() as connection:
        yield connection


@pytest.fixture(scope="function")
async def transaction(
    connection: AsyncConnection,
) -> AsyncGenerator[AsyncTransaction, None]:
    async with connection.begin() as transaction:
        yield transaction


@pytest.fixture(scope="function")
async def session(
    connection: AsyncConnection,
    transaction: AsyncTransaction
) -> AsyncGenerator[AsyncSession, None]:
    async_session_factory = sessionmaker(test_async_engine, class_=AsyncSession, expire_on_commit=False)
    session = async_session_factory()
    try:
        await connection.run_sync(Base.metadata.create_all)
        yield session
    finally:
        await session.close()
        await connection.run_sync(Base.metadata.drop_all)

class TestSettings(Settings):
    STORAGE_PATH: str = "/tmp/tests"

@pytest.fixture(scope="function")
async def client(
    app,
    connection: AsyncConnection,
     session: AsyncGenerator[AsyncSession, None]
) -> AsyncIterator[AsyncClient]:

    transport = ASGITransport(app=app)
    async_client = AsyncClient(transport=transport, base_url="http://testserver")

    app.dependency_overrides[get_async_db] = lambda: session
    app.dependency_overrides[get_settings] = lambda: TestSettings()

    await app.router.startup()

    try:
        yield async_client
    finally:
        await async_client.aclose()
        app.dependency_overrides.clear()
        await app.router.shutdown()


@pytest.fixture(scope="session")
async def app():
    from src.main import app

    return app
