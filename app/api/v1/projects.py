from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db_dep, require_project_admin, require_project_member
from app.models.user import User
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.schemas.project import ProjectCreate, ProjectMemberAdd, ProjectMemberResponse, ProjectResponse, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(prefix='/projects', tags=['projects'])


@router.post('/', response_model=ProjectResponse)
async def create_project(
    data: ProjectCreate, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db_dep)
):
    service = ProjectService(db)
    return await service.create_project(data, current_user.id)


@router.get('/', response_model=PaginatedResponse[ProjectResponse])
async def get_projects(
    current_user: User = Depends(get_current_active_user),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_dep),
):
    service = ProjectService(db)
    params = PaginationParams(page=page, size=size)
    return await service.get_user_projects(current_user.id, params)


@router.get('/{project_id}', response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_project_member),
    db: AsyncSession = Depends(get_db_dep),
):
    service = ProjectService(db)
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(404, 'Project not found')
    return project


@router.put('/{project_id}', response_model=ProjectResponse)
async def update_project(
    project_id: int,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_project_admin),
    db: AsyncSession = Depends(get_db_dep),
):
    service = ProjectService(db)
    project = await service.update_project(project_id, data)
    if not project:
        raise HTTPException(404, 'Project not found')
    return project


@router.delete('/{project_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_project_admin),
    db: AsyncSession = Depends(get_db_dep),
):
    service = ProjectService(db)
    deleted = await service.delete_project(project_id, current_user.id)
    if not deleted:
        raise HTTPException(404, 'Project not found')
    return {'message': 'Project deleted'}


@router.post('/{project_id}/members')
async def add_project_member(
    project_id: int,
    data: ProjectMemberAdd,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_project_admin),
    db: AsyncSession = Depends(get_db_dep),
):
    service = ProjectService(db)
    try:
        member = await service.add_member(project_id, data.user_id, data.role)
        return {'message': 'Member added', 'member': member}
    except ValueError as e:
        raise HTTPException(400, detail=str(e))


@router.get('/{project_id}/members', response_model=PaginatedResponse[ProjectMemberResponse])
async def get_project_members(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_project_member),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_dep),
):
    service = ProjectService(db)
    params = PaginationParams(page=page, size=size)
    result = await service.get_project_members(project_id, params)
    result.items = [ProjectMemberResponse.model_validate(m) for m in result.items]
    return result


@router.delete('/{project_id}/members/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def remove_project_member(
    project_id: int,
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_project_admin),
    db: AsyncSession = Depends(get_db_dep),
):
    service = ProjectService(db)
    try:
        removed = await service.remove_member(project_id, user_id)
        if not removed:
            raise HTTPException(404, 'Member not found')
        return {'message': 'Member removed'}
    except ValueError as e:
        raise HTTPException(400, detail=str(e))


@router.get('/category/{category_id}', response_model=PaginatedResponse[ProjectResponse])
async def get_projects_by_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_dep),
):
    service = ProjectService(db)
    params = PaginationParams(page=page, size=size)
    return await service.get_user_projects_by_category(current_user.id, category_id, params)
