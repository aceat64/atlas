import datetime
from pathlib import Path
from typing import Annotated, Any
from urllib.parse import urlencode

import httpx
import structlog
from fastapi import FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import NoResultFound
from sqlmodel import select
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.deps import DatabaseDep, oidc_provider
from app.frontend.deps import CurrentUser, SessionDep, TemplatesDep, templates
from app.models.session import Session
from app.models.user import User

log = structlog.stdlib.get_logger("frontend")


frontend_app = FastAPI()


@frontend_app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> Any:
    return templates.TemplateResponse(request, name="error.jinja", context={"exc": str(exc.detail)})


frontend_app.add_middleware(SessionMiddleware, secret_key=settings.frontend.cookie.session_key)

frontend_app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent.joinpath("static")),
    name="static",
)


@frontend_app.get("/", response_class=HTMLResponse)
async def index(request: Request, templates: TemplatesDep) -> Any:
    return templates.TemplateResponse(request, name="index.jinja", context={})


@frontend_app.get("/login")
async def login(request: Request, db: DatabaseDep) -> Any:
    provider_info = await oidc_provider.get_metadata()

    required_auth_support = [
        ("response_types_supported", "code"),
        ("response_modes_supported", "form_post"),
        ("grant_types_supported", "authorization_code"),
        ("subject_types_supported", "public"),
        ("token_endpoint_auth_methods_supported", "client_secret_post"),
        # TODO: check for backchannel_logout_supported=True and backchannel_logout_session_supported=True
    ]

    for parameter, required_value in required_auth_support:
        supported_values = getattr(provider_info, parameter)
        if required_value not in supported_values:
            message = "Authentication provider unsupported."
            log.error(
                message,
                **{"requiered_value": required_value, parameter: supported_values},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=message,
            )

    session = Session(
        expires_at=datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(seconds=settings.frontend.cookie.max_age)
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    log.debug("Session created", session_token=session.token)

    query_parameters = urlencode(
        {
            "scope": " ".join(settings.auth.scopes),
            "response_type": "code",
            "client_id": settings.auth.client_id,
            "redirect_uri": request.url_for("auth"),
            "state": session.auth_state,
            "response_mode": "form_post",
            "nonce": session.auth_nonce,
        }
    )
    login_url = f"{provider_info.authorization_endpoint}?{query_parameters}"
    response = RedirectResponse(url=login_url)

    # set session cookie
    response.set_cookie(
        key="session_token", value=str(session.token), max_age=settings.frontend.cookie.max_age, httponly=True
    )

    return response


async def get_session_from_state(db: DatabaseDep, state: str) -> Session:
    try:
        result = await db.exec(select(Session).where(Session.auth_state == state))
        session: Session = result.one()
    except NoResultFound:
        log.debug("Unknown session auth_state", session_auth_state=state)
        return Session()

    log.debug("Session found", session_token=session.token)
    if not session.is_active():
        log.debug("Session is not active", session_token=session.token)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is not active",
        )
    log.debug("Session active", session_token=session.token)

    # verify state matches against session data
    if not state == session.auth_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication response invalid: state mismatch",
        )

    return session


@frontend_app.post("/auth")
async def auth(
    code: Annotated[str, Form()],
    state: Annotated[str, Form()],
    request: Request,
    db: DatabaseDep,
) -> Any:
    log.info("auth response received", auth_code=code, auth_state=state)

    session = await get_session_from_state(db, state)

    provider_info = await oidc_provider.get_metadata()

    # use code to get id_token (and maybe access_token?)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            token_response = await client.post(
                str(provider_info.token_endpoint),
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": request.url_for("auth"),
                    "client_id": settings.auth.client_id,
                    "client_secret": settings.auth.client_secret,
                },
            )
            token_response.raise_for_status()
            tokens = token_response.json()
            # TODO: fully validate id_token (https://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation)
            userinfo = await oidc_provider.decode_token(tokens["id_token"], nonce=session.auth_nonce)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch id token from provider.",
        ) from exc

    log.info("userinfo", userinfo=userinfo)
    if not userinfo:
        log.debug("Failed to fetch userinfo")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch userinfo.",
        )

    # get or create user
    try:
        result = await db.exec(select(User).where(User.email == userinfo["email"]))
        user = result.one()
    except NoResultFound:
        # create user
        log.debug("User not found in DB, creating entry from the id token")
        user_create = User(email=userinfo["email"], name=userinfo["name"], username=userinfo["preferred_username"])
        db.add(user_create)
        await db.commit()
        await db.refresh(user_create)
        log.debug("User created", user=user_create)
        user = User.model_validate(user_create)

    session.user_id = user.id
    db.add(session)
    await db.commit()
    await db.refresh(session)
    log.debug("User login successful", user_id=user.id)

    return RedirectResponse(url=request.url_for("index"), status_code=status.HTTP_303_SEE_OTHER)


@frontend_app.get("/logout")
async def logout(session: SessionDep, db: DatabaseDep) -> RedirectResponse:
    if session:
        # if session is still active
        session.logged_out_at = datetime.datetime.now(tz=datetime.UTC)
        session.updated_at = datetime.datetime.now(tz=datetime.UTC)
        db.add(session)
        await db.commit()
        await db.refresh(session)

    response = RedirectResponse(url="/")
    # delete session cookie
    response.delete_cookie(key="session_token", httponly=True)

    return response


@frontend_app.get("/items", response_class=HTMLResponse)
async def items_index(request: Request, templates: TemplatesDep, user: CurrentUser) -> Any:
    return templates.TemplateResponse(request, name="items/index.jinja", context={})


@frontend_app.get("/items/list", response_class=HTMLResponse)
async def _list(request: Request, templates: TemplatesDep, user: CurrentUser) -> Any:
    return templates.TemplateResponse(request, name="items/components/list.jinja", context={"items": [{"name": "bar"}]})
