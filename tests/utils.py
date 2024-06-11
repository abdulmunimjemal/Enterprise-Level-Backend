from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
import pytest
from httpx import Response
from starlette.testclient import TestClient
from passlib.context import CryptContext

from db.models.user import User

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
