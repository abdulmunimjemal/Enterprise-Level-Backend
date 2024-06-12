from typing import Optional, Dict
from sqlmodel import Field
from sqlalchemy import JSON, Column



from src.core.common import (
    SoftDeleteMixin,
    UUIDMixin,
    Base,
    TimestampMixin
)

class AiModel(
    Base,
    UUIDMixin,
    TimestampMixin,
    SoftDeleteMixin,
    table=True
):
    name: str = Field(..., description="The name of the model")
    description: Optional[str] = Field(..., description="The description of the model")
    url_or_path: str = Field(..., description="The path to the model")
    version: str = Field(..., description="The version of the model")
    details: dict = Field(sa_column=Column(JSON), default={})




