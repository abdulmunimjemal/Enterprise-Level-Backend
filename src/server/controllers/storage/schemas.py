from typing import Optional
from pydantic import BaseModel, Field


class ShowBucket(BaseModel):
    name: str = Field(
        title="Bucket name",
        description="Name of the bucket",
        examples=["bucket1", "bucket2"],
    )

class ModelResponse(BaseModel):
    name: str = Field(..., description="The name of the model")
    description: Optional[str] = Field(..., description="The description of the model")
    version: str = Field(..., description="The version of the model")
    details: dict = Field(..., description="The details of the model")

