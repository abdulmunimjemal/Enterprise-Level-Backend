import pytest
from typing import Generator, AsyncGenerator, AsyncIterator
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    create_async_engine,
    AsyncTransaction,
)
from sqlmodel.pool import StaticPool
from sqlmodel.ext.asyncio.session import AsyncSession
from httpx import AsyncClient, ASGITransport

from starlette.testclient import TestClient

from src import app
from src.core.config import Settings, get_settings


test_async_engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)


@pytest.fixture(scope="session", params=["asyncio"])
def anyio_backend(request):
    return "asyncio"


# @pytest.fixture(scope="session")
# async def connection(anyio_backend) -> AsyncGenerator[AsyncConnection, None]:
#     async with test_async_engine.connect() as connection:
#         yield connection


# @pytest.fixture(scope="session")
# async def transaction(
#     connection: AsyncConnection,
# ) -> AsyncGenerator[AsyncTransaction, None]:
#     async with connection.begin() as transaction:
#         yield transaction


class TestSettings(Settings):
    STORAGE_PATH: str = "/tmp/tests"


@pytest.fixture(scope="session")
async def client(
    app,
    # connection: AsyncConnection,
    #  session: AsyncGenerator[AsyncSession, None]
) -> AsyncIterator[AsyncClient]:

    transport = ASGITransport(app=app)
    async_client = AsyncClient(transport=transport, base_url="http://testserver")

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
