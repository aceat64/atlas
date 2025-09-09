import datetime
from pathlib import Path
from typing import Any

import structlog
from authlib.integrations.starlette_client import OAuth
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import NoResultFound
from sqlmodel import select
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.deps import DatabaseDep
from app.frontend.deps import CurrentUser, SessionDep, TemplatesDep, templates
from app.models.session import Session
from app.models.user import User

log = structlog.stdlib.get_logger("frontend")

oauth = OAuth()  # type: ignore
oauth.register(
    name="oidc",
    client_id=settings.oauth2_client_id,
    client_secret=settings.oauth2_client_secret,
    server_metadata_url=str(settings.oidc_url),
    client_kwargs={"scope": "openid email profile"},
)

frontend_app = FastAPI()


@frontend_app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> Any:
    return templates.TemplateResponse(request=request, name="error.jinja", context={"exc": str(exc.detail)})


frontend_app.add_middleware(SessionMiddleware, secret_key=settings.frontend.cookie.session_key)

frontend_app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent.joinpath("static")),
    name="static",
)


@frontend_app.get("/", response_class=HTMLResponse)
async def index(request: Request, templates: TemplatesDep) -> Any:
    return templates.TemplateResponse(request=request, name="index.jinja", context={})


@frontend_app.get("/login")
async def login(request: Request) -> Any:
    redirect_uri = request.url_for("auth")
    return await oauth.oidc.authorize_redirect(request, redirect_uri)


@frontend_app.get("/auth")
async def auth(request: Request, db: DatabaseDep) -> Any:
    response = RedirectResponse(url="/")
    token = await oauth.oidc.authorize_access_token(request)
    userinfo = token.get("userinfo")
    if userinfo:
        print(userinfo)
        # get or create user
        try:
            result = await db.exec(select(User).where(User.email == userinfo.email))
            user = result.one()
        except NoResultFound:
            # create user
            log.debug("User not found in DB, creating entry from the access token")
            user_create = User(email=userinfo.email, name=userinfo.name, username=userinfo.preferred_username)
            db.add(user_create)
            await db.commit()
            await db.refresh(user_create)
            log.debug("User created", user=user_create)
            user = User.model_validate(user_create)

        # create session
        session_create = Session(
            expires_at=datetime.datetime.now(tz=datetime.UTC)
            + datetime.timedelta(seconds=settings.frontend.cookie.max_age),
            user_id=user.id,
        )
        db.add(session_create)
        await db.commit()
        await db.refresh(session_create)
        log.debug("Session created", user_session=session_create)
        session = Session.model_validate(session_create)
        print(session)

        # set session cookie
        response.set_cookie(
            key="session_token", value=str(session.token), max_age=settings.frontend.cookie.max_age, httponly=True
        )

    return response


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
