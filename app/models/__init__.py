from sqlmodel import SQLModel

# We list all the models here so that Alembic's autogenerate works.
# Used by "from app.models import *" in app/alembic/env.py
__all__ = ["attachment", "collection", "item", "room", "session", "stack", "tag", "user"]


class Message(SQLModel):
    """Generic response message"""

    detail: str
