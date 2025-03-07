from sqlalchemy import create_engine

from app.core.config import settings

engine = create_engine(str(settings.db_uri).replace("postgresql://", "postgresql+psycopg://"))
