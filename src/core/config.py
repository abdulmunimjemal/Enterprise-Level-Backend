from typing import List, Any, Annotated, TypeVar, Optional
from enum import Enum
from pydantic import PostgresDsn, field_validator, Field
from pydantic_settings import BaseSettings
from pydantic_core.core_schema import ValidationInfo
from starlette.config import Config
import os
from dotenv import load_dotenv

# Environment Variables Config Getters
current_file_dir = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(os.path.join(current_file_dir, "..", "..", ".."))
env_path = os.path.abspath(os.path.join(ROOT_DIR, ".env"))
config = Config(env_path)

load_dotenv(env_path)


T = TypeVar("T")
ExcludedField = Annotated[T, Field(exclude=True)]


class AppSettings(BaseSettings):
    PROJECT_NAME: str = config("PROJECT_NAME", default="MoodMe")
    PROJECT_DESCRIPTION: str = config("PROJECT_DESCRIPTION", default=None)
    APP_VERSION: str = config("APP_VERSION", default="0.1.0")


class AWSSettings(BaseSettings):
    AWS_PROFILE: Optional[str] = config("AWS_PROFILE", default="default")
    AWS_REGION: Optional[str] = config("AWS_REGION", default="us-east-1")
    AWS_ACCESS_KEY_ID: Optional[str] = config("AWS_ACCESS_KEY_ID", default=None)
    AWS_SECRET_ACCESS_KEY: Optional[str] = config("AWS_SECRET_ACCESS_KEY", default=None)
    AWS_MODEL_BUCKET: Optional[str] = config("AWS_MODEL_BUCKET", default=None)


class DatabaseSettings(BaseSettings):
    pass


class SecuritySettings(BaseSettings):
    PRIVATE_KEY_PATH: str = config("PRIVATE_KEY_PATH", default="./certs/privkey.pem")
    JWT_SECRET_KEY: str = config("JWT_SECRET_KEY", default="n0ts3cr3t")
    JWT_EXPIRATION_MINUTES: int = config("JWT_EXPIRATION_MINUTES", default=60)


class StorageSettings(BaseSettings):
    STORAGE_PATH: str = config("STORAGE_PATH", default="/tmp")
    MODEL_PATH: str = config("MODEL_PATH", default="/tmp/models")


class PostgresSettings(DatabaseSettings):
    POSTGRES_USER: str = config("POSTGRES_USER", default="postgres")
    POSTGRES_PASSWORD: str = config("POSTGRES_PASSWORD", default="postgres")
    POSTGRES_SERVER: str = config("POSTGRES_SERVER", default="db")
    POSTGRES_PORT: int = config("POSTGRES_PORT", default=5432)
    POSTGRES_DB: str = config("POSTGRES_DB", default="postgres")
    POSTGRES_ASYNC_URI: PostgresDsn | str = (
        "postgresql+asyncpg://postgres:postgres@db:5432/pybe"
    )

    @field_validator("POSTGRES_ASYNC_URI", mode="after")
    def assemble_db_connection(cls, v: str | None, info: ValidationInfo) -> Any:
        if isinstance(v, str):
            if v == "":
                return PostgresDsn.build(
                    scheme="postgresql+asyncpg",
                    username=info.data["POSTGRES_USER"],
                    password=info.data["POSTGRES_PASSWORD"],
                    host=info.data["POSTGRES_SERVER"],
                    port=info.data["POSTGRES_PORT"],
                    path=info.data["POSTGRES_DB"],
                )
        return v


class CORSSettings(BaseSettings):
    CORS_ALLOW_ORIGINS: List[str] | str = config(
        "CORS_ALLOW_ORIGINS", default="*"
    ).split(",")
    CORS_ALLOW_METHODS: List[str] | str = config("CORS_ALLOW_METHODS", default="*").upper().split(",")  # fmt: skip
    CORS_ALLOW_HEADERS: List[str] | str = config(
        "CORS_ALLOW_HEADERS", default="*"
    ).split(",")
    CORS_ALLOW_CREDENTIALS: bool = config("CORS_ALLOW_CREDENTIALS", default="False").lower() == "true"  # fmt: skip
    CORS_EXPOSE_HEADERS: List[str] | str = config(
        "CORS_EXPOSE_HEADERS", default=""
    ).split(",")
    CORS_MAX_AGE: int = int(config("CORS_MAX_AGE", default="600"))


class EnvironmentOption(Enum):
    LOCAL = "local"
    DEV = "dev"
    STAGING = "staging"
    PRODUCTION = "production"


class EnvironmentSettings(BaseSettings):
    ENVIRONMENT: EnvironmentOption = config("ENVIRONMENT", default="local")


class Settings(
    AppSettings,
    AWSSettings,
    SecuritySettings,
    PostgresSettings,
    StorageSettings,
    CORSSettings,
    EnvironmentSettings,
):
    pass


settings = Settings()


def get_settings():
    return settings
