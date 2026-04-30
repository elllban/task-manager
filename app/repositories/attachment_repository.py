from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.models.attachment import TaskAttachment
from app.repositories.base import BaseRepository


class AttachmentRepository(BaseRepository[TaskAttachment]):
    def __init__(self, db: AsyncSession):
        super().__init__(TaskAttachment, db)

    async def get_by_task(self, task_id: int) -> List[TaskAttachment]:
        result = await self.db.execute(
            select(TaskAttachment).where(TaskAttachment.task_id == task_id)
        )
        return result.scalars().all()