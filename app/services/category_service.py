from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.repositories.pagination import paginate
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.schemas.pagination import PaginatedResponse, PaginationParams


class CategoryService:
    def __init__(self, db: AsyncSession):
        self.repo = CategoryRepository(db)
        self.db = db

    async def create_category(self, data: CategoryCreate) -> Category:
        return await self.repo.create(name=data.name, color=data.color)

    async def get_category(self, category_id: int) -> Category | None:
        return await self.repo.get(category_id)

    async def get_all_categories(
        self, pagination: PaginationParams = PaginationParams()
    ) -> PaginatedResponse[Category]:
        query = select(Category)
        return await paginate(self.db, query, pagination)

    async def update_category(self, category_id: int, data: CategoryUpdate) -> Category | None:
        update_data = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not update_data:
            return await self.get_category(category_id)
        return await self.repo.update(category_id, **update_data)

    async def delete_category(self, category_id: int) -> bool:
        category = await self.repo.get(category_id)
        if not category:
            return False
        return await self.repo.delete(category_id)
