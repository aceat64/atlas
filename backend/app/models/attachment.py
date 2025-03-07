from sqlmodel import Field, Identity, Relationship, SQLModel

from .item import Item


class Attachment(SQLModel, table=True):
    """File attachment, database model, database table inferred from class name"""

    id: int | None = Field(default=None, primary_key=True, sa_column_args=[Identity(always=True)])
    item_id: int = Field(default=None, foreign_key="item.id")
    item: Item = Relationship(back_populates="attachments")
    filename: str
    mime_type: str
    filesize: int
    checksum: str
