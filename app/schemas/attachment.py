from datetime import datetime

from pydantic import BaseModel


class AttachmentCreate(BaseModel):
    file_name: str
    file_path: str
    content_type: str | None = None


class AttachmentResponse(BaseModel):
    id: int
    task_id: int
    file_name: str
    file_path: str
    content_type: str | None = None
    uploaded_at: datetime

    class Config:
        from_attributes = True
