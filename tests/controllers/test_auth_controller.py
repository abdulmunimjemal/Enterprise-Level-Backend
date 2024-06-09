import pytest
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Session, select

from db.models.user import User
from server.controllers.auth.auth_controller import AuthController
from server.controllers.auth.schemas import (
    CreateUser
)
from src.db.session import async_get_db


@pytest.mark.anyio
async def test_can_create_a_user(session: AsyncSession):
    create_user: CreateUser = CreateUser(
        first_name="Ari",
        last_name="Lerner",
        username="ari@mood-me.com",
        password="s3cret"
    )
    res = await AuthController.create_user(create_user, session, False)
    # # Select from db
    # query = select(User).where(User.username == create_user.username)
    # db_res = await db.exec(query)
    # print(f"db_res: {db_res}")
    # assert False
