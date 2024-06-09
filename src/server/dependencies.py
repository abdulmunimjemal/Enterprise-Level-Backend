from typing import Annotated
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from .schemas import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    return User(
        first_name="Ari",
        last_name="Lerner",
        username="ari@mood-me.com",
        password="s3cr3t"
    )