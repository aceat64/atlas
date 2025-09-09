import hashlib
from typing import Any

import obstore
import structlog
from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from opentelemetry import trace
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.trace import SpanKind, Status, StatusCode

from app.api.deps import CurrentUser, default_responses
from app.core.deps import DatabaseDep, ObjectStoreDep
from app.models import Message
from app.models.attachment import Attachment, AttachmentPublic
from app.models.item import Item
from app.utils import content_disposition_header

router = APIRouter()

hash_chunk_size = 1024 * 1024  # 1MB chunks
s3_chunk_size = hash_chunk_size

log = structlog.stdlib.get_logger("app")
obstore_tracer = trace.get_tracer("instrumentation.obstore")


def attachment_path(attachment: Attachment) -> str:
    return f"item_{attachment.item_id}/attachments/{attachment.id}"


@router.post("/{item_id}/attachment", responses=default_responses, response_model=AttachmentPublic)
async def create_attachment(
    session: DatabaseDep, user: CurrentUser, store: ObjectStoreDep, item_id: int, file: UploadFile
) -> Any:
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

    with obstore_tracer.start_as_current_span("PUT", kind=SpanKind.CLIENT) as span:
        span.set_attribute(SpanAttributes.HTTP_REQUEST_METHOD, "PUT")
        try:
            path = attachment_path(attachment)
            await obstore.put_async(store, path, file.file)
        except Exception as exc:
            span.set_status(Status(StatusCode.ERROR))
            span.record_exception(exc)
            log.error(
                "Upload failed",
                item_id=item_id,
                attachment_id=attachment.id,
                attachment_path=path,
                exc_info=exc,
            )
            raise HTTPException(status_code=500, detail="Upload failed") from exc

    # Update checksum in db now that file has been uploaded
    session.add(attachment)
    await session.commit()
    await session.refresh(attachment)
    log.debug(
        "Attachment uploaded",
        item_id=item_id,
        attachment_id=attachment.id,
        attachment_path=path,
    )
    return attachment


# TODO: Add 200 to responses
@router.get(
    "/{item_id}/attachment/{attachment_id}",
    responses=default_responses,
    response_class=StreamingResponse,
)
async def get_attachment(
    session: DatabaseDep, user: CurrentUser, store: ObjectStoreDep, item_id: int, attachment_id: int
) -> StreamingResponse:
    """Download an attached file."""

    item = await session.get(Item, item_id)
    if not item:
        log.debug("Item not found", item_id=item_id)
        raise HTTPException(status_code=404, detail="Item not found")

    attachment = await session.get(Attachment, attachment_id)
    if not attachment:
        log.debug("Attachment not found", item_id=item_id, attachment_id=attachment_id)
        raise HTTPException(status_code=404, detail="Attachment not found")

    with obstore_tracer.start_as_current_span("GET", kind=SpanKind.CLIENT) as span:
        span.set_attribute(SpanAttributes.HTTP_REQUEST_METHOD, "GET")
        try:
            path = attachment_path(attachment)
            resp = await obstore.get_async(store, path)
            return StreamingResponse(
                content=resp,
                media_type=attachment.content_type,
                headers={"Content-Disposition": content_disposition_header(attachment.filename, "attachment")},
            )
        except FileNotFoundError as exc:
            log.debug(
                "Attachment not found in object store",
                item_id=item_id,
                attachment_id=attachment_id,
                attachment_path=path,
            )
            raise HTTPException(status_code=404, detail="Attachment not found in object store") from exc
        except Exception as exc:
            span.set_status(Status(StatusCode.ERROR))
            span.record_exception(exc)
            log.error(
                "Download failed",
                item_id=item_id,
                attachment_id=attachment_id,
                attachment_path=path,
                exc_info=exc,
            )
            raise HTTPException(status_code=500, detail="Download failed") from exc


@router.delete("/{item_id}/attachment/{attachment_id}", responses=default_responses)
async def delete_attachment(
    session: DatabaseDep, user: CurrentUser, store: ObjectStoreDep, item_id: int, attachment_id: int
) -> Message:
    """Delete a file attachment."""

    item = await session.get(Item, item_id)
    if not item:
        log.debug("Item not found", item_id=item_id)
        raise HTTPException(status_code=404, detail="Item not found")

    attachment = await session.get(Attachment, attachment_id)
    if not attachment:
        log.debug("Attachment not found", item_id=item_id, attachment_id=attachment_id)
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Delete database entry (but don't commit yet)
    await session.delete(attachment)

    with obstore_tracer.start_as_current_span("DELETE", kind=SpanKind.CLIENT) as span:
        span.set_attribute(SpanAttributes.HTTP_REQUEST_METHOD, "DELETE")
        # Delete from object store
        try:
            path = attachment_path(attachment)
            await obstore.delete_async(store, path)
        except FileNotFoundError as exc:
            span.set_status(Status(StatusCode.ERROR))
            span.record_exception(exc)
            # This may not be needed
            # delete_async() doesn't seem to raise a FileNotFoundError exception
            log.warning(
                "File was missing from object store",
                item_id=item_id,
                attachment_id=attachment_id,
                attachment_path=path,
                exc_info=exc,
            )

    # File deleted from bucket, so we can delete the db entry
    await session.commit()
    log.debug(
        "Attachment deleted",
        item_id=item_id,
        attachment_id=attachment_id,
        attachment_path=path,
    )
    return Message(detail="Attachment deleted successfully")
