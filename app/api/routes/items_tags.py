from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, default_responses
from app.core.deps import DatabaseDep
from app.models.item import Item, ItemPublic
from app.models.tag import Tag

router = APIRouter()


@router.post("/{item_id}/tag/{tag_id}", response_model=ItemPublic, responses=default_responses)
async def add_tag(session: DatabaseDep, user: CurrentUser, item_id: int, tag_id: int) -> Any:
    """Add a tag to an item."""

    item = await session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    tag = await session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    # Item already has that tag
    if item.tags.count(tag):
        return item

    item.tags.append(tag)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@router.delete("/{item_id}/tag/{tag_id}", response_model=ItemPublic, responses=default_responses)
async def remove_tag(session: DatabaseDep, user: CurrentUser, item_id: int, tag_id: int) -> Any:
    """Remove a tag from a item."""

    item: Item | None = await session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    tag = await session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    # Item doesn't have have that tag, nothing to do
    if not item.tags.count(tag):
        return item

    item.tags.remove(tag)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item
