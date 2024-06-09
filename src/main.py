from contextlib import asynccontextmanager
from os import getenv

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()


@asynccontextmanager
async def lifespan(entrypoint: FastAPI):
    try:
        yield
    finally:
        pass


app = FastAPI(
    lifespan=lifespan,
    title=getenv("APP_NAME", "Moodme Backend"),
    version=getenv("APP_VERSION", "0.1.0"),
    description=getenv("APP_DESCRIPTION", "A backend for Moodme"),
    contact={
        "name": getenv("APP_CONTACT_NAME", "Moodme Team"),
        "url": getenv("APP_CONTACT_URL", "https://moodme.io"),
        "email": getenv("APP_CONTACT_EMAIL", "ari@mood-me.com"),
    },
)
