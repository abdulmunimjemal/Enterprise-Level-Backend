from typing import Optional, List
from sqlmodel import Field, Relationship

from core.common import (
    SoftDeleteMixin,
    UUIDMixin,
    Base,
    TimestampMixin
)

class User(
    Base,
    UUIDMixin,
    TimestampMixin,
    SoftDeleteMixin,
    table=True
):
    __tablename__ = "users"
    # __table_args__ = {'extend_existing': True}

    first_name: Optional[str] = Field(default=None, max_length=255)
    last_name: Optional[str] = Field(default=None, max_length=255)
    username: Optional[str] = Field(default=None, max_length=255)
    hashed_password: str = Field(
        nullable=False, description="Hashed password for user auth"
    )

