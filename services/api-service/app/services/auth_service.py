# services/api-service/app/services/auth_service.py
# Authentication Service

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

import ulid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    ResourceNotFoundError,
    ValidationError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    hash_api_key,
    verify_api_key,
    verify_password,
)
from app.models.database import ApiKey, User
from app.models.schemas import ApiKeyWithSecret, UserResponse


class AuthService:
    """Authentication and authorization service."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        company_name: Optional[str] = None,
    ) -> User:
        """Create a new user."""
        user_id = str(ulid.new())
        
        user = User(
            id=user_id,
            email=email.lower().strip(),
            password_hash=get_password_hash(password),
            full_name=full_name,
            company_name=company_name,
            credits_balance=100,  # Free credits for new users
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none()
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = await self.get_user_by_email(email)
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        return user
    
    async def create_tokens(self, user_id: str) -> dict:
        """Create access and refresh tokens."""
        access_token = create_access_token({"sub": user_id})
        refresh_token = create_refresh_token({"sub": user_id})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": 1800,  # 30 minutes
        }
    
    async def refresh_access_token(self, refresh_token: str) -> dict:
        """Refresh access token."""
        payload = decode_token(refresh_token, "refresh")
        user_id = payload.get("sub")
        
        user = await self.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise AuthenticationError("Invalid refresh token")
        
        return await self.create_tokens(user_id)
    
    async def revoke_token(self, token: str) -> None:
        """Revoke a token (add to blacklist)."""
        # Implementation would add token to Redis blacklist
        # with TTL based on expiration
        pass
    
    async def create_api_key(
        self,
        user_id: str,
        name: str,
        permissions: list[str],
        expires_days: Optional[int] = None,
    ) -> ApiKeyWithSecret:
        """Create a new API key."""
        from app.core.security import generate_api_key
        
        public_key, secret_key = generate_api_key()
        key_id = str(ulid.new())
        
        expires_at = None
        if expires_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)
        
        api_key = ApiKey(
            id=key_id,
            user_id=user_id,
            public_key=public_key,
            key_hash=hash_api_key(secret_key),
            name=name,
            permissions=permissions,
            expires_at=expires_at,
        )
        
        self.db.add(api_key)
        await self.db.commit()
        await self.db.refresh(api_key)
        
        return ApiKeyWithSecret(
            id=api_key.id,
            public_key=api_key.public_key,
            secret_key=secret_key,  # Only returned once
            name=api_key.name,
            permissions=api_key.permissions,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            last_used_at=api_key.last_used_at,
            expires_at=api_key.expires_at,
        )
    
    async def authenticate_api_key(
        self,
        public_key: str,
        secret_key: str,
    ) -> Optional[User]:
        """Authenticate using API key."""
        result = await self.db.execute(
            select(ApiKey).where(
                ApiKey.public_key == public_key,
                ApiKey.is_active == True,
            )
        )
        api_key = result.scalar_one_or_none()
        
        if not api_key:
            return None
        
        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
            return None
        
        # Verify secret
        if not verify_api_key(secret_key, api_key.key_hash):
            return None
        
        # Get user
        result = await self.db.execute(
            select(User).where(User.id == api_key.user_id)
        )
        return result.scalar_one_or_none()
    
    async def update_api_key_last_used(self, public_key: str) -> None:
        """Update last used timestamp."""
        result = await self.db.execute(
            select(ApiKey).where(ApiKey.public_key == public_key)
        )
        api_key = result.scalar_one_or_none()
        
        if api_key:
            api_key.last_used_at = datetime.now(timezone.utc)
            await self.db.commit()
    
    async def get_user_api_keys(self, user_id: str) -> list[ApiKey]:
        """Get all API keys for user."""
        result = await self.db.execute(
            select(ApiKey).where(ApiKey.user_id == user_id)
        )
        return result.scalars().all()
    
    async def revoke_api_key(self, key_id: str, user_id: str) -> None:
        """Revoke an API key."""
        result = await self.db.execute(
            select(ApiKey).where(
                ApiKey.id == key_id,
                ApiKey.user_id == user_id,
            )
        )
        api_key = result.scalar_one_or_none()
        
        if not api_key:
            raise ResourceNotFoundError("API key not found")
        
        api_key.is_active = False
        await self.db.commit()
    
    async def verify_email(self, token: str) -> None:
        """Verify email address."""
        # Implementation would verify email token
        pass
    
    async def initiate_password_reset(self, email: str) -> None:
        """Send password reset email."""
        # Implementation would send reset email
        pass
    
    async def reset_password(self, token: str, new_password: str) -> None:
        """Reset password."""
        # Implementation would validate token and update password
        pass