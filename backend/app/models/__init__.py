from sqlmodel import SQLModel

# We must import our table models here so that Alembic's autogenerate works.
from .attachment import Attachment  # noqa: F401
from .collection import Collection  # noqa: F401
from .item import Item  # noqa: F401
from .room import Room  # noqa: F401
from .stack import Stack  # noqa: F401
from .tag import Tag  # noqa: F401
from .user import User  # noqa: F401


class Message(SQLModel):
    """Generic response message"""

    detail: str


class Status(SQLModel):
    """Status response message"""

    status: str = "ok"
