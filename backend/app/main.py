from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from importlib.metadata import metadata

from fastapi import FastAPI
from fastapi_pagination import add_pagination
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings
from app.core.exceptions import dbapi_exception_handler, sqlalchemy_exception_handler
from app.core.logging import setup_logging
from app.core.telemetry import setup_telemetry
from app.utils import generate_unique_route_id

project_metadata = metadata("atlas")

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    # run before app start-up
    yield
    # run after app start-up


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
    generate_unique_id_function=generate_unique_route_id,
    exception_handlers={
        DBAPIError: dbapi_exception_handler,
        SQLAlchemyError: sqlalchemy_exception_handler,
    },
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allow_origins,
    allow_credentials=settings.cors.allow_credentials,
    allow_methods=settings.cors.allow_methods,
    allow_headers=settings.cors.allow_headers,
)
add_pagination(app)

if setup_telemetry():
    FastAPIInstrumentor.instrument_app(app)

app.include_router(api_router)
