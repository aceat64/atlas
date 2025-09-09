from fastapi import APIRouter

from app.api.routes import attachments, collections, items, items_tags, rooms, stacks, tags, users

api_router = APIRouter()
api_router.include_router(items.router, prefix="/items", tags=["Items"])
api_router.include_router(items_tags.router, prefix="/items", tags=["Item Tags"])
api_router.include_router(attachments.router, prefix="/items", tags=["Item Attachments"])

api_router.include_router(collections.router, prefix="/collections", tags=["Collections"])
api_router.include_router(rooms.router, prefix="/rooms", tags=["Rooms"])
api_router.include_router(stacks.router, prefix="/stacks", tags=["Stacks"])
api_router.include_router(tags.router, prefix="/tags", tags=["Tags"])

api_router.include_router(users.router, prefix="/users", tags=["Users"])
