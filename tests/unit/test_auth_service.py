from unittest.mock import AsyncMock, patch

import pytest

from app.services.auth_service import AuthService


@pytest.fixture
def auth_service():
    service = AuthService.__new__(AuthService)
    service.db = AsyncMock()
    service.user_repo = AsyncMock()
    return service


class TestAuthService:
    @pytest.mark.asyncio
    async def test_register_success(self, auth_service):
        auth_service.user_repo.get_by_email.return_value = None
        auth_service.user_repo.create.return_value = AsyncMock(id=1, email='test@test.com')

        with (
            patch('app.services.auth_service.SecurityService.get_password_hash') as mock_hash,
            patch('app.services.auth_service.SecurityService.create_access_token') as mock_at,
            patch('app.services.auth_service.SecurityService.create_refresh_token') as mock_rt,
        ):
            mock_hash.return_value = 'hashed'
            mock_at.return_value = 'access_token'
            mock_rt.return_value = 'refresh_token'

            result = await auth_service.register('test@test.com', 'Password1!')

            assert result['access_token'] == 'access_token'
            assert result['refresh_token'] == 'refresh_token'
            auth_service.user_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, auth_service):
        auth_service.user_repo.get_by_email.return_value = AsyncMock(id=1)

        with pytest.raises(ValueError, match='Email already registered'):
            await auth_service.register('existing@test.com', 'Password1!')

    @pytest.mark.asyncio
    async def test_login_success(self, auth_service):
        mock_user = AsyncMock(id=1, password_hash='hashed')
        auth_service.user_repo.get_by_email.return_value = mock_user

        with (
            patch('app.services.auth_service.SecurityService.verify_password') as mock_verify,
            patch('app.services.auth_service.SecurityService.create_access_token') as mock_at,
            patch('app.services.auth_service.SecurityService.create_refresh_token') as mock_rt,
        ):
            mock_verify.return_value = True
            mock_at.return_value = 'access_token'
            mock_rt.return_value = 'refresh_token'

            result = await auth_service.login('test@test.com', 'Password1!')

            assert result['access_token'] == 'access_token'

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, auth_service):
        mock_user = AsyncMock(password_hash='hashed')
        auth_service.user_repo.get_by_email.return_value = mock_user

        with patch('app.services.auth_service.SecurityService.verify_password') as mock_verify:
            mock_verify.return_value = False

            result = await auth_service.login('test@test.com', 'wrong')
            assert result is None

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, auth_service):
        auth_service.user_repo.get_by_email.return_value = None
        result = await auth_service.login('nonexistent@test.com', 'Password1!')
        assert result is None

    @pytest.mark.asyncio
    async def test_logout(self, auth_service):
        with patch('app.services.auth_service.cache') as mock_cache:
            await auth_service.logout(1, 'test-jti', 1800)
            mock_cache.set.assert_called_once_with('jwt_blacklist:test-jti', True, 1800)
