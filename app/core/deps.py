from typing import Annotated

from fastapi import Depends
from obstore.store import S3Store
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth.oidc import Provider
from app.core.config import settings
from app.core.db import get_db
from app.core.s3 import get_object_store

DatabaseDep = Annotated[AsyncSession, Depends(get_db)]
"""Get a database session instance"""

ObjectStoreDep = Annotated[S3Store, Depends(get_object_store)]
"""Get an S3Store instance"""

oidc_provider = Provider(settings.auth.oidc_url)
