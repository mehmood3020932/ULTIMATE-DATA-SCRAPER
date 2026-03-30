# services/api-service/app/dependencies.py
# FastAPI Dependencies for DI

from typing import AsyncGenerator, Optional

import aiokafka
import redis.asyncio as redis
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import decode_token, verify_api_key
from app.models.database import get_db_session
from app.models.schemas import UserResponse
from app.services.auth_service import AuthService
from app.services.job_orchestrator import JobOrchestrator

security = HTTPBearer(auto_error=False)


async def get_redis_pool() -> redis.Redis:
    """Get Redis connection pool."""
    settings = get_settings()
    return redis.from_url(
        str(settings.REDIS_URL),
        encoding="utf-8",
        decode_responses=True,
        max_connections=settings.REDIS_POOL_SIZE,
    )


async def get_kafka_producer() -> aiokafka.AIOKafkaProducer:
    """Get Kafka producer instance."""
    settings = get_settings()
    producer = aiokafka.AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        client_id=settings.KAFKA_CLIENT_ID,
        security_protocol=settings.KAFKA_SECURITY_PROTOCOL,
        sasl_mechanism=settings.KAFKA_SASL_MECHANISM,
        sasl_plain_username=settings.KAFKA_SASL_USERNAME,
        sasl_plain_password=settings.KAFKA_SASL_PASSWORD,
        value_serializer=lambda v: v.encode('utf-8') if isinstance(v, str) else str(v).encode('utf-8'),
    )
    await producer.start()
    return producer


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    """
    Get current authenticated user from JWT or API key.
    
    Priority:
    1. JWT Bearer token
    2. X-API-Key header
    """
    auth_service = AuthService(db)
    
    # Try JWT first
    if credentials and credentials.scheme == "Bearer":
        try:
            token = credentials.credentials
            payload = decode_token(token, "access")
            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationError("Invalid token: no user ID")
            
            user = await auth_service.get_user_by_id(user_id)
            if not user or not user.is_active:
                raise AuthenticationError("User not found or inactive")
            
            request.state.auth_method = "jwt"
            request.state.user_id = user_id
            return UserResponse.model_validate(user)
            
        except AuthenticationError:
            if not x_api_key:
                raise
    
    # Try API key
    if x_api_key:
        try:
            # Extract public key from format: ak_xxxx:sk_xxxx or just ak_xxxx
            if ":" in x_api_key:
                public_key, secret_key = x_api_key.split(":", 1)
            else:
                raise AuthenticationError("Invalid API key format. Expected 'public_key:secret_key'")
            
            user = await auth_service.authenticate_api_key(public_key, secret_key)
            if not user or not user.is_active:
                raise AuthenticationError("Invalid API key or user inactive")
            
            request.state.auth_method = "api_key"
            request.state.user_id = user.id
            request.state.api_key = public_key
            
            # Update last used timestamp (async fire-and-forget)
            await auth_service.update_api_key_last_used(public_key)
            
            return UserResponse.model_validate(user)
            
        except AuthenticationError:
            raise
    
    raise AuthenticationError("Authentication required. Provide Bearer token or API key")


async def get_current_active_user(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """Ensure user is active and verified."""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required",
        )
    return current_user


async def get_premium_user(
    current_user: UserResponse = Depends(get_current_active_user),
) -> UserResponse:
    """Ensure user has premium subscription."""
    if current_user.subscription_tier not in ["professional", "enterprise"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required",
        )
    return current_user


async def get_job_orchestrator(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> JobOrchestrator:
    """Get job orchestrator with required dependencies."""
    redis_pool = request.app.state.redis_pool
    kafka_producer = request.app.state.kafka_producer
    return JobOrchestrator(db, redis_pool, kafka_producer)


def require_permissions(*required_permissions: str):
    """Dependency factory for permission checking."""
    async def check_permissions(
        request: Request,
        current_user: UserResponse = Depends(get_current_user),
    ) -> UserResponse:
        # Get API key permissions if using API key auth
        if getattr(request.state, "auth_method", None) == "api_key":
            # TODO: Check API key specific permissions
            pass
        
        # Check user-level permissions (simplified)
        if current_user.is_superuser:
            return current_user
        
        # TODO: Implement proper permission checking
        return current_user
    
    return check_permissions


async def get_pagination(
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Get pagination parameters."""
    return {
        "page": max(1, page),
        "page_size": max(1, min(100, page_size)),
        "offset": (max(1, page) - 1) * max(1, min(100, page_size)),
    }