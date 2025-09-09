import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func

from .user import User


class Session(SQLModel, table=True):
    """Database model, database table inferred from class name"""

    token: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    created_at: datetime = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
    )
    logged_out_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True)),
    )

    user_id: int = Field(foreign_key="user.id")
    data: dict[str, Any] = Field({}, nullable=False, sa_type=JSONB)
    user: User | None = Relationship(
        back_populates="sessions",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
