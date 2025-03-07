from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OpenIdConnect
from fastapi.security.utils import get_authorization_scheme_param
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlalchemy.exc import NoResultFound
from sqlmodel import Session, select

from app.auth.oidc import OpenIDConnectDiscovery, TokenPayload
from app.core.config import settings
from app.core.db import engine
from app.models.user import User


def get_db() -> Generator[Session, None, None]:
    """Get a database session instance"""
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
"""Get a database session instance"""

openid_connect = OpenIdConnect(openIdConnectUrl=str(settings.oidc_url), auto_error=False)
openid_provider = OpenIDConnectDiscovery(settings.oidc_url)


def get_token_payload(authorization: Annotated[str, Depends(openid_connect)]) -> TokenPayload:
    try:
        scheme, token = get_authorization_scheme_param(authorization)
        if scheme.lower() != "bearer":
            # Tell the client they need to be using a bearer token
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        payload = openid_provider.decode_access_token(token)
        return TokenPayload.model_validate(payload)
    except (InvalidTokenError, ValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Could not validate credentials: {str(exc)}",
        ) from exc


TokenDep = Annotated[TokenPayload, Depends(get_token_payload)]
"""Get the validated access token payload for the request"""


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        user = session.exec(select(User).where(User.email == token.email)).one()
    except NoResultFound:
        user_create = User(email=token.email, name=token.name, username=token.preferred_username)
        session.add(user_create)
        session.commit()
        session.refresh(user_create)
        return User.model_validate(user_create)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
"""Get the user info for the request"""
