from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID

class CreateUser(BaseModel):
    first_name: str | None = Field(default=None, description="First name")
    last_name: str | None = Field(default=None, description="Last name")
    email: str | None = Field(default=None, description="Email")
    password: str = Field(..., description="Password")

class UserResponse(BaseModel):
    first_name: str
    last_name: str
    email: str

class LoginUser(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username_or_email: str