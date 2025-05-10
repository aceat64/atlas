from datetime import datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi_pagination.ext.sqlmodel import apaginate
from fastapi_pagination.links import LimitOffsetPage
from sqlmodel import col, column, exists, select

from app.api.deps import CurrentUser, SessionDep, default_responses
from app.models import Message
from app.models.collection import Collection
from app.models.item import Item, ItemCreate, ItemPublic, ItemType, ItemUpdate
from app.models.stack import Stack
from app.models.tag import ItemTagLink

router = APIRouter()


@router.get("/")
async def list_items(
    session: SessionDep,
    current_user: CurrentUser,
    sort: Literal["created_at", "updated_at", "title", "collection", "stack", "id"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
    type: Annotated[
        list[ItemType] | None, Query(description="Filter results to specified item types.")
    ] = None,
    tag_id: Annotated[
        list[int] | None,
        Query(description="Filter results to items with all of the specified tags."),
    ] = None,
    collection_id: Annotated[
        int | None,
        Query(description="Filter results to items from the specified collection."),
    ] = None,
    stack_id: Annotated[
        int | None,
        Query(description="Filter results to items in the specified stack."),
    ] = None,
) -> LimitOffsetPage[ItemPublic]:
    # ) -> ItemsList:
    """Retrieve a list of items."""

    if sort == "collection":
        statement = (
            select(Item)
            .join(Collection, isouter=True)
            .order_by(
                col(Collection.title).desc() if order == "desc" else col(Collection.title).asc()
            )
        )
    elif sort == "stack":
        if order == "desc":
            statement = (
                select(Item)
                .join(Stack, isouter=True)
                .order_by(col(Stack.title).desc())
                .order_by(column("shelf").desc())
                .order_by(column("slot").desc())
            )
        else:
            statement = (
                select(Item)
                .join(Stack, isouter=True)
                .order_by(col(Stack.title).asc())
                .order_by(column("shelf").asc())
                .order_by(column("slot").asc())
            )
    else:
        statement = select(Item).order_by(
            column(sort).desc() if order == "desc" else column(sort).asc()
        )

    if type:
        statement = statement.where(col(Item.item_type).in_(type))

    if tag_id:
        for id in tag_id:
            # Create a subquery that checks if the item has this specific tag
            exists_query = select(ItemTagLink).where(
                ItemTagLink.item_id == Item.id, ItemTagLink.tag_id == id
            )

            # Add an EXISTS filter for this tag
            statement = statement.where(exists(exists_query))

    if collection_id:
        statement = statement.where(col(Item.collection_id) == collection_id)

    if stack_id:
        statement = statement.where(col(Item.stack_id) == stack_id)

    page: LimitOffsetPage[ItemPublic] = await apaginate(session, statement)  # type: ignore[arg-type]
    # It feels wrong to ignore the incompatible arg-type
    return page


@router.get("/{item_id}", response_model=ItemPublic, responses=default_responses)
async def get_item(session: SessionDep, current_user: CurrentUser, item_id: int) -> Any:
    """Get item by ID."""

    item = await session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return item


@router.post("/", response_model=ItemPublic)
async def create_item(
    *, session: SessionDep, current_user: CurrentUser, item_in: ItemCreate
) -> Any:
    """Create new item."""

    item = Item.model_validate(item_in)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@router.put("/{item_id}", response_model=ItemPublic, responses=default_responses)
async def update_item(
    *, session: SessionDep, current_user: CurrentUser, item_id: int, item_in: ItemUpdate
) -> Any:
    """Update a item."""

    item = await session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    update_dict = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_dict)
    item.updated_at = datetime.now()
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@router.delete(
    "/{item_id}",
    responses={
        **default_responses,
        200: {
            "model": Message,
            "content": {"application/json": {"example": {"detail": "Item deleted successfully"}}},
        },
    },
)
async def delete_item(session: SessionDep, current_user: CurrentUser, item_id: int) -> Message:
    """Delete an item."""

    item = await session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    await session.delete(item)
    await session.commit()
    return Message(detail="Item deleted successfully")
