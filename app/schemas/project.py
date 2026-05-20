from datetime import datetime

from pydantic import BaseModel, Field

from app.models.project import ProjectRole


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    icon: str | None = None
    category_id: int = Field(...)


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    icon: str | None = None
    category_id: int | None = None


class ProjectMemberAdd(BaseModel):
    user_id: int = Field(..., description='ID пользователя')
    role: ProjectRole = ProjectRole.MEMBER


class ProjectMemberResponse(BaseModel):
    id: int
    user_id: int
    project_id: int
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class ProjectResponse(BaseModel):
    id: int
    name: str
    icon: str | None = None
    category_id: int
    owner_id: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True
