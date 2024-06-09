from pydantic import BaseModel, Field
from datetime import datetime


class ShowModel(BaseModel):
    name: str = Field(
        title="Model name",
        description="Name of the model",
        examples=["model1", "model2"],
    )
    version: str = Field(
        title="Model version",
        description="Version of the model",
        examples=["0.1.0"],
    )
