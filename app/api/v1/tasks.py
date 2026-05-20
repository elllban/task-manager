from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_active_user,
    get_db_dep,
    require_project_member,
    require_task_access,
    require_task_admin,
)
from app.models.task import TaskPriority
from app.models.user import User
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.schemas.task import TaskCreate, TaskFilter, TaskResponse, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix='/tasks', tags=['tasks'])


@router.post('/', response_model=TaskResponse)
async def create_task(
    data: TaskCreate, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db_dep)
):
    service = TaskService(db)
    return await service.create_task(data, current_user)


@router.post('/calendar', response_model=TaskResponse)
async def create_task_from_calendar(
    data: TaskCreate,
    date: str = Query(..., description='Date in YYYY-MM-DD format'),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_dep),
):
    from datetime import datetime

    try:
        due_date = datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid date format. Use YYYY-MM-DD')

    data.due_date = due_date
    service = TaskService(db)
    return await service.create_task(data, current_user)


@router.get('/', response_model=PaginatedResponse[TaskResponse])
async def get_tasks(
    current_user: User = Depends(get_current_active_user),
    project_id: int | None = Query(None),
    completed: bool | None = Query(None),
    priority: list[TaskPriority] | None = Query(None),
    has_completed_subtasks: bool | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_dep),
):
    service = TaskService(db)
    filters = TaskFilter(
        project_id=project_id, completed=completed, priority=priority, has_completed_subtasks=has_completed_subtasks
    )
    params = PaginationParams(page=page, size=size)
    return await service.get_tasks_with_filters(current_user, filters, params)


@router.get('/assigned', response_model=PaginatedResponse[TaskResponse])
async def get_assigned_tasks(
    current_user: User = Depends(get_current_active_user),
    completed: bool | None = Query(None),
    priority: list[TaskPriority] | None = Query(None),
    has_completed_subtasks: bool | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_dep),
):
    service = TaskService(db)
    params = PaginationParams(page=page, size=size)
    return await service.get_assigned_tasks_with_filters(
        current_user.id,
        completed=completed,
        priority=priority,
        has_completed_subtasks=has_completed_subtasks,
        pagination=params,
    )


@router.get('/assigned/stats')
async def get_assigned_stats(
    current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db_dep)
):
    service = TaskService(db)
    return await service.get_assigned_stats(current_user.id)


@router.get('/calendar/dates')
async def get_calendar_dates(
    current_user: User = Depends(get_current_active_user),
    month: int = Query(..., ge=1, le=12),
    year: int = Query(...),
    completed: bool | None = Query(None),
    priority: list[TaskPriority] | None = Query(None),
    db: AsyncSession = Depends(get_db_dep),
):
    service = TaskService(db)
    return await service.get_calendar_dates(current_user, year, month, completed, priority)


@router.get('/calendar')
async def get_calendar_tasks(
    current_user: User = Depends(get_current_active_user),
    month: int = Query(..., ge=1, le=12),
    year: int = Query(...),
    completed: bool | None = Query(None),
    priority: list[TaskPriority] | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_dep),
):
    service = TaskService(db)
    params = PaginationParams(page=page, size=size)
    return await service.get_calendar_tasks(current_user, year, month, completed, priority, params)


@router.get('/{task_id}', response_model=TaskResponse)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_task_access),
    db: AsyncSession = Depends(get_db_dep),
):
    service = TaskService(db)
    task = await service.get_task_with_details(task_id, current_user)
    if not task:
        raise HTTPException(404, 'Task not found')
    return task


@router.put('/{task_id}', response_model=TaskResponse)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_task_access),
    db: AsyncSession = Depends(get_db_dep),
):
    service = TaskService(db)
    task = await service.update_task(task_id, data, current_user)
    if not task:
        raise HTTPException(404, 'Task not found')
    return task


@router.patch('/{task_id}/complete')
async def mark_task_complete(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_task_access),
    db: AsyncSession = Depends(get_db_dep),
):
    service = TaskService(db)
    task = await service.mark_completed(task_id, True)
    if not task:
        raise HTTPException(404, 'Task not found')
    return {'message': 'Task marked as completed'}


@router.patch('/{task_id}/uncomplete')
async def mark_task_uncomplete(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_task_access),
    db: AsyncSession = Depends(get_db_dep),
):
    service = TaskService(db)
    task = await service.mark_completed(task_id, False)
    if not task:
        raise HTTPException(404, 'Task not found')
    return {'message': 'Task marked as uncompleted'}


@router.delete('/{task_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_task_admin),
    db: AsyncSession = Depends(get_db_dep),
):
    service = TaskService(db)
    deleted = await service.delete_task(task_id, current_user)
    if not deleted:
        raise HTTPException(404, 'Task not found')
    return {'message': 'Task deleted'}


@router.get('/project/{project_id}', response_model=PaginatedResponse[TaskResponse])
async def get_tasks_by_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_project_member),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_dep),
):
    service = TaskService(db)
    params = PaginationParams(page=page, size=size)
    return await service.get_tasks_by_project(project_id, current_user, params)
