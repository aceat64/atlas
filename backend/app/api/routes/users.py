from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from fastapi_pagination.ext.sqlmodel import apaginate
from fastapi_pagination.links import LimitOffsetPage
from sqlmodel import column, select

from app.api.deps import CurrentUser, SessionDep, default_responses
from app.models.user import User, UserPublic

router = APIRouter()


@router.get("/")
async def list_users(
    session: SessionDep,
    current_user: CurrentUser,
    sort: Literal["created_at", "updated_at", "id", "email", "name", "username"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
) -> LimitOffsetPage[UserPublic]:
    """Retrieve a list of users."""

    statement = select(User).order_by(column(sort).desc() if order == "desc" else column(sort).asc())
    page: LimitOffsetPage[UserPublic] = await apaginate(session, statement)  # type: ignore[arg-type]
    # It feels wrong to ignore the incompatible arg-type
    return page


@router.get("/{user_id}", response_model=UserPublic, responses=default_responses)
async def get_user(session: SessionDep, current_user: CurrentUser, user_id: int) -> Any:
    """Get user by ID."""

    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
