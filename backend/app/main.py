from collections.abc import Awaitable, Callable
from importlib.metadata import metadata

import humps
from fastapi import FastAPI, Request, Response
from fastapi.routing import APIRoute
from fastapi_pagination import add_pagination
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

add_pagination(app)

app.include_router(api_router)

@app.middleware("http")
async def add_link_headers(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    response: Response = await call_next(request)

    base_url = f"{request.url.scheme}://{request.url.netloc}"
    openapi_url = f"{base_url}{request.app.openapi_url}"
    docs_url = f"{base_url}{request.app.docs_url}"

    response.headers.append("Link", f'<{openapi_url}>; rel="service-desc"')
    response.headers.append("Link", f'<{openapi_url}>; rel="describedby"')
    response.headers.append("Link", f'<{docs_url}>; rel="service-doc"')
    response.headers.append("Link", f'<{docs_url}>; rel="help"')
    return response
