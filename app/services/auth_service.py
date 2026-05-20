import asyncio
import random
import smtplib
import string
from datetime import datetime, timedelta
from email.message import EmailMessage

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache
from app.core.config import settings
from app.core.security import SecurityService
from app.repositories.user_repository import UserRepository

reset_codes: dict[str, dict[str, any]] = {}


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def register(self, email: str, password: str, name: str | None = None) -> dict:
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise ValueError('Email already registered')

        password_hash = SecurityService.get_password_hash(password)

        user = await self.user_repo.create(email=email, password_hash=password_hash, name=name)

        access_token = SecurityService.create_access_token({'sub': str(user.id)})
        refresh_token = SecurityService.create_refresh_token({'sub': str(user.id)})

        return {'access_token': access_token, 'refresh_token': refresh_token}

    async def login(self, email: str, password: str) -> dict | None:
        user = await self.user_repo.get_by_email(email)
        if not user:
            return None

        if not SecurityService.verify_password(password, user.password_hash):
            return None

        access_token = SecurityService.create_access_token({'sub': str(user.id)})
        refresh_token = SecurityService.create_refresh_token({'sub': str(user.id)})

        return {'access_token': access_token, 'refresh_token': refresh_token}

    async def refresh_access_token(self, refresh_token: str) -> dict | None:
        payload = SecurityService.decode_token(refresh_token)
        if not payload or payload.get('type') != 'refresh':
            return None

        user_id = payload.get('sub')
        if not user_id:
            return None

        user = await self.user_repo.get(int(user_id))
        if not user or not user.is_active:
            return None

        new_access_token = SecurityService.create_access_token({'sub': str(user.id)})
        new_refresh_token = SecurityService.create_refresh_token({'sub': str(user.id)})

        return {'access_token': new_access_token, 'refresh_token': new_refresh_token}

    async def send_reset_code(self, email: str) -> None:
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise ValueError('Email not registered')

        code = ''.join(random.choices(string.digits, k=6))
        reset_codes[email] = {'code': code, 'expires_at': datetime.utcnow() + timedelta(minutes=15)}

        await self._send_reset_email(email, code)

    async def _send_reset_email(self, email: str, code: str) -> None:
        message = EmailMessage()
        message['From'] = settings.SMTP_FROM
        message['To'] = email
        message['Subject'] = 'Password Reset Code'

        body = f'Your password reset code is: {code}\nThis code expires in 15 minutes.'
        message.set_content(body)

        def send_email_sync():
            try:
                with smtplib.SMTP(settings.SMTP_HOST, 2525) as smtp:
                    smtp.starttls()
                    smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    smtp.send_message(message)
            except Exception:
                try:
                    with smtplib.SMTP(settings.SMTP_HOST, 587) as smtp:
                        smtp.starttls()
                        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                        smtp.send_message(message)
                except Exception as e2:
                    raise ValueError(f'Failed to send email: {str(e2)}')

        try:
            await asyncio.to_thread(send_email_sync)
        except Exception as e:
            raise ValueError(f'Failed to send email: {str(e)}')

    async def reset_password(self, email: str, code: str, new_password: str) -> None:
        if email not in reset_codes:
            raise ValueError('Invalid or expired reset code')

        stored = reset_codes[email]
        if stored['code'] != code:
            raise ValueError('Invalid reset code')

        if datetime.utcnow() > stored['expires_at']:
            del reset_codes[email]
            raise ValueError('Reset code expired')

        user = await self.user_repo.get_by_email(email)
        if not user:
            raise ValueError('User not found')

        password_hash = SecurityService.get_password_hash(new_password)
        await self.user_repo.update(user.id, password_hash=password_hash)

        del reset_codes[email]

    async def logout(self, user_id: int, jti: str, remaining_ttl: int) -> None:
        cache.set(f'jwt_blacklist:{jti}', True, remaining_ttl)
        cache.clear_user_session(user_id)

    async def change_password(self, user_id: int, old_password: str, new_password: str) -> None:
        user = await self.user_repo.get(user_id)
        if not user:
            raise ValueError('User not found')

        if not SecurityService.verify_password(old_password, user.password_hash):
            raise ValueError('Invalid old password')

        password_hash = SecurityService.get_password_hash(new_password)
        await self.user_repo.update(user.id, password_hash=password_hash)
