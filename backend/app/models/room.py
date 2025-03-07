from typing import TYPE_CHECKING, Any

from pydantic import Json
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Identity, Relationship, SQLModel

if TYPE_CHECKING:
    from .stack import Stack


class RoomBase(SQLModel):
    """Shared properties"""

    title: str = Field(min_length=1, max_length=255)
    annotations: Json[Any] | None = Field(None, sa_type=JSONB)


class RoomCreate(RoomBase):
    """Properties to receive on room creation"""

    pass


class RoomUpdate(RoomBase):
    """Properties to receive on room update"""

    # We are ignoring the typing issues because we need the fields to be optional on update
    title: str | None = Field(None, max_length=255)  # type: ignore


class Room(RoomBase, table=True):
    """Database model, database table inferred from class name"""

    id: int | None = Field(default=None, primary_key=True, sa_column_args=[Identity(always=True)])
    """id will be generated by the database"""

    stacks: list["Stack"] = Relationship(back_populates="room", cascade_delete=False)


class RoomPublic(RoomBase):
    """Properties to return via API, id is always required"""

    id: int


class RoomsPublic(SQLModel):
    data: list[RoomPublic]
    count: int
