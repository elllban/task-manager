from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AttachmentCreate(BaseModel):
    file_name: str
    file_path: str
    content_type: Optional[str] = None


class AttachmentResponse(BaseModel):
    id: int
    task_id: int
    file_name: str
    file_path: str
    content_type: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True