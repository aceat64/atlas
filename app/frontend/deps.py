from pathlib import Path
from typing import Annotated

import structlog
from fastapi import Cookie, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from opentelemetry import trace
from sqlalchemy.exc import NoResultFound
from sqlmodel import select

from app.core.deps import DatabaseDep
from app.models.session import Session
from app.models.user import User

log = structlog.stdlib.get_logger("frontend")

templates = Jinja2Templates(directory=Path(__file__).parent.joinpath("templates"))


async def get_templates() -> Jinja2Templates:
    return templates


TemplatesDep = Annotated[Jinja2Templates, Depends(get_templates)]
"""Get a jinja template instance"""


async def get_session(db: DatabaseDep, session_token: Annotated[str | None, Cookie()] = None) -> Session:
    if session_token is None:
        log.debug("No session token cookie")
        return Session()

    try:
        result = await db.exec(select(Session).where(Session.token == session_token))
        session: Session = result.one()
    except NoResultFound:
        log.debug("Unknown session token", session_token=session_token)
        return Session()

    log.debug("Session found", session_token=session.token)
    if session.is_active():
        log.debug("Session active", session_token=session.token)
        return session

    log.debug("Session is not active", session_token=session.token)
    return Session()


SessionDep = Annotated[Session, Depends(get_session)]


async def get_current_user(db: DatabaseDep, session: SessionDep) -> User:
    if not session.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        result = await db.exec(select(User).where(User.id == session.user_id))
        user = result.one()
    except NoResultFound as exc:
        log.warn(
            "Active session, but the user doesn't exist!",
            session_token=session.token,
            user_id=session.user_id,
        )
        raise HTTPException(status_code=500, detail="An unexpected error occurred.") from exc

    log.debug("User found in DB", user=user)
    structlog.contextvars.bind_contextvars(user_id=user.id)
    current_span = trace.get_current_span()
    # ref: https://opentelemetry.io/docs/specs/semconv/attributes-registry/enduser/#end-user-attributes
    current_span.set_attribute("enduser.id", str(user.id))
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
"""Get the user info for the request"""
