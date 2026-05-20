from typing import Generic, TypeVar

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

ModelType = TypeVar('ModelType')


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def create(self, **kwargs) -> ModelType:
        stmt = insert(self.model).values(**kwargs).returning(self.model)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.scalar_one()

    async def get(self, id: int) -> ModelType | None:
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        result = await self.db.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()

    async def update(self, id: int, **kwargs) -> ModelType | None:
        stmt = update(self.model).where(self.model.id == id).values(**kwargs).returning(self.model)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.scalar_one_or_none()

    async def delete(self, id: int) -> bool:
        result = await self.db.execute(delete(self.model).where(self.model.id == id).returning(self.model.id))
        await self.db.commit()
        return result.scalar_one_or_none() is not None

    async def exists(self, id: int) -> bool:
        result = await self.db.execute(select(func.count()).select_from(self.model).where(self.model.id == id))
        return result.scalar() > 0
