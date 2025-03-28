# Third-Party Dependencies
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

# Local Dependencies
from src.core.config import settings
from src.core.logger import logging

logger = logging.getLogger(__name__)


# Define the database URI and URL based on the application settings
POSTGRES_ASYNC_URI = f"{settings.POSTGRES_ASYNC_URI}"

# Create an async database engine
async_engine = create_async_engine(POSTGRES_ASYNC_URI, echo=False, future=True)

# Create a local session class using the async engine
local_session = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


# Define an async function to get the database session
async def get_async_db() -> AsyncSession:
    logger.info(f"Creating session with engine URL")

    async_session = local_session

    async with async_session() as db:
        try:
            yield db
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise e
        finally:
            await db.close()
