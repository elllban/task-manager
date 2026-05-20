from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache
from app.core.database import get_db
from app.core.security import SecurityService
from app.models.project import ProjectRole
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v1/auth/login')


async def get_db_dep() -> AsyncSession:
    async for session in get_db():
        yield session


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db_dep)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    payload = SecurityService.decode_token(token)
    if not payload:
        raise credentials_exception

    if payload.get('type') != 'access':
        raise credentials_exception

    jti = payload.get('jti')
    if jti and cache.exists(f'jwt_blacklist:{jti}'):
        raise credentials_exception

    user_id = payload.get('sub')
    if not user_id:
        raise credentials_exception

    user_repo = UserRepository(db)
    user = await user_repo.get(int(user_id))
    if not user:
        raise credentials_exception

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Inactive user')
    return current_user


class AccessChecker:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.task_repo = TaskRepository(db)

    async def check_project_access(
        self, project_id: int, user: User, required_roles: list[ProjectRole] | None = None
    ) -> bool:
        member = await self.project_repo.get_member(project_id, user.id)
        if not member:
            return False

        if required_roles and member.role not in required_roles:
            return False

        return True

    async def check_task_access(
        self, task_id: int, user: User, required_roles: list[ProjectRole] | None = None
    ) -> bool:
        task = await self.task_repo.get(task_id)
        if not task:
            return False

        return await self.check_project_access(task.project_id, user, required_roles)


async def get_access_checker(db: AsyncSession = Depends(get_db_dep)) -> AccessChecker:
    return AccessChecker(db)


async def require_project_member(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    access_checker: AccessChecker = Depends(get_access_checker),
):
    has_access = await access_checker.check_project_access(project_id, current_user)
    if not has_access:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this project")
    return True


async def require_project_admin(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    access_checker: AccessChecker = Depends(get_access_checker),
):
    has_access = await access_checker.check_project_access(
        project_id, current_user, required_roles=[ProjectRole.OWNER, ProjectRole.ADMIN]
    )
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail='Only project owner or admin can perform this action'
        )
    return True


async def require_task_access(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    access_checker: AccessChecker = Depends(get_access_checker),
):

    has_access = await access_checker.check_task_access(task_id, current_user)
    if not has_access:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this task")
    return True


async def require_task_admin(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    access_checker: AccessChecker = Depends(get_access_checker),
):

    has_access = await access_checker.check_task_access(
        task_id, current_user, required_roles=[ProjectRole.OWNER, ProjectRole.ADMIN]
    )
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail='Only project owner or admin can perform this action'
        )
    return True
