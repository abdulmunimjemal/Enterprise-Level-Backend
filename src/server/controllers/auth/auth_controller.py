from typing import Annotated, Dict
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Depends
# from fastapi.security import OAuth2PasswordBearer
import requests
from jose import jwt
from jose.exceptions import JWTError
from passlib.context import CryptContext
from sqlmodel import Session, select, delete
from datetime import datetime, timedelta

from db.session import get_async_db
from db.models.user import User
from core.config import get_settings

# from db.session import get_async_db
from server.dependencies import oauth2_scheme

from .schemas import (
    CreateUser,
    UserResponse,
    LoginUser
)

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = settings.JWT_SECRET_KEY
EXPIRATION_MINUTES = settings.JWT_EXPIRATION_MINUTES

class AuthController:

    @staticmethod
    async def create_user(
        db: AsyncSession,
        create_user: CreateUser,
        oauth: bool = False
    ) -> User:
        """
        Create a new user in the users table
        """
        # db = get_async_db()
        # Does the user already exist?
        query = select(User).where(User.email == create_user.email)
        res = await db.exec(query)                      
        found_user = res.first()
        if found_user:
            raise Exception("Email already exists")

        hashed_password = pwd_context.hash(create_user.password) if not oauth else None
        db_user = User(
            email=create_user.email,
            first_name=create_user.first_name,
            last_name=create_user.last_name,
            hashed_password=hashed_password
        )
        db.add(db_user)
        return db_user

    @staticmethod
    async def delete_user(
        db: AsyncSession,
        email: str,
    ) -> None:
        """
        Delete a user from the users table
        """
        query = select(User).where(User.email == email)
        user = await db.exec(query)
        user = user.first()
        if not user:
            raise Exception("User not found")
        await db.delete(user)
        return True

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        login_user: LoginUser,
    ) -> User:
        """
        Authenticate a user
        """
        query = select(User).where(User.email == login_user.email)
        user = await db.exec(query)
        user = user.first()
        print(f"found_user: {user}")
        if not user:
            return None
        print(f"verifying password {pwd_context.verify(login_user.password, user.hashed_password)}")
        if not pwd_context.verify(login_user.password, user.hashed_password):
            return None
        print("returning user")
        return user

    @staticmethod
    async def create_access_token(user: User):
        expire = datetime.now() + timedelta(minutes=EXPIRATION_MINUTES)
        public_user = UserResponse.model_validate(user.model_dump(mode="json"))
        to_encode = {"exp": expire, "sub": user.email, "user": public_user.model_dump(mode="json")}
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
        return encoded_jwt


async def get_current_user(
    db: AsyncSession = Depends(get_async_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    # first try to decode the token using our auth
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            raise Exception("Could not validate credentials")

        user = await db.exec(select(User).where(User.email == email))
        user = user.first()
        if user is None:
            raise Exception("Could not validate credentials")

    # if the token is not from our auth, try to decode it using facebook auth
    except JWTError:
        try:
            user = await AuthController.get_facebook_user(token) or await AuthController.get_google_user(token)
            return user
        except Exception:
            raise Exception("Could not validate credentials")

    return user

async def get_facebook_user(token: str):
    pass

async def get_google_user(token: str):
    pass

