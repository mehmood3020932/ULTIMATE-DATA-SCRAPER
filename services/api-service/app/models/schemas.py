# services/api-service/app/models/schemas.py
# Pydantic Schemas for Request/Response Validation

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, HttpUrl


# Enums
class JobStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class SubscriptionTier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


# Base schemas
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        populate_by_name = True


# User schemas
class UserCreate(BaseSchema):
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    company_name: Optional[str] = None


class UserResponse(BaseSchema):
    id: str
    email: str
    full_name: Optional[str]
    company_name: Optional[str]
    subscription_tier: SubscriptionTier
    credits_balance: Decimal
    is_verified: bool
    created_at: datetime


class UserLogin(BaseSchema):
    email: str
    password: str


# Token schemas
class TokenResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseSchema):
    refresh_token: str


# API Key schemas
class ApiKeyCreate(BaseSchema):
    name: str = Field(..., max_length=100)
    permissions: Optional[List[str]] = Field(default_factory=list)


class ApiKeyResponse(BaseSchema):
    id: str
    public_key: str
    name: Optional[str]
    permissions: List[str]
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]


class ApiKeyWithSecret(ApiKeyResponse):
    secret_key: str  # Only shown once on creation


# Scraping Job schemas
class ScrapingConfig(BaseSchema):
    max_depth: int = Field(default=1, ge=1, le=10)
    max_pages: int = Field(default=100, ge=1, le=10000)
    timeout_seconds: int = Field(default=30, ge=5, le=300)
    follow_pagination: bool = True
    respect_robots_txt: bool = True
    delay_ms: int = Field(default=1000, ge=100, le=10000)
    user_agent: Optional[str] = None
    proxy_country: Optional[str] = None
    javascript_enabled: bool = True
    wait_for_selector: Optional[str] = None


class ScrapingInstruction(BaseSchema):
    target_url: HttpUrl
    instructions: str = Field(..., min_length=10, max_length=10000)
    output_schema: Optional[Dict[str, Any]] = None
    config: ScrapingConfig = Field(default_factory=ScrapingConfig)
    credentials_id: Optional[str] = None
    webhook_url: Optional[HttpUrl] = None


class ScrapingJobCreate(BaseSchema):
    name: Optional[str] = Field(None, max_length=255)
    instructions: ScrapingInstruction


class ScrapingJobResponse(BaseSchema):
    id: str
    name: Optional[str]
    status: JobStatus
    target_url: str
    pages_scraped: int
    pages_total: Optional[int]
    items_extracted: int
    credits_consumed: Decimal
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    estimated_duration_seconds: Optional[int]
    confidence_score: Optional[Decimal]


class ScrapingJobDetail(ScrapingJobResponse):
    instructions: str
    config: Dict[str, Any]
    result_data: Optional[Any]
    result_file_url: Optional[str]
    error_message: Optional[str]
    agents_used: List[str]
    llm_calls_made: int
    events: List[Dict[str, Any]]


class JobListResponse(BaseSchema):
    jobs: List[ScrapingJobResponse]
    total: int
    page: int
    page_size: int


class JobEventResponse(BaseSchema):
    id: str
    event_type: str
    severity: str
    message: Optional[str]
    agent_name: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime


# Billing schemas
class CreditPurchaseRequest(BaseSchema):
    amount_usd: Decimal = Field(..., gt=0)
    payment_method_id: Optional[str] = None


class CreditPurchaseResponse(BaseSchema):
    id: str
    credits_added: Decimal
    amount_paid: Decimal
    status: str
    stripe_payment_intent_id: Optional[str]


class UsageReport(BaseSchema):
    period_start: datetime
    period_end: datetime
    total_jobs: int
    total_pages_scraped: int
    total_credits_consumed: Decimal
    top_domains: List[Dict[str, Any]]
    cost_breakdown: Dict[str, Decimal]


# Webhook schemas
class WebhookPayload(BaseSchema):
    event_type: str
    job_id: str
    timestamp: datetime
    data: Dict[str, Any]


# Health check
class HealthCheck(BaseSchema):
    status: str
    version: str
    timestamp: datetime
    checks: Dict[str, Any]


# Pagination
class PaginationParams(BaseSchema):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size