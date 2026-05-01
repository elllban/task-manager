from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.repositories.task_repository import TaskRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.task import TaskCreate, TaskUpdate, TaskFilter, TaskResponse
from app.models.task import Task, TaskPriority
from app.models.user import User
from app.models.project import Project


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.task_repo = TaskRepository(db)
        self.project_repo = ProjectRepository(db)

    async def create_task(self, data: TaskCreate, author: User) -> TaskResponse:
        has_access = await self.project_repo.get_member(data.project_id, author.id)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this project"
            )

        if data.assignee_id:
            assignee_member = await self.project_repo.get_member(data.project_id, data.assignee_id)
            if not assignee_member:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assignee must be a project member"
                )

        if data.parent_id:
            parent_task = await self.task_repo.get(data.parent_id)
            if not parent_task:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent task not found"
                )
            if parent_task.project_id != data.project_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent task must be in the same project"
                )

        task = await self.task_repo.create(
            title=data.title,
            description=data.description,
            project_id=data.project_id,
            author_id=author.id,
            assignee_id=data.assignee_id,
            parent_id=data.parent_id,
            due_date=data.due_date,
            priority=data.priority.value if hasattr(data.priority, 'value') else data.priority
        )

        result = await self.db.execute(
            select(Task)
            .where(Task.id == task.id)
            .options(
                selectinload(Task.assignee),
                selectinload(Task.author),
                selectinload(Task.project).selectinload(Project.category)
            )
        )
        loaded_task = result.scalar_one()
        return TaskResponse.from_task(loaded_task)

    async def get_task(self, task_id: int, current_user: User) -> Optional[Task]:
        task = await self.task_repo.get(task_id)
        if not task:
            return None

        has_access = await self.project_repo.get_member(task.project_id, current_user.id)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this task"
            )

        return task

    async def get_task_with_details(self, task_id: int, current_user: User) -> Optional[TaskResponse]:
        result = await self.db.execute(
            select(Task)
            .where(Task.id == task_id)
            .options(
                selectinload(Task.assignee),
                selectinload(Task.author),
                selectinload(Task.project).selectinload(Project.category)
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            return None

        has_access = await self.project_repo.get_member(task.project_id, current_user.id)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this task"
            )

        return TaskResponse.from_task(task)

    async def get_all_tasks(self, current_user: User) -> List[Task]:
        user_projects = await self.project_repo.get_user_projects(current_user.id)
        project_ids = [p.id for p in user_projects]

        if not project_ids:
            return []

        all_tasks = []
        for project_id in project_ids:
            tasks = await self.task_repo.get_by_project(project_id)
            all_tasks.extend(tasks)

        return all_tasks

    async def get_tasks_with_filters(self, current_user: User, filters: TaskFilter) -> List[TaskResponse]:
        user_projects = await self.project_repo.get_user_projects(current_user.id)
        project_ids = [p.id for p in user_projects]

        if not project_ids:
            return []

        query = (
            select(Task)
            .where(Task.project_id.in_(project_ids))
            .options(
                selectinload(Task.assignee),
                selectinload(Task.author),
                selectinload(Task.project).selectinload(Project.category)
            )
        )

        if filters.project_id:
            if filters.project_id not in project_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this project"
                )
            query = query.where(Task.project_id == filters.project_id        )

        if filters.completed is None:
            query = query.where(Task.completed == False)
        else:
            query = query.where(Task.completed == filters.completed)

        if filters.priority:
            priorities = [p.value if hasattr(p, 'value') else p for p in filters.priority]
            query = query.where(Task.priority.in_(priorities))

        if filters.due_date_from:
            query = query.where(Task.due_date >= filters.due_date_from)

        if filters.due_date_to:
            query = query.where(Task.due_date <= filters.due_date_to)

        result = await self.db.execute(query)
        tasks = result.scalars().all()
        return [TaskResponse.from_task(task) for task in tasks]

    async def get_assigned_tasks_with_filters(
            self,
            user_id: int,
            completed: Optional[bool] = None,
            priority: Optional[List[TaskPriority]] = None
     ) -> List[TaskResponse]:
        query = (
            select(Task)
            .where(Task.assignee_id == user_id)
            .options(
                selectinload(Task.assignee),
                selectinload(Task.author),
                selectinload(Task.project).selectinload(Project.category)
            )
        )

        if completed is not None:
            query = query.where(Task.completed == completed)

        if priority:
            priorities = [p.value if hasattr(p, 'value') else p for p in priority]
            query = query.where(Task.priority.in_(priorities))

        result = await self.db.execute(query)
        tasks = result.scalars().all()
        return [TaskResponse.from_task(task, hide_project_category=True) for task in tasks]

    async def get_assigned_stats(self, user_id: int) -> dict:
        tasks = await self.task_repo.get_by_assignee(user_id)
        return {
            "total": len(tasks),
            "completed": len([t for t in tasks if t.completed]),
            "pending": len([t for t in tasks if not t.completed])
        }

    async def get_calendar_tasks(self, current_user: User, year: int, month: int, completed: Optional[bool] = None, priority: Optional[List[TaskPriority]] = None) -> List[TaskResponse]:
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        user_projects = await self.project_repo.get_user_projects(current_user.id)
        project_ids = [p.id for p in user_projects]

        if not project_ids:
            return []

        query = (
            select(Task)
            .where(
                Task.project_id.in_(project_ids),
                Task.due_date >= start_date,
                Task.due_date < end_date
            )
            .options(
                selectinload(Task.assignee),
                selectinload(Task.author),
                selectinload(Task.project).selectinload(Project.category)
            )
        )

        if completed is not None:
            query = query.where(Task.completed == completed)

        if priority:
            priorities = [p.value if hasattr(p, 'value') else p for p in priority]
            query = query.where(Task.priority.in_(priorities))

        result = await self.db.execute(query)
        tasks = result.scalars().all()
        return [TaskResponse.from_task(task, hide_project_category=(task.assignee_id == current_user.id)) for task in tasks]

    async def update_task(self, task_id: int, data: TaskUpdate, current_user: User) -> Optional[TaskResponse]:
        task = await self.get_task(task_id, current_user)
        if not task:
            return None

        update_data = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}

        if 'priority' in update_data and hasattr(update_data['priority'], 'value'):
            update_data['priority'] = update_data['priority'].value

        if 'assignee_id' in update_data and update_data['assignee_id']:
            assignee_member = await self.project_repo.get_member(task.project_id, update_data['assignee_id'])
            if not assignee_member:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assignee must be a project member"
                )

        updated_task = await self.task_repo.update(task_id, **update_data)
        if not updated_task:
            return None

        result = await self.db.execute(
            select(Task)
            .where(Task.id == task_id)
            .options(
                selectinload(Task.assignee),
                selectinload(Task.author),
                selectinload(Task.project).selectinload(Project.category)
            )
        )
        loaded_task = result.scalar_one()
        return TaskResponse.from_task(loaded_task)

    async def delete_task(self, task_id: int, current_user: User) -> bool:
        task = await self.get_task(task_id, current_user)
        if not task:
            return False

        member = await self.project_repo.get_member(task.project_id, current_user.id)
        if member.role not in ["owner", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owner or admin can delete tasks"
            )

        return await self.task_repo.delete(task_id)

    async def mark_completed(self, task_id: int, completed: bool) -> Optional[Task]:
        return await self.task_repo.update(task_id, completed=completed)

    async def get_tasks_by_project(self, project_id: int, current_user: User) -> List[TaskResponse]:
        has_access = await self.project_repo.get_member(project_id, current_user.id)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this project"
            )
        tasks = await self.task_repo.get_by_project(project_id)

        result = []
        for task in tasks:
            task_result = await self.db.execute(
                select(Task)
                .where(Task.id == task.id)
                .options(
                    selectinload(Task.assignee),
                    selectinload(Task.author),
                    selectinload(Task.project).selectinload(Project.category)
                )
            )
            loaded_task = task_result.scalar_one()
            result.append(TaskResponse.from_task(loaded_task))
        return result

    async def get_calendar_dates(self, current_user: User, year: int, month: int, completed: Optional[bool] = None, priority: Optional[List[TaskPriority]] = None) -> List[str]:
        """Return list of dates (YYYY-MM-DD) that have tasks for the given month."""
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        user_projects = await self.project_repo.get_user_projects(current_user.id)
        project_ids = [p.id for p in user_projects]

        if not project_ids:
            return []

        query = (
            select(func.date(Task.due_date))
            .where(
                Task.project_id.in_(project_ids),
                Task.due_date >= start_date,
                Task.due_date < end_date
            )
        )

        if completed is not None:
            query = query.where(Task.completed == completed)

        if priority:
            priorities = [p.value if hasattr(p, 'value') else p for p in priority]
            query = query.where(Task.priority.in_(priorities))

        query = query.distinct()
        result = await self.db.execute(query)
        dates = result.scalars().all()
        return [d.strftime("%Y-%m-%d") for d in dates if d is not None]