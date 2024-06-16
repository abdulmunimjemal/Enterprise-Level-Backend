from fastapi import UploadFile, File
from typing import Optional, Dict, Annotated
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID

class ModelResponse(BaseModel):
    name: str = Field(..., description="The name of the model")
    description: Optional[str] = Field(..., description="The description of the model")
    url_or_path: str = Field(..., description="The path to the model")
    details: Optional[Dict[str, str]] = Field(default=None, description="The metadata of the model")
    version: Optional[str] = Field(default='0.0.1', description="The version of the model")

class CreateModel(BaseModel):
    name: str = Field(..., description="The name of the model")
    description: Optional[str] = Field(..., description="The description of the model")
    url_or_path: str = Field(..., description="The path to the model")
    details: Optional[Dict[str, str]] = Field(default=None, description="The metadata of the model")
    version: Optional[str] = Field(default='0.0.1', description="The version of the model")

