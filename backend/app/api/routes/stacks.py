from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from fastapi_pagination.ext.sqlmodel import apaginate
from fastapi_pagination.links import LimitOffsetPage
from sqlmodel import col, column, select

from app.api.deps import CurrentUser, SessionDep, default_responses
from app.models import Message
from app.models.room import Room
from app.models.stack import Stack, StackCreate, StackPublic, StackUpdate

router = APIRouter()


@router.get("/")
async def list_stacks(
    session: SessionDep,
    current_user: CurrentUser,
    sort: Literal["created_at", "updated_at", "id", "title", "room"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
) -> LimitOffsetPage[StackPublic]:
    """Retrieve a list of stacks."""

    if sort == "room":
        statement = (
            select(Stack)
            .join(Room, isouter=True)
            .order_by(col(Room.title).desc() if order == "desc" else col(Room.title).asc())
        )
    else:
        statement = select(Stack).order_by(
            column(sort).desc() if order == "desc" else column(sort).asc()
        )

    page: LimitOffsetPage[StackPublic] = await apaginate(session, statement)  # type: ignore[arg-type]
    # It feels wrong to ignore the incompatible arg-type
    return page


@router.get("/{stack_id}", response_model=StackPublic, responses=default_responses)
async def get_stack(session: SessionDep, current_user: CurrentUser, stack_id: int) -> Any:
    """Get stack by ID."""

    stack = await session.get(Stack, stack_id)
    if not stack:
        raise HTTPException(status_code=404, detail="Stack not found")

    return stack


@router.post("/", response_model=StackPublic)
async def create_stack(
    session: SessionDep, current_user: CurrentUser, stack_in: StackCreate
) -> Any:
    """Create new stack."""

    stack = Stack.model_validate(stack_in)
    session.add(stack)
    await session.commit()
    await session.refresh(stack)
    return stack


@router.put("/{stack_id}", response_model=StackPublic, responses=default_responses)
async def update_stack(
    session: SessionDep, current_user: CurrentUser, stack_id: int, stack_in: StackUpdate
) -> Any:
    """Update a stack."""

    stack = await session.get(Stack, stack_id)
    if not stack:
        raise HTTPException(status_code=404, detail="Stack not found")

    update_dict = stack_in.model_dump(exclude_unset=True)
    stack.sqlmodel_update(update_dict)
    session.add(stack)
    await session.commit()
    await session.refresh(stack)
    return stack


@router.delete(
    "/{stack_id}",
    responses={
        **default_responses,
        200: {
            "model": Message,
            "content": {"application/json": {"example": {"detail": "Stack deleted successfully"}}},
        },
    },
)
async def delete_stack(session: SessionDep, current_user: CurrentUser, stack_id: int) -> Message:
    """Delete a stack."""

    stack = await session.get(Stack, stack_id)
    if not stack:
        raise HTTPException(status_code=404, detail="Stack not found")

    await session.delete(stack)
    await session.commit()
    return Message(detail="Stack deleted successfully")
