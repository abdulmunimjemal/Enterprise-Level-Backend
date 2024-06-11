from typing import Annotated, Dict
from datetime import datetime, timezone
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import APIRouter, Request, Depends
from fastapi.exceptions import HTTPException

from fastapi.security import OAuth2PasswordRequestForm
from server.dependencies import oauth2_scheme

from core.config import get_settings
from db.session import get_async_db
from server.controllers.auth.auth_controller import AuthController, get_current_user

from db.models import User
from server.controllers.auth.schemas import (
    Token,
    CreateUser,
    LoginUser,
    UserResponse
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=User)
async def signup(
    create_user: CreateUser,
    db: Annotated[AsyncSession, Depends(get_async_db)],
) -> Dict[str, str]:
    try:
        user = await AuthController.create_user(db, create_user)
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail="User already exists")

@router.post("/token", response_model=Token)
async def login(
    db: Annotated[AsyncSession, Depends(get_async_db)],
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Dict[str, str]:
    login_user = LoginUser(
        email=form_data.username,
        password=form_data.password,
    )
    user = await AuthController.authenticate_user(db, login_user)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = await AuthController.create_access_token(user)
    return Token(access_token=access_token, token_type="bearer")

@router.get("/me", response_model=UserResponse)
async def me(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> User:
    return current_user

