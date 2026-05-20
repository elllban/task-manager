import re

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db_dep, oauth2_scheme
from app.core.security import SecurityService
from app.models.user import User
from app.services.auth_service import AuthService

router = APIRouter(prefix='/auth', tags=['authentication'])

PASSWORD_PATTERN = re.compile(r'^[A-Za-z0-9!#$%&*+\-.<=>?@^_]+$')


def validate_password(password: str) -> str:
    if not PASSWORD_PATTERN.match(password):
        raise ValueError('Password must contain only A-Z a-z 0-9 ! # $ % & * + - . < = > ? @ ^ _')
    return password


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=16)
    password_confirm: str = Field(..., min_length=8, max_length=16)
    name: str | None = Field(None, min_length=1, max_length=50)

    @field_validator('password')
    def password_valid_chars(cls, v):
        return validate_password(v)

    @field_validator('password_confirm')
    def passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str = Field(..., min_length=8, max_length=16)
    new_password_confirm: str = Field(..., min_length=8, max_length=16)

    @field_validator('new_password')
    def new_password_valid_chars(cls, v):
        return validate_password(v)

    @field_validator('new_password_confirm')
    def passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=16)
    new_password_confirm: str = Field(..., min_length=8, max_length=16)

    @field_validator('new_password')
    def new_password_valid_chars(cls, v):
        return validate_password(v)

    @field_validator('new_password_confirm')
    def passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v


@router.post('/register', response_model=TokenResponse)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db_dep)):
    service = AuthService(db)
    try:
        return await service.register(data.email, data.password, data.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post('/login', response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db_dep)):
    service = AuthService(db)
    tokens = await service.login(form_data.username, form_data.password)
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect email or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    return tokens


@router.post('/refresh', response_model=TokenResponse)
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db_dep)):
    service = AuthService(db)
    tokens = await service.refresh_access_token(refresh_token)
    if not tokens:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid refresh token')
    return tokens


@router.post('/forgot-password')
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db_dep)):
    service = AuthService(db)
    try:
        await service.send_reset_code(data.email)
        return {'message': 'Reset code sent to your email'}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post('/reset-password')
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db_dep)):
    service = AuthService(db)
    try:
        await service.reset_password(data.email, data.code, data.new_password)
        return {'message': 'Password successfully reset'}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post('/change-password')
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_dep),
):
    service = AuthService(db)
    try:
        await service.change_password(current_user.id, data.old_password, data.new_password)
        return {'message': 'Password successfully changed'}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post('/logout')
async def logout(
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_dep),
):
    payload = SecurityService.decode_token(token)
    if payload:
        jti = payload.get('jti')
        remaining_ttl = SecurityService.get_token_remaining_ttl(payload)
        service = AuthService(db)
        await service.logout(current_user.id, jti, remaining_ttl)
    return {'message': 'Successfully logged out'}


@router.get('/me')
async def get_me(current_user: User = Depends(get_current_active_user)):
    return {
        'id': current_user.id,
        'email': current_user.email,
        'name': current_user.name,
        'avatar': current_user.avatar,
    }
