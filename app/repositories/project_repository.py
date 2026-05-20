from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectMember, ProjectRole
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db: AsyncSession):
        super().__init__(Project, db)

    async def get_by_category(self, category_id: int) -> list[Project]:
        result = await self.db.execute(select(Project).where(Project.category_id == category_id))
        return result.scalars().all()

    async def add_member(self, project_id: int, user_id: int, role: ProjectRole = ProjectRole.MEMBER) -> ProjectMember:
        stmt = select(ProjectMember).where(
            and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            return existing

        member = ProjectMember(project_id=project_id, user_id=user_id, role=role)
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def get_member(self, project_id: int, user_id: int) -> ProjectMember | None:
        result = await self.db.execute(
            select(ProjectMember).where(and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id))
        )
        return result.scalar_one_or_none()

    async def get_user_projects(self, user_id: int) -> list[Project]:
        result = await self.db.execute(select(Project).join(ProjectMember).where(ProjectMember.user_id == user_id))
        return result.scalars().all()

    async def remove_member(self, project_id: int, user_id: int) -> bool:
        result = await self.db.execute(
            select(ProjectMember).where(and_(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id))
        )
        member = result.scalar_one_or_none()
        if not member:
            return False
        await self.db.delete(member)
        await self.db.commit()
        return True

    async def get_project_members(self, project_id: int) -> list[ProjectMember]:
        result = await self.db.execute(select(ProjectMember).where(ProjectMember.project_id == project_id))
        return result.scalars().all()
