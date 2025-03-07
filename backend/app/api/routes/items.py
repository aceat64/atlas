from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import Message
from app.models.item import Item, ItemCreate, ItemPublic, ItemsPublic, ItemUpdate

router = APIRouter()


@router.get("/", response_model=ItemsPublic)
def read_items(
    session: SessionDep,
    user: CurrentUser,
    skip: int = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> Any:
    """
    Retrieve a list of items.
    """

    count_statement = select(func.count()).select_from(Item)
    count = session.exec(count_statement).one()
    statement = select(Item).offset(skip).limit(limit)
    things = session.exec(statement).all()

    return ItemsPublic(data=things, count=count)


@router.get("/{id}", response_model=ItemPublic)
def read_item(
    session: SessionDep,
    user: CurrentUser,
    id: int,
) -> Any:
    """
    Get item by ID.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post("/", response_model=ItemPublic)
def create_item(*, session: SessionDep, user: CurrentUser, item_in: ItemCreate) -> Any:
    """
    Create new thing.
    """
    item = Item.model_validate(item_in)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.put("/{id}", response_model=ItemPublic)
def update_item(
    *,
    session: SessionDep,
    user: CurrentUser,
    id: int,
    item_in: ItemUpdate,
) -> Any:
    """
    Update a item.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    update_dict = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_dict)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/{id}")
def delete_thing(
    session: SessionDep,
    user: CurrentUser,
    id: int,
) -> Message:
    """
    Delete an item.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    session.delete(item)
    session.commit()
    return Message(message="Item deleted successfully")
