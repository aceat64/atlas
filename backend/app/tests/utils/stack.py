from sqlmodel import Session

from app.models.stack import Stack
from app.tests.utils.room import create_random_room
from app.tests.utils.utils import random_lower_string


def create_random_stack(session: Session) -> Stack:
    title = random_lower_string()
    room = create_random_room(session)
    stack = Stack(
        title=title,
        room_id=room.id,
        annotations={"foo": "bar"},
    )
    session.add(stack)
    session.commit()
    session.refresh(stack)
    return stack
