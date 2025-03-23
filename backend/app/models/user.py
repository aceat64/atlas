from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, Identity, SQLModel


class UserBase(SQLModel):
    """Shared properties"""

    email: EmailStr = Field(max_length=255)
    name: str = Field(max_length=255)
    username: str = Field(max_length=255)


class UserCreate(UserBase):
    """Properties to receive on user creation"""

    pass


class UserUpdate(UserBase):
    """Properties to receive on user update"""

    pass


class User(UserBase, table=True):
    """Database model, database table inferred from class name"""

    id: int | None = Field(default=None, primary_key=True, sa_column_args=[Identity(always=True)])
    """id will be generated by the database"""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class UserPublic(UserBase):
    """Properties to return via API, id is always required"""

    id: int
    created_at: datetime
    updated_at: datetime
