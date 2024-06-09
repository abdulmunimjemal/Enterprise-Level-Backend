from typing import Annotated, Dict
from datetime import datetime, timezone
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import APIRouter, Request, Depends


from core.config import get_settings
from .schemas import Token, CreateUser
from db.session import async_get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=Token)
async def login_for_access_token(
    create_user: CreateUser,
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> Dict[str, str]:
    print(create_user)
    return Token(access_token="yay", token_type="email")