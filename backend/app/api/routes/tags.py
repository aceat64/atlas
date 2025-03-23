from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination.links import LimitOffsetPage
from sqlmodel import column, select

from app.api.deps import CurrentUser, SessionDep
from app.models import Message
from app.models.tag import Tag, TagBase, TagPublic

router = APIRouter()

responses = {
    404: {
        "model": Message,
        "content": {"application/json": {"example": {"detail": "Tag not found"}}},
    }
}


@router.get("/")
def list_tags(
    session: SessionDep,
    user: CurrentUser,
    sort: Literal["created_at", "updated_at", "id", "name"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
) -> LimitOffsetPage[TagPublic]:
    """Retrieve a list of tags."""

    statement = select(Tag).order_by(column(sort).desc() if order == "desc" else column(sort).asc())
    return paginate(session, statement)


@router.get("/{tag_id}", response_model=TagPublic, responses=responses)
def get_tag(session: SessionDep, user: CurrentUser, tag_id: int) -> Any:
    """Get tag by ID."""

    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    return tag


@router.post("/", response_model=TagPublic)
def create_tag(session: SessionDep, user: CurrentUser, tag_in: TagBase) -> Any:
    """Create new tag."""

    tag = Tag.model_validate(tag_in)
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


@router.put("/{tag_id}", response_model=TagPublic, responses=responses)
def update_tag(session: SessionDep, user: CurrentUser, tag_id: int, tag_in: TagBase) -> Any:
    """Update a tag."""

    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    update_dict = tag_in.model_dump(exclude_unset=True)
    tag.sqlmodel_update(update_dict)
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


@router.delete(
    "/{tag_id}",
    responses={
        **responses,
        200: {
            "model": Message,
            "content": {"application/json": {"example": {"detail": "Tag deleted successfully"}}},
        },
    },
)
def delete_tag(session: SessionDep, user: CurrentUser, tag_id: int) -> Message:
    """Delete a tag."""

    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    session.delete(tag)
    session.commit()
    return Message(detail="Tag deleted successfully")
