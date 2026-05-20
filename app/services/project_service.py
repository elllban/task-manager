from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectMember, ProjectRole
from app.repositories.category_repository import CategoryRepository
from app.repositories.pagination import paginate
from app.repositories.project_repository import ProjectRepository
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.repo = ProjectRepository(db)
        self.category_repo = CategoryRepository(db)
        self.db = db

    async def create_project(self, data: ProjectCreate, owner_id: int) -> Project:
        category = await self.category_repo.get(data.category_id)
        if not category:
            raise HTTPException(status_code=404, detail='Category not found')

        project = await self.repo.create(
            name=data.name, icon=data.icon, category_id=data.category_id, owner_id=owner_id
        )
        await self.repo.add_member(project.id, owner_id, ProjectRole.OWNER)
        return project

    async def get_project(self, project_id: int) -> Project | None:
        return await self.repo.get(project_id)

    async def get_user_projects(
        self, user_id: int, pagination: PaginationParams = PaginationParams()
    ) -> PaginatedResponse[Project]:
        query = select(Project).join(ProjectMember).where(ProjectMember.user_id == user_id)
        return await paginate(self.db, query, pagination)

    async def get_user_projects_by_category(
        self, user_id: int, category_id: int, pagination: PaginationParams = PaginationParams()
    ) -> PaginatedResponse[Project]:
        query = (
            select(Project)
            .join(ProjectMember)
            .where(
                ProjectMember.user_id == user_id,
                Project.category_id == category_id,
            )
        )
        return await paginate(self.db, query, pagination)

    async def update_project(self, project_id: int, data: ProjectUpdate) -> Project | None:
        update_data = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not update_data:
            return await self.repo.get(project_id)

        if 'category_id' in update_data:
            category = await self.category_repo.get(update_data['category_id'])
            if not category:
                raise HTTPException(status_code=404, detail='Category not found')

        return await self.repo.update(project_id, **update_data)

    async def delete_project(self, project_id: int, user_id: int) -> bool:
        project = await self.repo.get(project_id)
        if not project:
            return False
        if project.owner_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Only project owner can delete project')
        return await self.repo.delete(project_id)

    async def add_member(self, project_id: int, user_id: int, role: ProjectRole = ProjectRole.MEMBER) -> ProjectMember:
        return await self.repo.add_member(project_id, user_id, role)

    async def remove_member(self, project_id: int, user_id: int) -> bool:
        return await self.repo.remove_member(project_id, user_id)

    async def get_project_members(
        self, project_id: int, pagination: PaginationParams = PaginationParams()
    ) -> PaginatedResponse[ProjectMember]:
        query = select(ProjectMember).where(ProjectMember.project_id == project_id)
        return await paginate(self.db, query, pagination)
