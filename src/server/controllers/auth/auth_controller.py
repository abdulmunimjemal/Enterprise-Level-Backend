from typing import Annotated, Dict
from sqlmodel.ext.asyncio.session import AsyncSession
# from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose.exceptions import JWTError
from passlib.context import CryptContext
from sqlmodel import Session, select

from db.models.user import User
from core.config import get_settings

# from db.session import async_get_db
from server.dependencies import oauth2_scheme

from .schemas import CreateUser

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = settings.JWT_SECRET_KEY
EXPIRATION_MINUTES = settings.JWT_EXPIRATION_MINUTES

class AuthController:

    @staticmethod
    async def create_user(
        create_user: CreateUser,
        db: AsyncSession,
        oauth: bool = False
    ) -> User:
        """
        Create a new user in the users table
        """
        # db = async_get_db()
        # Does the user already exist?
        query = select(User).where(User.username == create_user.username)
        res = await db.exec(query)
        if res.first():
            raise Exception("Email already exists")

        hashed_password = pwd_context.hash(create_user.password) if not oauth else None
        db_user = User(
            username=create_user.username,
            first_name=create_user.first_name,
            last_name=create_user.last_name,
            hashed_password=hashed_password
        )
        db.add(db_user)
        return db_user