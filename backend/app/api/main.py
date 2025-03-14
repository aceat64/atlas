from fastapi import APIRouter

from app.api.routes import attachments, collections, items, items_tags, rooms, stacks, tags, users
from app.models import Status

api_router = APIRouter()
api_router.include_router(items.router, prefix="/items", tags=["Items"])
api_router.include_router(items_tags.router, prefix="/items", tags=["Item Tags"])
api_router.include_router(attachments.router, prefix="/items", tags=["Item Attachments"])

api_router.include_router(collections.router, prefix="/collections", tags=["Collections"])
api_router.include_router(rooms.router, prefix="/rooms", tags=["Rooms"])
api_router.include_router(stacks.router, prefix="/stacks", tags=["Stacks"])
api_router.include_router(tags.router, prefix="/tags", tags=["Tags"])

api_router.include_router(users.router, prefix="/users", tags=["Users"])


@api_router.get("/livez", tags=["internal"])
async def livez() -> Status:
    """Must always return a 200 status or the container will be killed."""
    return Status()


@api_router.get("/readyz", tags=["internal"])
async def readyz() -> Status:
    """Returns a 200 status code."""
    return Status()
