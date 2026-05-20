import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

NAME_PATTERN = re.compile(r'^[A-Za-zА-Яа-я\-]+$')


class UserUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
    email: EmailStr | None = None
    avatar: str | None = None

    @field_validator('name')
    def validate_name(cls, v):
        if v is not None and not NAME_PATTERN.match(v):
            raise ValueError('Name must contain only A-Z a-z А-Я а-я -')
        return v


class UserResponse(BaseModel):
    id: int
    email: str
    name: str | None = None
    avatar: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
