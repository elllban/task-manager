from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.pagination import PaginatedResponse, PaginationParams


async def paginate_query(
    db: AsyncSession,
    query: Any,
    page: int = 1,
    size: int = 20,
) -> tuple[list[Any], int]:
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * size
    result = await db.execute(query.offset(offset).limit(size))
    items = list(result.scalars().all())

    return items, total


async def paginate(
    db: AsyncSession,
    query: Any,
    params: PaginationParams,
) -> PaginatedResponse:
    items, total = await paginate_query(db, query, params.page, params.size)
    return PaginatedResponse.create(items, total, params.page, params.size)
