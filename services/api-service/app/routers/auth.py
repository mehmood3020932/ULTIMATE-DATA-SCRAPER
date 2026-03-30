# services/api-service/app/routers/auth.py
# Authentication Endpoints

from typing import Optional

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ValidationError
from app.dependencies import get_current_user, get_db_session
from app.models.database import User
from app.models.schemas import (
    ApiKeyCreate,
    ApiKeyResponse,
    ApiKeyWithSecret,
    TokenRefresh,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Register a new user account.
    """
    auth_service = AuthService(db)
    
    # Check if email exists
    existing = await auth_service.get_user_by_email(user_data.email)
    if existing:
        raise ValidationError("Email already registered")
    
    # Create user
    user = await auth_service.create_user(
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        company_name=user_data.company_name,
    )
    
    # TODO: Send verification email
    
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Authenticate user and return tokens.
    """
    auth_service = AuthService(db)
    
    user = await auth_service.authenticate_user(
        email=credentials.email,
        password=credentials.password,
    )
    
    if not user:
        raise AuthenticationError("Invalid email or password")
    
    if not user.is_active:
        raise AuthenticationError("Account is deactivated")
    
    tokens = await auth_service.create_tokens(user.id)
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="bearer",
        expires_in=tokens["expires_in"],
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: TokenRefresh,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Refresh access token using refresh token.
    """
    auth_service = AuthService(db)
    
    tokens = await auth_service.refresh_access_token(refresh_data.refresh_token)
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="bearer",
        expires_in=tokens["expires_in"],
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Logout user (revoke tokens).
    """
    auth_service = AuthService(db)
    
    # Revoke token
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if token:
        await auth_service.revoke_token(token)
    
    return None


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get current user profile.
    """
    return current_user


@router.post("/api-keys", response_model=ApiKeyWithSecret, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: ApiKeyCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Create a new API key.
    """
    auth_service = AuthService(db)
    
    api_key = await auth_service.create_api_key(
        user_id=current_user.id,
        name=key_data.name,
        permissions=key_data.permissions,
    )
    
    return api_key


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    List user's API keys (without secrets).
    """
    auth_service = AuthService(db)
    keys = await auth_service.get_user_api_keys(current_user.id)
    return keys


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Revoke an API key.
    """
    auth_service = AuthService(db)
    await auth_service.revoke_api_key(key_id, current_user.id)
    return None


@router.post("/verify-email/{token}")
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Verify email address.
    """
    auth_service = AuthService(db)
    await auth_service.verify_email(token)
    return {"message": "Email verified successfully"}


@router.post("/forgot-password")
async def forgot_password(
    email: str,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Request password reset.
    """
    auth_service = AuthService(db)
    await auth_service.initiate_password_reset(email)
    return {"message": "If email exists, reset instructions sent"}


@router.post("/reset-password/{token}")
async def reset_password(
    token: str,
    new_password: str,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Reset password using token.
    """
    auth_service = AuthService(db)
    await auth_service.reset_password(token, new_password)
    return {"message": "Password reset successful"}