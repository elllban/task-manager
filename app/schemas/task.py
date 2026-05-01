from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List
from app.models.task import TaskPriority


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    project_id: int = Field(...)
    assignee_id: Optional[int] = Field(None)
    parent_id: Optional[int] = Field(None)
    due_date: Optional[datetime] = None
    priority: Optional[str] = Field("not_urgent", pattern="^(very_urgent|urgent|can_wait|not_urgent)$")

    @field_validator('title')
    def title_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    assignee_id: Optional[int] = Field(None)
    due_date: Optional[datetime] = None
    priority: Optional[str] = Field(None, pattern="^(very_urgent|urgent|can_wait|not_urgent)$")
    completed: Optional[bool] = None

    @field_validator('title')
    def title_not_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Title cannot be empty')
        return v.strip() if v else v


class TaskFilter(BaseModel):
    project_id: Optional[int] = None
    completed: Optional[bool] = None
    priority: Optional[List[TaskPriority]] = None
    due_date_from: Optional[datetime] = None
    due_date_to: Optional[datetime] = None
    has_completed_subtasks: Optional[bool] = None


class UserBrief(BaseModel):
    id: int
    name: Optional[str] = None
    email: str

    class Config:
        from_attributes = True


class ProjectBrief(BaseModel):
    id: int
    name: str
    icon: Optional[str] = None


class CategoryBrief(BaseModel):
    id: int
    name: str
    color: str


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    preview_description: Optional[str] = None
    project_id: int
    project: Optional[ProjectBrief] = None
    category: Optional[CategoryBrief] = None
    author_id: Optional[int] = None
    author: Optional[UserBrief] = None
    assignee_id: Optional[int] = None
    assignee: Optional[UserBrief] = None
    parent_id: Optional[int] = None
    due_date: Optional[datetime] = None
    priority: str
    priority_color: Optional[str] = None
    completed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_task(cls, task: "Task", hide_project_category: bool = False) -> "TaskResponse":
        preview = None
        if task.description:
            preview = task.description[:100] + "..." if len(task.description) > 100 else task.description

        priority_colors = {
            "very_urgent": "red",
            "urgent": "orange",
            "can_wait": "yellow",
            "not_urgent": "green"
        }

        return cls(
            id=task.id,
            title=task.title,
            description=task.description,
            preview_description=preview,
            project_id=task.project_id,
            project=ProjectBrief(
                id=task.project.id,
                name=task.project.name,
                icon=task.project.icon
            ) if task.project and not hide_project_category else None,
            category=CategoryBrief(
                id=task.project.category.id,
                name=task.project.category.name,
                color=task.project.category.color
            ) if task.project and task.project.category and not hide_project_category else None,
            author_id=task.author_id,
            author=UserBrief(
                id=task.author.id,
                name=task.author.name,
                email=task.author.email
            ) if task.author else None,
            assignee_id=task.assignee_id,
            assignee=UserBrief(
                id=task.assignee.id,
                name=task.assignee.name,
                email=task.assignee.email
            ) if task.assignee else None,
            parent_id=task.parent_id,
            due_date=task.due_date,
            priority=task.priority,
            priority_color=priority_colors.get(task.priority, "gray"),
            completed=task.completed,
            created_at=task.created_at,
            updated_at=task.updated_at
        )