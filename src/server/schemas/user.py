from pydantic import BaseModel, ConfigDict, Field

class User(BaseModel):
    first_name: str = Field(...,description="First name")
    last_name: str = Field(..., description="Last name")
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")