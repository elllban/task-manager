from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, field_validator

from app.models.task import TaskPriority

if TYPE_CHECKING:
    from app.models.task import Task


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    project_id: int = Field(...)
    assignee_id: int | None = Field(None)
    parent_id: int | None = Field(None)
    due_date: datetime | None = None
    priority: str | None = Field('not_urgent', pattern='^(very_urgent|urgent|can_wait|not_urgent)$')

    @field_validator('title')
    def title_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()


class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    assignee_id: int | None = Field(None)
    due_date: datetime | None = None
    priority: str | None = Field(None, pattern='^(very_urgent|urgent|can_wait|not_urgent)$')
    completed: bool | None = None

    @field_validator('title')
    def title_not_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Title cannot be empty')
        return v.strip() if v else v


class TaskFilter(BaseModel):
    project_id: int | None = None
    completed: bool | None = None
    priority: list[TaskPriority] | None = None
    due_date_from: datetime | None = None
    due_date_to: datetime | None = None
    has_completed_subtasks: bool | None = None


class UserBrief(BaseModel):
    id: int
    name: str | None = None
    email: str

    class Config:
        from_attributes = True


class ProjectBrief(BaseModel):
    id: int
    name: str
    icon: str | None = None


class CategoryBrief(BaseModel):
    id: int
    name: str
    color: str


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    preview_description: str | None = None
    project_id: int
    project: ProjectBrief | None = None
    category: CategoryBrief | None = None
    author_id: int | None = None
    author: UserBrief | None = None
    assignee_id: int | None = None
    assignee: UserBrief | None = None
    parent_id: int | None = None
    due_date: datetime | None = None
    priority: str
    priority_color: str | None = None
    completed: bool
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True

    @classmethod
    def from_task(cls, task: Task, hide_project_category: bool = False) -> TaskResponse:
        preview = None
        if task.description:
            preview = task.description[:100] + '...' if len(task.description) > 100 else task.description

        priority_colors = {'very_urgent': 'red', 'urgent': 'orange', 'can_wait': 'yellow', 'not_urgent': 'green'}

        return cls(
            id=task.id,
            title=task.title,
            description=task.description,
            preview_description=preview,
            project_id=task.project_id,
            project=ProjectBrief(id=task.project.id, name=task.project.name, icon=task.project.icon)
            if task.project and not hide_project_category
            else None,
            category=CategoryBrief(
                id=task.project.category.id, name=task.project.category.name, color=task.project.category.color
            )
            if task.project and task.project.category and not hide_project_category
            else None,
            author_id=task.author_id,
            author=UserBrief(id=task.author.id, name=task.author.name, email=task.author.email)
            if task.author
            else None,
            assignee_id=task.assignee_id,
            assignee=UserBrief(id=task.assignee.id, name=task.assignee.name, email=task.assignee.email)
            if task.assignee
            else None,
            parent_id=task.parent_id,
            due_date=task.due_date,
            priority=task.priority,
            priority_color=priority_colors.get(task.priority, 'gray'),
            completed=task.completed,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
