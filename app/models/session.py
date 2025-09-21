import datetime
import secrets
import uuid
from typing import Any

import structlog
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel, func

from .user import User

log = structlog.stdlib.get_logger("models")


def generate_token_urlsafe() -> str:
    return secrets.token_urlsafe(64)


class Session(SQLModel, table=True):
    """Database model, database table inferred from class name"""

    token: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    auth_state: str = Field(default_factory=generate_token_urlsafe, unique=True)
    auth_nonce: str = Field(default_factory=generate_token_urlsafe, unique=True)

    created_at: datetime.datetime = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: datetime.datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )
    expires_at: datetime.datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
    )
    logged_out_at: datetime.datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True)),
    )

    user_id: int | None = Field(None, foreign_key="user.id")
    data: dict[str, Any] = Field({}, nullable=False, sa_type=JSONB)
    user: User | None = Relationship(
        back_populates="sessions",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    def is_active(self) -> bool:
        """Is the session active?"""
        if self.expires_at < datetime.datetime.now(datetime.UTC):
            log.debug("Session expired", session_token=self.token, expired_at=self.expires_at)
            return False
        if self.logged_out_at:
            log.debug("Session was already logged out", session_token=self.token, logged_out_at=self.logged_out_at)
            return False
        return True
