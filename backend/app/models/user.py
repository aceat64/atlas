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

    # We are ignoring the typing issues because we need the fields to be optional on update
    name: str | None = Field(default=None, max_length=255)  # type: ignore
    username: str | None = Field(default=None, max_length=255)  # type: ignore


class User(UserBase, table=True):
    """Database model, database table inferred from class name"""

    id: int | None = Field(default=None, primary_key=True, sa_column_args=[Identity(always=True)])
    """id will be generated by the database"""


class UserPublic(UserBase):
    """Properties to return via API, id is always required"""

    id: int


class UsersPublic(UserBase):
    data: list[UserPublic]
    count: int
