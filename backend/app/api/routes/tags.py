from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import Message
from app.models.tag import Tag, TagBase, TagPublic, TagsPublic

router = APIRouter()


@router.get("/", response_model=TagsPublic)
def read_tags(
    session: SessionDep,
    user: CurrentUser,
    skip: int = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> Any:
    """
    Retrieve a list of tags.
    """

    count_statement = select(func.count()).select_from(Tag)
    count = session.exec(count_statement).one()
    statement = select(Tag).offset(skip).limit(limit)
    tags = session.exec(statement).all()

    return TagsPublic(data=tags, count=count)


@router.get("/{tag_id}", response_model=TagPublic)
def read_tag(
    session: SessionDep,
    user: CurrentUser,
    tag_id: int,
) -> Any:
    """
    Get tag by ID.
    """
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


@router.post("/", response_model=TagPublic)
def create_tag(
    session: SessionDep,
    user: CurrentUser,
    tag_in: TagBase,
) -> Any:
    """
    Create new tag.
    """
    tag = Tag.model_validate(tag_in)
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


@router.put("/{tag_id}")
def update_tag(
    session: SessionDep,
    user: CurrentUser,
    tag_id: int,
    tag_in: TagBase,
) -> Tag:
    """
    Update a tag.
    """
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    update_dict = tag_in.model_dump(exclude_unset=True)
    tag.sqlmodel_update(update_dict)
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


@router.delete("/{tag_id}")
def delete_tag(
    session: SessionDep,
    user: CurrentUser,
    tag_id: int,
) -> Message:
    """
    Delete a tag.
    """
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    session.delete(tag)
    session.commit()
    return Message(message="Tag deleted successfully")
