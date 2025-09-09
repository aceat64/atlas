from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from fastapi_pagination.ext.sqlmodel import apaginate
from fastapi_pagination.links import LimitOffsetPage
from sqlmodel import column, select

from app.api.deps import CurrentUser, default_responses
from app.core.deps import DatabaseDep
from app.models import Message
from app.models.collection import Collection, CollectionCreate, CollectionPublic, CollectionUpdate

router = APIRouter()


@router.get("/")
async def list_collections(
    session: DatabaseDep,
    user: CurrentUser,
    sort: Literal["created_at", "updated_at", "title", "id"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
) -> LimitOffsetPage[CollectionPublic]:
    """Retrieve a list of collections."""

    statement = select(Collection).order_by(column(sort).desc() if order == "desc" else column(sort).asc())
    page: LimitOffsetPage[CollectionPublic] = await apaginate(session, statement)  # type: ignore[arg-type]
    # It feels wrong to ignore the incompatible arg-type
    return page


@router.get("/{collection_id}", response_model=CollectionPublic, responses=default_responses)
async def get_collection(session: DatabaseDep, user: CurrentUser, collection_id: int) -> Any:
    """Get collection by ID."""

    collection = await session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    return collection


@router.post("/", response_model=CollectionPublic)
async def create_collection(session: DatabaseDep, user: CurrentUser, collection_in: CollectionCreate) -> Any:
    """Create new collection."""

    collection = Collection.model_validate(collection_in)
    session.add(collection)
    await session.commit()
    await session.refresh(collection)
    return collection


@router.put("/{collection_id}", response_model=CollectionPublic, responses=default_responses)
async def update_collection(
    session: DatabaseDep, user: CurrentUser, collection_id: int, collection_in: CollectionUpdate
) -> Any:
    """Update a collection."""

    collection = await session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    update_dict = collection_in.model_dump(exclude_unset=True)
    collection.sqlmodel_update(update_dict)
    session.add(collection)
    await session.commit()
    await session.refresh(collection)
    return collection


@router.delete(
    "/{collection_id}",
    responses={
        **default_responses,
        200: {
            "model": Message,
            "content": {"application/json": {"example": {"detail": "Collection deleted successfully"}}},
        },
    },
)
async def delete_collection(session: DatabaseDep, user: CurrentUser, collection_id: int) -> Message:
    """Delete a collection."""

    collection = await session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    await session.delete(collection)
    await session.commit()
    return Message(detail="Collection deleted successfully")
