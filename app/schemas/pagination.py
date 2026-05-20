from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar('T')


class PaginationParams(BaseModel):
    page: int = 1
    size: int = 20

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        return self.size


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def create(cls, items: list[T], total: int, page: int, size: int) -> 'PaginatedResponse[T]':
        pages = (total + size - 1) // size if total > 0 else 0
        return cls(items=items, total=total, page=page, size=size, pages=pages)
