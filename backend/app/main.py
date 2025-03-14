from importlib.metadata import metadata

import humps
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings

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

app.include_router(api_router)
