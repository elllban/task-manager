from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import os
import uuid

from app.api.deps import get_db_dep, get_current_active_user, require_task_access
from app.services.attachment_service import AttachmentService
from app.schemas.attachment import AttachmentResponse
from app.models.user import User
from app.repositories.task_repository import TaskRepository
from app.repositories.project_repository import ProjectRepository

router = APIRouter(prefix="/attachments", tags=["attachments"])

UPLOAD_DIR = "uploads/attachments"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/tasks/{task_id}")
async def upload_attachment(
        task_id: int,
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_active_user),
        _: bool = Depends(require_task_access),
        db: AsyncSession = Depends(get_db_dep)
):
    ext = file.filename.split(".")[-1] if "." in file.filename else ""
    filename = f"{uuid.uuid4()}.{ext}" if ext else str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    service = AttachmentService(db)
    attachment = await service.create_attachment(
        task_id,
        file.filename,
        file_path,
        file.content_type
    )

    return {
        "id": attachment.id,
        "file_name": attachment.file_name,
        "file_size": len(content),
        "content_type": file.content_type
    }


@router.get("/tasks/{task_id}", response_model=List[AttachmentResponse])
async def get_task_attachments(
        task_id: int,
        current_user: User = Depends(get_current_active_user),
        _: bool = Depends(require_task_access),
        db: AsyncSession = Depends(get_db_dep)
):
    service = AttachmentService(db)
    return await service.get_attachments_by_task(task_id)


@router.get("/{attachment_id}/download")
async def download_attachment(
        attachment_id: int,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_dep)
):
    service = AttachmentService(db)
    attachment = await service.get_attachment(attachment_id)
    if not attachment:
        raise HTTPException(404, "Attachment not found")

    task_repo = TaskRepository(db)
    task = await task_repo.get(attachment.task_id)

    project_repo = ProjectRepository(db)
    has_access = await project_repo.get_member(task.project_id, current_user.id)

    if not has_access:
        raise HTTPException(403, "Access denied")

    if not os.path.exists(attachment.file_path):
        raise HTTPException(404, "File not found")

    return FileResponse(
        attachment.file_path,
        media_type=attachment.content_type or 'application/octet-stream',
        filename=attachment.file_name
    )


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
        attachment_id: int,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_dep)
):
    service = AttachmentService(db)

    attachment = await service.get_attachment(attachment_id)
    if not attachment:
        raise HTTPException(404, "Attachment not found")

    task_repo = TaskRepository(db)
    task = await task_repo.get(attachment.task_id)

    project_repo = ProjectRepository(db)
    member = await project_repo.get_member(task.project_id, current_user.id)

    if not member or member.role not in ["owner", "admin"]:
        raise HTTPException(403, "Only project admin/owner can delete attachments")

    if os.path.exists(attachment.file_path):
        os.remove(attachment.file_path)

    deleted = await service.delete_attachment(attachment_id)
    if not deleted:
        raise HTTPException(404, "Attachment not found")

    return {"message": "Attachment deleted"}