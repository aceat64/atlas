from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.models.item import Item, ItemPublic
from app.models.tag import Tag

router = APIRouter()


@router.put("/{item_id}/tag/{tag_id}", response_model=ItemPublic)
def add_tag(
    session: SessionDep,
    user: CurrentUser,
    item_id: int,
    tag_id: int,
) -> Any:
    """
    Add a tag to an item.
    """
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    if item.tags.count(tag):
        return item

    item.tags.append(tag)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/{item_id}/tag/{tag_id}", response_model=ItemPublic)
def remove_tag(
    session: SessionDep,
    user: CurrentUser,
    item_id: int,
    tag_id: int,
) -> Any:
    """
    Remove a tag from a item.
    """
    item: Item | None = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    if not item.tags.count(tag):
        return item

    item.tags.remove(tag)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item
