from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import List, Optional
from app.models.task import Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    def __init__(self, db: AsyncSession):
        super().__init__(Task, db)

    async def get_by_project(self, project_id: int) -> List[Task]:
        result = await self.db.execute(
            select(Task).where(Task.project_id == project_id)
        )
        return result.scalars().all()

    async def get_by_assignee(self, assignee_id: int, completed: Optional[bool] = None) -> List[Task]:
        query = select(Task).where(Task.assignee_id == assignee_id)
        if completed is not None:
            query = query.where(Task.completed == completed)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_due_date_range(self, start_date: datetime, end_date: datetime) -> List[Task]:
        result = await self.db.execute(
            select(Task).where(
                Task.due_date >= start_date,
                Task.due_date <= end_date
            )
        )
        return result.scalars().all()

    async def get_by_due_date_range_and_projects(
            self, start_date: datetime, end_date: datetime, project_ids: List[int]
    ) -> List[Task]:
        result = await self.db.execute(
            select(Task).where(
                Task.due_date >= start_date,
                Task.due_date <= end_date,
                Task.project_id.in_(project_ids)
            )
        )
        return result.scalars().all()