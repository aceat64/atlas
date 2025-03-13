from sqlmodel import Session

from app.models.collection import Collection
from app.tests.utils.utils import random_lower_string


def create_random_collection(session: Session) -> Collection:
    title = random_lower_string()
    collection = Collection(
        title=title,
        annotations={"foo": "bar"},
    )
    session.add(collection)
    session.commit()
    session.refresh(collection)
    return collection
