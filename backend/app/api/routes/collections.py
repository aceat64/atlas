from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination.links import LimitOffsetPage
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import Message
from app.models.collection import Collection, CollectionBase, CollectionPublic

router = APIRouter()

responses = {
    404: {
        "model": Message,
        "content": {"application/json": {"example": {"detail": "Collection not found"}}},
    }
}


@router.get("/")
def list_collections(session: SessionDep, user: CurrentUser) -> LimitOffsetPage[CollectionPublic]:
    """Retrieve a list of collections."""

    return paginate(session, select(Collection))


@router.get("/{collection_id}", response_model=CollectionPublic, responses=responses)
def get_collection(session: SessionDep, user: CurrentUser, collection_id: int) -> Any:
    """Get collection by ID."""

    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    return collection


@router.post("/", response_model=CollectionPublic)
def create_collection(session: SessionDep, user: CurrentUser, collection_in: CollectionBase) -> Any:
    """Create new collection."""

    collection = Collection.model_validate(collection_in)
    session.add(collection)
    session.commit()
    session.refresh(collection)
    return collection


@router.put("/{collection_id}", response_model=CollectionPublic, responses=responses)
def update_collection(
    session: SessionDep, user: CurrentUser, collection_id: int, collection_in: CollectionBase
) -> Any:
    """Update a collection."""

    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    update_dict = collection_in.model_dump(exclude_unset=True)
    collection.sqlmodel_update(update_dict)
    session.add(collection)
    session.commit()
    session.refresh(collection)
    return collection


@router.delete(
    "/{collection_id}",
    responses={
        **responses,
        200: {
            "model": Message,
            "content": {
                "application/json": {"example": {"detail": "Collection deleted successfully"}}
            },
        },
    },
)
def delete_collection(session: SessionDep, user: CurrentUser, collection_id: int) -> Message:
    """Delete a collection."""

    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    session.delete(collection)
    session.commit()
    return Message(detail="Collection deleted successfully")
