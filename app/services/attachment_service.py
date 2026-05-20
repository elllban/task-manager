from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attachment import TaskAttachment
from app.repositories.attachment_repository import AttachmentRepository
from app.repositories.pagination import paginate
from app.schemas.pagination import PaginatedResponse, PaginationParams


class AttachmentService:
    def __init__(self, db: AsyncSession):
        self.repo = AttachmentRepository(db)
        self.db = db

    async def create_attachment(
        self, task_id: int, file_name: str, file_path: str, content_type: str = None
    ) -> TaskAttachment:
        return await self.repo.create(
            task_id=task_id, file_name=file_name, file_path=file_path, content_type=content_type
        )

    async def get_attachment(self, attachment_id: int) -> TaskAttachment | None:
        return await self.repo.get(attachment_id)

    async def get_attachments_by_task(
        self, task_id: int, pagination: PaginationParams = PaginationParams()
    ) -> PaginatedResponse[TaskAttachment]:
        query = select(TaskAttachment).where(TaskAttachment.task_id == task_id)
        return await paginate(self.db, query, pagination)

    async def delete_attachment(self, attachment_id: int) -> bool:
        attachment = await self.repo.get(attachment_id)
        if not attachment:
            return False
        return await self.repo.delete(attachment_id)
