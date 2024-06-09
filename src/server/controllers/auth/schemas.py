from pydantic import BaseModel, ConfigDict, Field

class CreateUser(BaseModel):
    first_name: str = Field(...,description="First name")
    last_name: str = Field(..., description="Last name")
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username_or_email: str