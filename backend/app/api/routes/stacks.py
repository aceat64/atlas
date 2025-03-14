from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import Message
from app.models.stack import Stack, StackBase, StackPublic, StacksPublic

router = APIRouter()

responses = {
    404: {
        "model": Message,
        "content": {"application/json": {"example": {"detail": "Stack not found"}}},
    }
}


@router.get("/", response_model=StacksPublic)
def list_stacks(
    session: SessionDep,
    user: CurrentUser,
    skip: int = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> Any:
    """Retrieve a list of stacks."""

    count_statement = select(func.count()).select_from(Stack)
    count = session.exec(count_statement).one()
    statement = select(Stack).offset(skip).limit(limit)
    stacks = session.exec(statement).all()

    return StacksPublic(data=stacks, count=count)


@router.get("/{stack_id}", response_model=StackPublic, responses=responses)
def get_stack(session: SessionDep, user: CurrentUser, stack_id: int) -> Any:
    """Get stack by ID."""

    stack = session.get(Stack, stack_id)
    if not stack:
        raise HTTPException(status_code=404, detail="Stack not found")

    return stack


@router.post("/", response_model=StackPublic)
def create_stack(session: SessionDep, user: CurrentUser, stack_in: StackBase) -> Any:
    """Create new stack."""

    stack = Stack.model_validate(stack_in)
    session.add(stack)
    session.commit()
    session.refresh(stack)
    return stack


@router.put("/{stack_id}", response_model=StackPublic, responses=responses)
def update_stack(session: SessionDep, user: CurrentUser, stack_id: int, stack_in: StackBase) -> Any:
    """Update a stack."""

    stack = session.get(Stack, stack_id)
    if not stack:
        raise HTTPException(status_code=404, detail="Stack not found")

    update_dict = stack_in.model_dump(exclude_unset=True)
    stack.sqlmodel_update(update_dict)
    session.add(stack)
    session.commit()
    session.refresh(stack)
    return stack


@router.delete(
    "/{stack_id}",
    responses={
        **responses,
        200: {
            "model": Message,
            "content": {"application/json": {"example": {"detail": "Stack deleted successfully"}}},
        },
    },
)
def delete_stack(session: SessionDep, user: CurrentUser, stack_id: int) -> Message:
    """Delete a stack."""

    stack = session.get(Stack, stack_id)
    if not stack:
        raise HTTPException(status_code=404, detail="Stack not found")

    session.delete(stack)
    session.commit()
    return Message(message="Stack deleted successfully")
