from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings

db_url = str(Settings().db_uri).replace("postgresql://", "postgresql+psycopg://")
engine = create_engine(db_url)
async_engine = create_async_engine(db_url)
