from typing import Union, Dict, Any
from contextlib import asynccontextmanager
from os import getenv
import anyio

from fastapi import FastAPI, APIRouter
import fastapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

from db.session import async_engine as engine
from core.models import Base
from core.logger import logging
from utils.system_info import log_system_info
from core.config import (
    AppSettings,
    DatabaseSettings,
    CORSSettings,
    SecuritySettings,
    EnvironmentSettings,
    EnvironmentOption,
)

from apps import router as api_router

# Logger instance for the current module
logger = logging.getLogger(__name__)


# Database
async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def set_threadpool_tokens(number_of_tokens: int = 100) -> None:
    limiter = anyio.to_thread.current_default_thread_limiter()
    limiter.total_tokens = number_of_tokens


async def ensure_private_key_exists() -> None:
    # Function to ensure private key exists
    from src.core.config import settings
    import os

    if not os.path.exists(settings.PRIVATE_KEY_PATH):
        raise FileNotFoundError(f"Private key not found at {settings.PRIVATE_KEY_PATH}")


async def startup_logging() -> None:
    log_system_info(logger=logger)


async def shutdown_logging() -> None:
    logger.info("API Shutdown")


@asynccontextmanager
async def lifespan(_entrypoint: FastAPI):
    await ensure_private_key_exists()
    await set_threadpool_tokens()
    # await create_tables()
    yield
    await shutdown_logging()


def create_app(
    settings: Union[
        AppSettings,
        DatabaseSettings,
        CORSSettings,
        SecuritySettings,
        EnvironmentSettings,
    ],
    **kwargs: Dict[str, Any],
) -> FastAPI:
    if isinstance(settings, AppSettings):
        to_update = {
            "title": settings.PROJECT_NAME,
            "version": settings.APP_VERSION,
            "description": settings.PROJECT_DESCRIPTION,
        }
        kwargs.update(to_update)

    if isinstance(settings, EnvironmentSettings):
        kwargs.update({"docs_url": None, "redoc_url": None, "openapi_url": None})

    app_ = FastAPI(lifespan=lifespan, **kwargs)

    if isinstance(settings, SecuritySettings):
        app_.add_event_handler("startup", ensure_private_key_exists)

    if isinstance(settings, CORSSettings):
        app_.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ALLOW_ORIGINS,
            allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
            allow_methods=settings.CORS_ALLOW_METHODS,
            allow_headers=settings.CORS_ALLOW_HEADERS,
            expose_headers=settings.CORS_EXPOSE_HEADERS,
            max_age=settings.CORS_MAX_AGE,
        )

        if isinstance(settings, EnvironmentSettings):
            if settings.ENVIRONMENT != EnvironmentOption.PRODUCTION:
                docs_router = APIRouter()
                # if settings.ENVIRONMENT != EnvironmentOption.LOCAL:
                #     docs_router = APIRouter(dependencies=[Depends(get_current_superuser)])

                @docs_router.get("/docs", include_in_schema=False)
                async def get_swagger_documentation() -> fastapi.responses.HTMLResponse:
                    return get_swagger_ui_html(
                        openapi_url="/openapi.json", title="docs"
                    )

                @docs_router.get("/redoc", include_in_schema=False)
                async def get_redoc_documentation() -> fastapi.responses.HTMLResponse:
                    return get_redoc_html(openapi_url="/openapi.json", title="docs")

                @docs_router.get("/openapi.json", include_in_schema=False)
                async def openapi() -> Dict[str, Any]:
                    out: dict = get_openapi(
                        title=app_.title,
                        description=app_.description,
                        contact=app_.contact,
                        version=app_.version,
                        routes=app_.routes,
                    )

                    return out

            app_.include_router(docs_router)
    app_.include_router(api_router)
    return app_
