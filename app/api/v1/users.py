from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import os
import uuid

from app.api.deps import get_db_dep, get_current_active_user
from app.services.user_service import UserService
from app.schemas.user import UserResponse, UserUpdate
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])

UPLOAD_DIR = "uploads/avatars"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/", response_model=List[UserResponse])
async def get_users(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_dep)
):
    service = UserService(db)
    return await service.get_all_users()


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
        current_user: User = Depends(get_current_active_user)
):
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
        user_id: int,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_dep)
):
    service = UserService(db)
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
        data: UserUpdate,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_dep)
):
    service = UserService(db)
    try:
        user = await service.update_user(current_user.id, data)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/me/avatar")
async def upload_avatar(
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_dep)
):
    if not file.content_type.startswith('image/'):
        raise HTTPException(400, "File must be an image")

    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    service = UserService(db)
    avatar_url = f"/uploads/avatars/{filename}"
    user = await service.update_avatar(current_user.id, avatar_url)

    return {"avatar_url": avatar_url}


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_dep)
):
    service = UserService(db)
    deleted = await service.delete_user(current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Account deleted"}