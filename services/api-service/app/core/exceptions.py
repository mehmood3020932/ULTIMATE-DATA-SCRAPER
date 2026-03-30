# services/api-service/app/core/exceptions.py
# Custom Exception Classes

from typing import Any, Dict, List, Optional


class BaseAppException(Exception):
    """Base application exception."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(BaseAppException):
    """Authentication failed."""
    pass


class AuthorizationError(BaseAppException):
    """Authorization failed - insufficient permissions."""
    pass


class ValidationError(BaseAppException):
    """Input validation failed."""
    
    def __init__(
        self,
        message: str,
        errors: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(message)
        self.errors = errors or []


class RateLimitError(BaseAppException):
    """Rate limit exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = 60,
    ):
        super().__init__(message)
        self.retry_after = retry_after


class ScrapingError(BaseAppException):
    """Scraping operation failed."""
    
    def __init__(
        self,
        message: str,
        job_id: Optional[str] = None,
        url: Optional[str] = None,
    ):
        super().__init__(message)
        self.job_id = job_id
        self.url = url


class BusinessLogicError(BaseAppException):
    """Business logic violation."""
    pass


class ResourceNotFoundError(BaseAppException):
    """Requested resource not found."""
    pass


class ConflictError(BaseAppException):
    """Resource conflict."""
    pass


class ExternalServiceError(BaseAppException):
    """External service call failed."""
    pass


class DatabaseError(BaseAppException):
    """Database operation failed."""
    pass


class CacheError(BaseAppException):
    """Cache operation failed."""
    pass


class LLMError(BaseAppException):
    """LLM provider error."""
    pass


class AgentError(BaseAppException):
    """AI agent execution error."""
    pass