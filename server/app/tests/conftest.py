import datetime
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.api.deps import get_current_user, get_token_payload
from app.auth.oidc import TokenPayload
from app.core.db import engine
from app.main import app
from app.models.attachment import Attachment
from app.models.collection import Collection
from app.models.item import Item
from app.models.room import Room
from app.models.stack import Stack
from app.models.user import User


@pytest.fixture(scope="module")
def client() -> Generator[TestClient]:
    with TestClient(app) as c:
        yield c


def clear_db(session: Session) -> None:
    # Delete it all now that the tests are done
    statement = delete(Item)
    session.exec(statement)  # type: ignore

    statement = delete(Collection)
    session.exec(statement)  # type: ignore

    statement = delete(Stack)
    session.exec(statement)  # type: ignore

    statement = delete(Room)
    session.exec(statement)  # type: ignore

    statement = delete(Attachment)
    session.exec(statement)  # type: ignore

    statement = delete(User)
    session.exec(statement)  # type: ignore
    session.commit()


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session]:
    with Session(engine) as session:
        clear_db(session)
        yield session
        clear_db(session)


def override_get_token_payload() -> TokenPayload:
    now = datetime.datetime.timestamp(datetime.datetime.now(tz=datetime.UTC))
    return TokenPayload(
        iss="https://authentik/application/o/atlas/",
        sub="testuser",
        aud="atlas",
        exp=now + 3600,  # 1hr from now
        iat=now - 3600,  # issued 1 hour ago
    )


app.dependency_overrides[get_token_payload] = override_get_token_payload


def override_get_current_user() -> User:
    return User(id=1, email="test@test.test", name="Test User", username="testuser")


app.dependency_overrides[get_current_user] = override_get_current_user
