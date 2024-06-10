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
    # Select from db
    query = select(User).where(User.username == create_user.username)
    db_res = await session.exec(query)
    found_user = db_res.first();
    assert found_user.username == create_user.username
    assert found_user.first_name == create_user.first_name
    assert found_user.last_name == create_user.last_name

@pytest.mark.anyio
async def test_cannot_create_a_user_with_existing_username(session: AsyncSession):
    # Create a user
    session.add(User(
        first_name="Ari",
        last_name="Lerner",
        username="ari@mood-me.com",
        hashed_password="s3cret"
    ))
    await session.commit()
    # Try to create a user with the same username
    with pytest.raises(Exception):
        create_user: CreateUser = CreateUser(
            first_name="Ari",
            last_name="Lerner",
            username="ari@mood-me.com",
            password="s3cret"
        )
        await AuthController.create_user(create_user, session, False)
    # Select from db
    