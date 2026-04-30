from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.deps import get_db_dep, get_current_active_user
from app.services.category_service import CategoryService
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.models.user import User

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("/", response_model=CategoryResponse)
async def create_category(
    data: CategoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_dep)
):
    service = CategoryService(db)
    return await service.create_category(data)


@router.get("/", response_model=List[CategoryResponse])
async def get_categories(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_dep)
):
    service = CategoryService(db)
    return await service.get_all_categories()


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_dep)
):
    service = CategoryService(db)
    category = await service.get_category(category_id)
    if not category:
        raise HTTPException(404, "Category not found")
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_dep)
):
    service = CategoryService(db)
    category = await service.update_category(category_id, data)
    if not category:
        raise HTTPException(404, "Category not found")
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_dep)
):
    service = CategoryService(db)
    deleted = await service.delete_category(category_id)
    if not deleted:
        raise HTTPException(404, "Category not found")
    return {"message": "Category deleted"}