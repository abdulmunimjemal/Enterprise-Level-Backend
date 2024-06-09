from pydantic import BaseModel, Field
from datetime import datetime


class APIStatus(BaseModel):
    status: str = Field(
        title="Status", description="Status of the service", examples=["ok", "error"]
    )
    timestamp: datetime = Field(
        description="Timestamp of the response", examples=["2024-05-12T12:34:56.7892"]
    )
    version: str = Field(description="API version", examples=["0.1.0"])
    uptime: int = Field(description="System uptime in seconds", examples=[123456])
