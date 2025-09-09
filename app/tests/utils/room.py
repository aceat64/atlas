from sqlmodel import Session

from app.models.room import Room
from app.tests.utils.utils import random_lower_string


def create_random_room(session: Session) -> Room:
    title = random_lower_string()
    room = Room(
        title=title,
        annotations={"foo": "bar"},
    )
    session.add(room)
    session.commit()
    session.refresh(room)
    return room
