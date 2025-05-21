from collections.abc import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import Settings

db_url = str(Settings().db_uri).replace("postgresql://", "postgresql+psycopg://")
engine = create_engine(db_url)
async_engine = create_async_engine(db_url)


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with AsyncSession(async_engine) as session:
        yield session
