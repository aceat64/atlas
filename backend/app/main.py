from importlib.metadata import metadata

import humps
import structlog
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi_pagination import add_pagination
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings
from app.middleware.structlog import StructLogMiddleware

log = structlog.stdlib.get_logger("app")
project_metadata = metadata("atlas")


def custom_generate_unique_id(route: APIRoute) -> str:
    route_tag = humps.pascalize(str(route.tags[0]))
    route_name = humps.pascalize(route.name)
    return f"{route_tag}_{route_name}"


app = FastAPI(
    title="ATLAS",
    version=project_metadata["Version"],
    summary=project_metadata["Summary"],
    description=project_metadata["Description"],
    # Configure Swagger UI so that auth and "try it now" work
    swagger_ui_init_oauth={
        "clientId": "atlas",
        "usePkceWithAuthorizationCodeGrant": True,
        "scopes": "openid profile email",
    },
    swagger_ui_parameters={"tryItOutEnabled": True, "persistAuthorization": True},
    generate_unique_id_function=custom_generate_unique_id,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allow_origins,
    allow_credentials=settings.cors.allow_credentials,
    allow_methods=settings.cors.allow_methods,
    allow_headers=settings.cors.allow_headers,
)


@app.exception_handler(DBAPIError)
async def dbapi_exception_handler(request: Request, exc: DBAPIError) -> JSONResponse:
    log.error(
        f"DBAPIError: {exc.orig}",
        statement=exc.statement,
        params=exc.params,
        exc_info=settings.log.tracebacks,
    )
    raise HTTPException(status_code=500, detail="An unexpected error occurred.")


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    log.error(
        f"SQLAlchemyError: {exc}",
        exc_info=settings.log.tracebacks,
    )
    raise HTTPException(status_code=500, detail="An unexpected error occurred.")


app.add_middleware(StructLogMiddleware)
app.add_middleware(CorrelationIdMiddleware)

add_pagination(app)
app.include_router(api_router)