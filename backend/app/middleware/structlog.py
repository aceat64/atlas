import time
import urllib.parse
from typing import TypedDict

import structlog
from asgi_correlation_id import correlation_id
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import settings

app_logger = structlog.stdlib.get_logger("app")
access_logger = structlog.stdlib.get_logger("access")

# Adapted from: https://wazaari.dev/blog/fastapi-structlog-integration


class AccessInfo(TypedDict, total=False):
    status_code: int
    start_time: float


class StructLogMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app
        pass

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # If the request is not an HTTP request, we don't need to do anything special
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=correlation_id.get())

        info = AccessInfo()

        # Inner send function
        async def inner_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                info["status_code"] = message["status"]
            await send(message)

        try:
            info["start_time"] = time.perf_counter_ns()
            await self.app(scope, receive, inner_send)
        except Exception as exc:
            app_logger.error(
                f"An unhandled exception was caught by last resort middleware: {exc}",
                exc_info=settings.log.tracebacks,
            )
            info["status_code"] = 500
            response = JSONResponse(
                status_code=500,
                content={"detail": "An unexpected error occurred."},
            )
            await response(scope, receive, send)
        finally:
            process_time = time.perf_counter_ns() - info["start_time"]
            client_host, client_port = scope["client"]
            url = urllib.parse.quote(scope["path"])
            if scope["query_string"]:
                url = "{}?{}".format(url, scope["query_string"].decode("ascii"))

            # Recreate the Uvicorn access log format,
            # but add all parameters as structured information
            access_logger.info(
                f"""{client_host}:{client_port} - "{scope["method"]} {url} HTTP/{scope["http_version"]}" {info["status_code"]}""",  # noqa: E501
                http={
                    "method": scope["method"],
                    "url": url,
                    "version": scope["http_version"],
                    "status_code": info["status_code"],
                },
                client={"host": client_host, "port": client_port},
                duration=process_time,
            )
