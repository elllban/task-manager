from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional
import re

NAME_PATTERN = re.compile(r'^[A-Za-zА-Яа-я\-]+$')

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    avatar: Optional[str] = None

    @field_validator('name')
    def validate_name(cls, v):
        if v is not None and not NAME_PATTERN.match(v):
            raise ValueError('Name must contain only A-Z a-z А-Я а-я -')
        return v


class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    avatar: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True