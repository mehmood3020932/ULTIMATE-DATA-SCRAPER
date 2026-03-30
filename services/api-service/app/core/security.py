# services/api-service/app/core/security.py
# Security Utilities - JWT, Password Hashing, Encryption

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import jwt
from cryptography.fernet import Fernet
from passlib.context import CryptContext

from app.config import get_settings
from app.core.exceptions import AuthenticationError

# Password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)

# Encryption for sensitive data
_fernet_instance: Optional[Fernet] = None


def get_fernet() -> Fernet:
    """Get or create Fernet encryption instance."""
    global _fernet_instance
    if _fernet_instance is None:
        settings = get_settings()
        # Ensure key is 32 bytes for Fernet
        key = settings.SECRET_KEY[:32].encode()
        # Pad or truncate to 32 bytes
        key = key.ljust(32, b'0')[:32]
        import base64
        fernet_key = base64.urlsafe_b64encode(key)
        _fernet_instance = Fernet(fernet_key)
    return _fernet_instance


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create JWT access token."""
    settings = get_settings()
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
        "jti": secrets.token_urlsafe(16),  # Unique token ID for revocation
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create JWT refresh token."""
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
        "jti": secrets.token_urlsafe(16),
    })
    
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token string
        token_type: Expected token type ('access' or 'refresh')
    
    Returns:
        Decoded token payload
    
    Raises:
        AuthenticationError: If token is invalid or expired
    """
    settings = get_settings()
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        
        # Validate token type
        if payload.get("type") != token_type:
            raise AuthenticationError(f"Invalid token type. Expected {token_type}")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")


def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data like API keys."""
    fernet = get_fernet()
    return fernet.encrypt(data.encode()).decode()


def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data."""
    fernet = get_fernet()
    return fernet.decrypt(encrypted_data.encode()).decode()


def generate_api_key() -> Tuple[str, str]:
    """
    Generate a new API key pair.
    
    Returns:
        Tuple of (public_key, secret_key)
    """
    public_key = f"ak_{secrets.token_urlsafe(16)}"
    secret_key = f"sk_{secrets.token_urlsafe(32)}"
    return public_key, secret_key


def generate_secure_random_string(length: int = 32) -> str:
    """Generate cryptographically secure random string."""
    return secrets.token_urlsafe(length)


def hash_api_key(secret_key: str) -> str:
    """Hash API key for storage (similar to password hashing)."""
    return pwd_context.hash(secret_key)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify API key against hash."""
    return pwd_context.verify(plain_key, hashed_key)


def generate_nonce() -> str:
    """Generate unique nonce for request signing."""
    return secrets.token_hex(16)


def calculate_token_expiry(created_at: datetime, expires_in_days: int) -> datetime:
    """Calculate token expiry datetime."""
    return created_at + timedelta(days=expires_in_days)