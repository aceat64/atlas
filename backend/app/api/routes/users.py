from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models.user import User, UserPublic, UsersPublic

router = APIRouter()


@router.get("/", response_model=UsersPublic)
def list_users(
    session: SessionDep,
    user: CurrentUser,
    skip: int = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> Any:
    """Retrieve a list of users."""

    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()
    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()

    return UsersPublic(data=users, count=count)


@router.get("/{user_id}", response_model=UserPublic)
def get_user(session: SessionDep, user: CurrentUser, user_id: int) -> Any:
    """Get user by ID."""

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
