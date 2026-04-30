from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.models.category import Category


class CategoryService:
    def __init__(self, db: AsyncSession):
        self.repo = CategoryRepository(db)

    async def create_category(self, data: CategoryCreate) -> Category:
        return await self.repo.create(name=data.name, color=data.color)

    async def get_category(self, category_id: int) -> Optional[Category]:
        return await self.repo.get(category_id)

    async def get_all_categories(self) -> List[Category]:
        return await self.repo.get_all()

    async def update_category(self, category_id: int, data: CategoryUpdate) -> Optional[Category]:
        update_data = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not update_data:
            return await self.get_category(category_id)
        return await self.repo.update(category_id, **update_data)

    async def delete_category(self, category_id: int) -> bool:
        category = await self.repo.get(category_id)
        if not category:
            return False
        return await self.repo.delete(category_id)