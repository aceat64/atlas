import structlog
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

from app.core.config import settings

log = structlog.stdlib.get_logger("app")


async def dbapi_exception_handler(request: Request, exc: DBAPIError) -> JSONResponse:
    log.error(
        f"DBAPIError: {exc.orig}",
        statement=exc.statement,
        params=exc.params,
        exc_info=settings.log.tracebacks,
    )
    raise HTTPException(status_code=500, detail="An unexpected error occurred.")


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    log.error(
        f"SQLAlchemyError: {exc}",
        exc_info=settings.log.tracebacks,
    )
    raise HTTPException(status_code=500, detail="An unexpected error occurred.")
