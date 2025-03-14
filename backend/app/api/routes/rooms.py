from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import Message
from app.models.room import Room, RoomBase, RoomPublic, RoomsPublic

router = APIRouter()

responses = {
    404: {
        "model": Message,
        "content": {"application/json": {"example": {"detail": "Room not found"}}},
    }
}


@router.get("/", response_model=RoomsPublic)
def list_rooms(
    session: SessionDep,
    user: CurrentUser,
    skip: int = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> Any:
    """Retrieve a list of rooms."""

    count_statement = select(func.count()).select_from(Room)
    count = session.exec(count_statement).one()
    statement = select(Room).offset(skip).limit(limit)
    rooms = session.exec(statement).all()

    return RoomsPublic(data=rooms, count=count)


@router.get("/{room_id}", response_model=RoomPublic, responses=responses)
def get_room(session: SessionDep, user: CurrentUser, room_id: int) -> Any:
    """Get room by ID."""

    room = session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    return room


@router.post("/", response_model=RoomPublic)
def create_room(session: SessionDep, user: CurrentUser, room_in: RoomBase) -> Any:
    """Create new room."""

    room = Room.model_validate(room_in)
    session.add(room)
    session.commit()
    session.refresh(room)
    return room


@router.put("/{room_id}", response_model=RoomPublic, responses=responses)
def update_room(session: SessionDep, user: CurrentUser, room_id: int, room_in: RoomBase) -> Any:
    """Update a room."""

    room = session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    update_dict = room_in.model_dump(exclude_unset=True)
    room.sqlmodel_update(update_dict)
    session.add(room)
    session.commit()
    session.refresh(room)
    return room


@router.delete(
    "/{room_id}",
    responses={
        **responses,
        200: {
            "model": Message,
            "content": {"application/json": {"example": {"detail": "Room deleted successfully"}}},
        },
    },
)
def delete_room(session: SessionDep, user: CurrentUser, room_id: int) -> Message:
    """Delete a room."""

    room = session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    session.delete(room)
    session.commit()
    return Message(message="Room deleted successfully")
