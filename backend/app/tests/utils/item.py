import random

from sqlmodel import Session

from app.models.item import Item, ItemType
from app.tests.utils.collection import create_random_collection
from app.tests.utils.stack import create_random_stack
from app.tests.utils.utils import random_lower_string


def create_random_item(
    session: Session,
    create_collection: bool = True,
    create_stack: bool = True,
    create_shelf: bool = True,
    create_slot: bool = True,
) -> Item:
    title = random_lower_string()
    collection_id = None
    stack_id = None
    shelf_num = None
    slot_num = None

    if create_collection:
        collection = create_random_collection(session)
        collection_id = collection.id
    if create_stack:
        stack = create_random_stack(session)
        stack_id = stack.id
    if create_shelf:
        shelf_num = random.randint(0, 10)
    if create_slot:
        slot_num = random.randint(0, 10)

    item = Item(
        title=title,
        item_type=random.choice(list(ItemType)),
        collection_id=collection_id,
        stack_id=stack_id,
        shelf=shelf_num,
        slot=slot_num,
        annotations={"foo": "bar"},
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item
