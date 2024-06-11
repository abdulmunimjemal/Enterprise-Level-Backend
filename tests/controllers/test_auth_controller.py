import pytest
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Session, select, delete
from passlib.context import CryptContext

from db.models.user import User
from server.controllers.auth.auth_controller import AuthController
from server.controllers.auth.schemas import (
    CreateUser,
    LoginUser
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.mark.anyio
async def test_can_create_a_user(session: AsyncSession):
    create_user: CreateUser = CreateUser(
        first_name="Ari",
        last_name="Lerner",
        email="ari@mood-me.com",
        password="s3cret"
    )
    res = await AuthController.create_user(session, create_user, False)
    # Select from db
    query = select(User).where(User.email == create_user.email)
    db_res = await session.exec(query)
    found_user = db_res.first();
    assert found_user.email == create_user.email
    assert found_user.first_name == create_user.first_name
    assert found_user.last_name == create_user.last_name

@pytest.mark.anyio
async def test_create_duplicate_user(session: AsyncSession):
    # no users with duplicate emails or emails shall be created
    user = CreateUser(email="test", password="test")
    res = await AuthController.create_user(session, user, False)
    print(f"res: {res}")
    with pytest.raises(Exception):
        created_user = await AuthController.create_user(session, user, False)
        print(f"created_user: {created_user}")

    user3 = CreateUser(email="test", password="test")
    with pytest.raises(Exception):
        await AuthController.create_user(session, user3, False)

    # check if the second user was not created
    query = await session.exec(select(User).where(User.email == user.email))
    assert len(query.fetchall()) == 1
    
@pytest.mark.anyio
async def test_can_delete_a_user(session: AsyncSession):
    # Create a user
    session.add(User(
        first_name="Ari",
        last_name="Lerner",
        email="ari@mood-me.com",
        hashed_password=pwd_context.hash("s3cret")
    ))
    res = await AuthController.delete_user(session, "ari@mood-me.com")    
    assert res is True

@pytest.mark.anyio
async def test_cannot_delete_a_user_that_does_not_exist(session: AsyncSession):
    with pytest.raises(Exception):
        await AuthController.delete_user(session, "not_a_user@mood-me.com")

@pytest.mark.anyio
async def test_can_authenticate_a_user(
    session: AsyncSession
):

    hashed_password = pwd_context.hash("s3cret")
    create_user = User(
        first_name="Ari",
        last_name="Lerner",
        email="ari@mood-me.com",
        hashed_password=hashed_password
    )
    session.add(create_user)
    login_user: LoginUser = LoginUser(
        email=create_user.email,
        password="s3cret"
    )
    res = await AuthController.authenticate_user(session, login_user)
    assert res is not None

@pytest.mark.anyio
async def test_authenticate_user(session: AsyncSession):
    hashed_password = pwd_context.hash("test")
    user = User(
        first_name="Ari",
        last_name="Lerner",
        email="ari@mood-me.com",
        hashed_password=hashed_password
    )
    session.add(user)

    auth_user = await AuthController.authenticate_user(session, LoginUser(
        email="ari@mood-me.com",
        password="test"
    ))

    # check if the auth user matches the user
    assert auth_user.id == user.id
    assert auth_user.email == user.email
    assert auth_user.email == user.email

    auth_user = await AuthController.authenticate_user(session, LoginUser(
        email="joedoe@gmail.com",
        password="easy-pw-123"
    ))
    assert auth_user is None


@pytest.mark.anyio
async def test_authenticate_unexistant_user(session: AsyncSession):
    auth_user = await AuthController.authenticate_user(session, LoginUser(
        email="test1@gmail.com",
        password="test"
    ))
    assert auth_user is None

@pytest.mark.anyio
async def test_create_access_token(session: AsyncSession, user: User):
    token = await AuthController.create_access_token(user)
    assert token is not None

@pytest.mark.anyio
async def test_get_current_user_with_token(session: AsyncSession, user: User):
    token = await AuthController.create_access_token(user)
    print(f"token: {token}")
    assert token is not None
    user = await AuthController.get_current_user(session, token)
    assert user is not None

