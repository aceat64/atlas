from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination.links import LimitOffsetPage
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models.user import User, UserPublic, UsersPublic

router = APIRouter()


@router.get("/", response_model=UsersPublic)
def list_users(session: SessionDep, user: CurrentUser) -> LimitOffsetPage[UserPublic]:
    """Retrieve a list of users."""

    return paginate(session, select(User))


@router.get("/{user_id}", response_model=UserPublic)
def get_user(session: SessionDep, user: CurrentUser, user_id: int) -> Any:
    """Get user by ID."""

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
