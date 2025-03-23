from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination.links import LimitOffsetPage
from sqlmodel import column, select

from app.api.deps import CurrentUser, SessionDep
from app.models.user import User, UserPublic

router = APIRouter()


@router.get("/")
def list_users(
    session: SessionDep,
    user: CurrentUser,
    sort: Literal["created_at", "updated_at", "id", "email", "name", "username"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
) -> LimitOffsetPage[UserPublic]:
    """Retrieve a list of users."""

    statement = select(User).order_by(
        column(sort).desc() if order == "desc" else column(sort).asc()
    )
    return paginate(session, statement)


@router.get("/{user_id}", response_model=UserPublic)
def get_user(session: SessionDep, user: CurrentUser, user_id: int) -> Any:
    """Get user by ID."""

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
