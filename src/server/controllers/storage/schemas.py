from pydantic import BaseModel, Field


class ShowBucket(BaseModel):
    name: str = Field(
        title="Bucket name",
        description="Name of the bucket",
        examples=["bucket1", "bucket2"],
    )
