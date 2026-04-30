from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.repositories.attachment_repository import AttachmentRepository
from app.schemas.attachment import AttachmentCreate
from app.models.attachment import TaskAttachment


class AttachmentService:
    def __init__(self, db: AsyncSession):
        self.repo = AttachmentRepository(db)

    async def create_attachment(self, task_id: int, file_name: str, file_path: str, content_type: str = None) -> TaskAttachment:
        return await self.repo.create(
            task_id=task_id,
            file_name=file_name,
            file_path=file_path,
            content_type=content_type
        )

    async def get_attachment(self, attachment_id: int) -> Optional[TaskAttachment]:
        return await self.repo.get(attachment_id)

    async def get_attachments_by_task(self, task_id: int) -> List[TaskAttachment]:
        return await self.repo.get_by_task(task_id)

    async def delete_attachment(self, attachment_id: int) -> bool:
        attachment = await self.repo.get(attachment_id)
        if not attachment:
            return False
        return await self.repo.delete(attachment_id)