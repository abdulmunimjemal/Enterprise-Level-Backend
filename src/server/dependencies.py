from typing import Annotated
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from .schemas import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

