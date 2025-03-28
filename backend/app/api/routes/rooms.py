from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination.links import LimitOffsetPage
from sqlmodel import column, select

from app.api.deps import CurrentUser, SessionDep, default_responses
from app.models import Message
from app.models.room import Room, RoomCreate, RoomPublic, RoomUpdate

router = APIRouter()


@router.get("/")
async def list_rooms(
    session: SessionDep,
    current_user: CurrentUser,
    sort: Literal["created_at", "updated_at", "id", "title"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
) -> LimitOffsetPage[RoomPublic]:
    """Retrieve a list of rooms."""

    statement = select(Room).order_by(
        column(sort).desc() if order == "desc" else column(sort).asc()
    )

    page: LimitOffsetPage[RoomPublic] = await paginate(session, statement)
    return page


@router.get("/{room_id}", response_model=RoomPublic, responses=default_responses)
async def get_room(session: SessionDep, current_user: CurrentUser, room_id: int) -> Any:
    """Get room by ID."""

    room = await session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    return room


@router.post("/", response_model=RoomPublic)
async def create_room(session: SessionDep, current_user: CurrentUser, room_in: RoomCreate) -> Any:
    """Create new room."""

    room = Room.model_validate(room_in)
    session.add(room)
    await session.commit()
    await session.refresh(room)
    return room


@router.put("/{room_id}", response_model=RoomPublic, responses=default_responses)
async def update_room(
    session: SessionDep, current_user: CurrentUser, room_id: int, room_in: RoomUpdate
) -> Any:
    """Update a room."""

    room = await session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    update_dict = room_in.model_dump(exclude_unset=True)
    room.sqlmodel_update(update_dict)
    session.add(room)
    await session.commit()
    await session.refresh(room)
    return room


@router.delete(
    "/{room_id}",
    responses={
        **default_responses,
        200: {
            "model": Message,
            "content": {"application/json": {"example": {"detail": "Room deleted successfully"}}},
        },
    },
)
async def delete_room(session: SessionDep, current_user: CurrentUser, room_id: int) -> Message:
    """Delete a room."""

    room = await session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    await session.delete(room)
    await session.commit()
    return Message(detail="Room deleted successfully")
