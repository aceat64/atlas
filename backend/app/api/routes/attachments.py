import hashlib
from collections.abc import AsyncGenerator

import aioboto3  # type: ignore[import-untyped]
from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser, SessionDep, default_responses
from app.core.config import settings
from app.models import Message
from app.models.attachment import Attachment
from app.models.item import Item
from app.utils import content_disposition_header

router = APIRouter()

hash_chunk_size = 1024 * 1024  # 1MB chunks
s3_chunk_size = hash_chunk_size


@router.post("/{item_id}/attachment", responses=default_responses)
async def create_attachment(
    session: SessionDep, user: CurrentUser, item_id: int, file: UploadFile
) -> Attachment:
    """Upload and attach a file to an item."""

    item = await session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    attachment = Attachment.model_validate(
        {
            "item_id": item.id,
            "filename": file.filename,
            "content_type": file.content_type,
            "filesize": file.size,
        }
    )
    session.add(attachment)
    await session.commit()
    await session.refresh(attachment)

    # Calculate sha256sum of the file in chucks so we don't have to load it all into memory
    hash_obj = hashlib.sha256()
    while content := await file.read(hash_chunk_size):
        hash_obj.update(content)
    attachment.checksum_sha256 = hash_obj.hexdigest()
    await file.seek(0)

    # TODO: Move s3 client setup to deps?
    boto_session = aioboto3.Session(
        aws_access_key_id=settings.s3.access_key_id,
        aws_secret_access_key=settings.s3.secret_access_key,
        region_name=settings.s3.region_name,
    )
    async with boto_session.client("s3", endpoint_url=str(settings.s3.url)) as s3:
        try:
            await s3.upload_fileobj(
                file,
                settings.s3.bucket_name,
                f"{settings.s3.path_prefix}item_{attachment.item_id}/attachments/{attachment.id}",
                ExtraArgs={"ContentType": attachment.content_type},
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Upload failed: {exc}") from exc

    # Update checksum in db now that file has been uploaded
    session.add(attachment)
    await session.commit()
    await session.refresh(attachment)
    return attachment


async def get_s3_chunk(attachment: Attachment) -> AsyncGenerator[bytes]:
    """Streaming download of an S3 object."""

    # TODO: Move s3 client setup to deps?
    boto_session = aioboto3.Session(
        aws_access_key_id=settings.s3.access_key_id,
        aws_secret_access_key=settings.s3.secret_access_key,
        region_name=settings.s3.region_name,
    )
    async with boto_session.client("s3", endpoint_url=str(settings.s3.url)) as s3:
        s3_obj = await s3.get_object(
            Bucket=settings.s3.bucket_name,
            Key=f"{settings.s3.path_prefix}item_{attachment.item_id}/attachments/{attachment.id}",
        )
        async with s3_obj["Body"] as stream:
            yield await stream.read()


# TODO: Add 200 to responses
@router.get(
    "/{item_id}/attachment/{attachment_id}",
    responses=default_responses,
    response_class=StreamingResponse,
)
async def get_attachment(
    session: SessionDep, user: CurrentUser, item_id: int, attachment_id: int
) -> StreamingResponse:
    """Download an attached file."""

    item = await session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    attachment = await session.get(Attachment, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    return StreamingResponse(
        content=get_s3_chunk(attachment),
        media_type=attachment.content_type,
        headers={
            "Content-Disposition": content_disposition_header(attachment.filename, "attachment")
        },
    )


@router.delete("/{item_id}/attachment/{attachment_id}", responses=default_responses)
async def delete_attachment(
    session: SessionDep, user: CurrentUser, item_id: int, attachment_id: int
) -> Message:
    """Delete a file attachment."""

    item = await session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    attachment = await session.get(Attachment, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Delete database entry (but don't commit yet)
    await session.delete(attachment)

    # TODO: Move s3 client setup to deps?
    boto_session = aioboto3.Session(
        aws_access_key_id=settings.s3.access_key_id,
        aws_secret_access_key=settings.s3.secret_access_key,
        region_name=settings.s3.region_name,
    )
    async with boto_session.client("s3", endpoint_url=str(settings.s3.url)) as s3:
        try:
            await s3.delete_object(
                Bucket=settings.s3.bucket_name,
                Key=f"{settings.s3.path_prefix}item_{attachment.item_id}/attachments/{attachment.id}",
            )
        except Exception as exc:
            # TODO: Test out various failure modes, we may still want to delete the db entry
            raise HTTPException(status_code=500, detail=f"Delete failed: {exc}") from exc

    # File deleted from bucket, so we can delete the db entry
    await session.commit()
    return Message(detail="Attachment deleted successfully")
