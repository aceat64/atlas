from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination.links import LimitOffsetPage
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import Message
from app.models.item import Item, ItemCreate, ItemDetail, ItemPublic, ItemUpdate

router = APIRouter()

responses = {
    404: {
        "model": Message,
        "content": {"application/json": {"example": {"detail": "Item not found"}}},
    }
}


@router.get("/")
def list_items(session: SessionDep, user: CurrentUser) -> LimitOffsetPage[ItemPublic]:
    """Retrieve a list of items."""

    return paginate(session, select(Item))


@router.get("/{item_id}", response_model=ItemDetail, responses=responses)
def get_item(session: SessionDep, user: CurrentUser, item_id: int) -> Any:
    """Get item by ID."""

    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return item


@router.post("/", response_model=ItemPublic)
def create_item(*, session: SessionDep, user: CurrentUser, item_in: ItemCreate) -> Any:
    """Create new item."""

    item = Item.model_validate(item_in)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.put("/{item_id}", response_model=ItemPublic, responses=responses)
def update_item(
    *, session: SessionDep, user: CurrentUser, item_id: int, item_in: ItemUpdate
) -> Any:
    """Update a item."""

    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    update_dict = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_dict)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete(
    "/{item_id}",
    responses={
        **responses,
        200: {
            "model": Message,
            "content": {"application/json": {"example": {"detail": "Item deleted successfully"}}},
        },
    },
)
def delete_item(session: SessionDep, user: CurrentUser, item_id: int) -> Message:
    """Delete an item."""

    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    session.delete(item)
    session.commit()
    return Message(detail="Item deleted successfully")
