from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.project import ProjectRole


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    icon: Optional[str] = None
    category_id: int = Field(...)


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    icon: Optional[str] = None
    category_id: Optional[int] = None


class ProjectMemberAdd(BaseModel):
    user_id: int = Field(..., description="ID пользователя")
    role: ProjectRole = ProjectRole.MEMBER


class ProjectResponse(BaseModel):
    id: int
    name: str
    icon: Optional[str] = None
    category_id: int
    owner_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True