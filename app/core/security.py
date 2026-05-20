import uuid
from datetime import datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


class SecurityService:
    ALGORITHM = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False

    @staticmethod
    def get_password_hash(password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=SecurityService.ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({'exp': expire, 'type': 'access', 'jti': str(uuid.uuid4())})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=SecurityService.ALGORITHM)

    @staticmethod
    def create_refresh_token(data: dict[str, Any]) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=SecurityService.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({'exp': expire, 'type': 'refresh', 'jti': str(uuid.uuid4())})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=SecurityService.ALGORITHM)

    @staticmethod
    def get_token_remaining_ttl(payload: dict[str, Any]) -> int:
        exp = payload.get('exp')
        if not exp:
            return 0
        remaining = exp - datetime.utcnow().timestamp()
        return max(0, int(remaining))

    @staticmethod
    def decode_token(token: str) -> dict[str, Any] | None:
        try:
            return jwt.decode(token, settings.SECRET_KEY, algorithms=[SecurityService.ALGORITHM])
        except JWTError:
            return None
