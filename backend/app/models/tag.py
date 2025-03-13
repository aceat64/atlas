from typing import TYPE_CHECKING

from pydantic import computed_field
from sqlmodel import Field, Identity, Relationship, SQLModel, UniqueConstraint

if TYPE_CHECKING:
    from .item import Item


class ItemTagLink(SQLModel, table=True):
    """Linking table (many-to-many) for Item and Tag"""

    __table_args__ = (UniqueConstraint("item_id", "tag_id"),)
    item_id: int = Field(default=None, foreign_key="item.id", primary_key=True)
    tag_id: int = Field(default=None, foreign_key="tag.id", primary_key=True)


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

    items: list["Item"] = Relationship(back_populates="tags", link_model=ItemTagLink)

    @computed_field
    def item_count(self) -> int:
        """Total number of items with this tag"""
        return len(self.items)


class TagPublic(TagBase):
    """Properties to return via API, id is always required"""

    id: int


class TagsPublic(SQLModel):
    data: list[TagPublic]
    count: int
