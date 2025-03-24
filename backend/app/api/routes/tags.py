from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination.links import LimitOffsetPage
from sqlmodel import column, select

from app.api.deps import CurrentUser, SessionDep, default_responses
from app.models import Message
from app.models.tag import Tag, TagBase, TagPublic

router = APIRouter()


@router.get("/")
async def list_tags(
    session: SessionDep,
    current_user: CurrentUser,
    sort: Literal["created_at", "updated_at", "id", "name"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
) -> LimitOffsetPage[TagPublic]:
    """Retrieve a list of tags."""

    statement = select(Tag).order_by(column(sort).desc() if order == "desc" else column(sort).asc())
    page: LimitOffsetPage[TagPublic] = await paginate(session, statement)
    return page


@router.get("/{tag_id}", response_model=TagPublic, responses=default_responses)
async def get_tag(session: SessionDep, current_user: CurrentUser, tag_id: int) -> Any:
    """Get tag by ID."""

    tag = await session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    return tag


@router.post("/", response_model=TagPublic)
async def create_tag(session: SessionDep, current_user: CurrentUser, tag_in: TagBase) -> Any:
    """Create new tag."""

    tag = Tag.model_validate(tag_in)
    session.add(tag)
    await session.commit()
    await session.refresh(tag)
    return tag


@router.put("/{tag_id}", response_model=TagPublic, responses=default_responses)
async def update_tag(
    session: SessionDep, current_user: CurrentUser, tag_id: int, tag_in: TagBase
) -> Any:
    """Update a tag."""

    tag = await session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    update_dict = tag_in.model_dump(exclude_unset=True)
    tag.sqlmodel_update(update_dict)
    session.add(tag)
    await session.commit()
    await session.refresh(tag)
    return tag


@router.delete(
    "/{tag_id}",
    responses={
        **default_responses,
        200: {
            "model": Message,
            "content": {"application/json": {"example": {"detail": "Tag deleted successfully"}}},
        },
    },
)
async def delete_tag(session: SessionDep, current_user: CurrentUser, tag_id: int) -> Message:
    """Delete a tag."""

    tag = await session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    await session.delete(tag)
    await session.commit()
    return Message(detail="Tag deleted successfully")
