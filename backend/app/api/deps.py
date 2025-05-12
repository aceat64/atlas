from collections.abc import AsyncGenerator
from typing import Annotated, Any

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import OpenIdConnect
from fastapi.security.utils import get_authorization_scheme_param
from jwt.exceptions import InvalidTokenError
from opentelemetry import trace
from pydantic import ValidationError
from sqlalchemy.exc import NoResultFound
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth.oidc import OpenIDConnectDiscovery, TokenPayload
from app.core.config import settings
from app.core.db import async_engine
from app.models import Message
from app.models.user import User

default_responses: dict[int | str, dict[str, Any]] = {404: {"model": Message}}

log = structlog.stdlib.get_logger("app")


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with AsyncSession(async_engine) as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db)]
"""Get a database session instance"""

openid_connect = OpenIdConnect(openIdConnectUrl=str(settings.oidc_url), auto_error=False)
openid_provider = OpenIDConnectDiscovery(settings.oidc_url)


async def get_token_payload(authorization: Annotated[str, Depends(openid_connect)]) -> TokenPayload:
    try:
        scheme, token = get_authorization_scheme_param(authorization)
        if scheme.lower() != "bearer":
            # Tell the client they need to be using a bearer token
            log.debug("No access token was provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        payload = openid_provider.decode_access_token(token)
        log.debug("Validated access token", token=payload)
        return TokenPayload.model_validate(payload)
    except (InvalidTokenError, ValidationError) as exc:
        log.debug(f"Could not validate credentials: {exc}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Could not validate credentials: {exc}",
        ) from exc


TokenDep = Annotated[TokenPayload, Depends(get_token_payload)]
"""Get the validated access token payload for the request"""


async def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        result = await session.exec(select(User).where(User.email == token.email))
        user = result.one()
    except NoResultFound:
        log.debug("User not found in DB, creating entry from the access token")
        user_create = User(email=token.email, name=token.name, username=token.preferred_username)
        session.add(user_create)
        await session.commit()
        await session.refresh(user_create)
        log.debug("User created", user=user_create)
        return User.model_validate(user_create)

    log.debug("User found in DB", user=user)
    if isinstance(user.id, int):
        structlog.contextvars.bind_contextvars(user_id=user.id)
        current_span = trace.get_current_span()
        # ref: https://opentelemetry.io/docs/specs/semconv/attributes-registry/enduser/#end-user-attributes
        current_span.set_attribute("enduser.id", user.id)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
"""Get the user info for the request"""
