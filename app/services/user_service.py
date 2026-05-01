from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from fastapi import HTTPException, status
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserUpdate
from app.models.user import User


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserRepository(db)

    async def get_user(self, user_id: int) -> Optional[User]:
        return await self.repo.get(user_id)

    async def get_all_users(self) -> List[User]:
        return await self.repo.get_all()

    async def update_user(self, user_id: int, data: UserUpdate) -> Optional[User]:
        user = await self.repo.get(user_id)
        if not user:
            return None

        update_data = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not update_data:
            return user

        if 'email' in update_data:
            existing = await self.repo.get_by_email(update_data['email'])
            if existing and existing.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

        return await self.repo.update(user_id, **update_data)

    async def update_avatar(self, user_id: int, avatar_url: str) -> Optional[User]:
        return await self.repo.update(user_id, avatar=avatar_url)

    async def delete_user(self, user_id: int) -> bool:
        user = await self.repo.get(user_id)
        if not user:
            return False
        return await self.repo.delete(user_id)