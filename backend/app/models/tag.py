from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import computed_field
from sqlmodel import (
    Column,
    DateTime,
    Field,
    Identity,
    Relationship,
    SQLModel,
    UniqueConstraint,
    func,
)

if TYPE_CHECKING:
    from .item import Item


class ItemTagLink(SQLModel, table=True):
    """Linking table (many-to-many) for Item and Tag"""

    __table_args__ = (UniqueConstraint("item_id", "tag_id", name="uix_item_tag"),)
    item_id: int = Field(foreign_key="item.id", primary_key=True)
    tag_id: int = Field(foreign_key="tag.id", primary_key=True)
    created_at: datetime | None = Field(sa_column=Column(DateTime(timezone=True), server_default=func.now()))


class TagBase(SQLModel):
    """Shared properties"""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class TagCreate(TagBase):
    """Properties to receive on tag creation"""

    pass


class TagUpdate(TagBase):
    """Properties to receive on tag update"""

    name: str | None = None  # type: ignore


class Tag(TagBase, table=True):
    """Database model, database table inferred from class name"""

    id: int | None = Field(default=None, primary_key=True, sa_column_args=[Identity(always=True)])
    """id will be generated by the database"""
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )

    items: list["Item"] = Relationship(
        back_populates="tags",
        link_model=ItemTagLink,
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    @computed_field
    def item_count(self) -> int:
        """Total number of items with this tag"""
        return len(self.items)


class TagPublic(TagBase):
    """Properties to return via API, id is always required"""

    id: int
    created_at: datetime
    updated_at: datetime | None
