from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Column, DateTime, Field, Identity, Relationship, SQLModel, func

if TYPE_CHECKING:
    from .item import Item


class AttachmentBase(SQLModel):
    item_id: int = Field(default=None, foreign_key="item.id")
    filename: str
    content_type: str
    filesize: int
    """Size of file in bytes"""
    checksum_sha256: str | None = None
    """sha256 checksum of file, calculated prior to uploading"""


class Attachment(AttachmentBase, table=True):
    """File attachment, database model, database table inferred from class name"""

    id: int | None = Field(None, primary_key=True, sa_column_args=[Identity(always=True)])
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    item: "Item" = Relationship(
        back_populates="attachments",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class AttachmentPublic(AttachmentBase):
    """Properties to return via API, id is always required"""

    id: int
    created_at: datetime
