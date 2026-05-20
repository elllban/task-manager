from unittest.mock import AsyncMock, patch

import pytest

import app.models.attachment  # noqa: F401
import app.models.category  # noqa: F401
import app.models.project  # noqa: F401
import app.models.task  # noqa: F401
import app.models.user  # noqa: F401
from app.schemas.pagination import PaginationParams
from app.schemas.task import TaskCreate, TaskFilter
from app.services.task_service import TaskService


@pytest.fixture
def task_service():
    service = TaskService.__new__(TaskService)
    service.db = AsyncMock()
    service.task_repo = AsyncMock()
    service.project_repo = AsyncMock()
    return service


class TestTaskService:
    @pytest.mark.asyncio
    async def test_create_task_success(self, task_service):
        task_service.project_repo.get_member.return_value = AsyncMock()
        task_service.task_repo.create.return_value = AsyncMock(id=1, project_id=1)

        mock_loaded_task = AsyncMock(
            id=1,
            title='Test Task',
            description=None,
            project_id=1,
            author_id=1,
            assignee_id=None,
            parent_id=None,
            due_date=None,
            priority='not_urgent',
            completed=False,
            author=None,
            assignee=None,
            project=None,
        )

        mock_result = AsyncMock()
        mock_result.scalar_one.return_value = mock_loaded_task
        task_service.db.execute.return_value = mock_result

        data = TaskCreate(title='Test Task', project_id=1)
        with patch('app.services.task_service.TaskResponse.from_task') as mock_from:
            mock_from.return_value = {'id': 1, 'title': 'Test Task'}
            result = await task_service.create_task(data, AsyncMock(id=1))

            assert result['id'] == 1
            task_service.task_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_task_no_project_access(self, task_service):
        task_service.project_repo.get_member.return_value = None
        data = TaskCreate(title='Test', project_id=1)

        with pytest.raises(Exception, match='access to this project'):
            await task_service.create_task(data, AsyncMock(id=1))

    @pytest.mark.asyncio
    async def test_get_tasks_with_filters_empty(self, task_service):
        task_service.project_repo.get_user_projects.return_value = []
        params = PaginationParams(page=1, size=20)

        result = await task_service.get_tasks_with_filters(AsyncMock(id=1), TaskFilter(), params)

        assert result.total == 0
        assert result.items == []
