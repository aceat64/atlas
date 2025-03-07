import hashlib

from fastapi import APIRouter, HTTPException, UploadFile

from app.api.deps import CurrentUser, SessionDep
from app.models import Message
from app.models.attachment import Attachment
from app.models.item import Item

router = APIRouter()


@router.post("/{item_id}/attachment")
def create_attachment(
    session: SessionDep,
    user: CurrentUser,
    item_id: int,
    file: UploadFile,
) -> Attachment:
    """
    Upload and attach a file to a Item
    """
    item: Item | None = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    attachment = Attachment.model_validate(
        {
            "item_id": item_id,
            "filename": file.filename,
            "mime_type": file.content_type,
            "filesize": file.size,
            "checksum": hashlib.file_digest(file, "sha3_256"),  # type: ignore
        }
    )
    session.add(attachment)
    # TODO: Upload file to object storage service (S3)
    session.commit()
    session.refresh(attachment)
    return attachment


@router.delete("/{item_id}/attachment/{attachment_id}")
def delete_attachment(
    session: SessionDep,
    user: CurrentUser,
    item_id: int,
    attachment_id: int,
) -> Message:
    """
    Delete a file attachment.
    """
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    attachment = session.get(Attachment, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    session.delete(attachment)
    #  TODO: Delete file from object storage service (S3)
    session.commit()
    return Message(message="Attachment deleted successfully")
