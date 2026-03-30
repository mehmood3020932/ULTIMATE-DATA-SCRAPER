# app/models/enums.py
from enum import Enum


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


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PAST_DUE = "past_due"


class BillingRecordType(str, Enum):
    CREDIT_PURCHASE = "credit_purchase"
    USAGE_CHARGE = "usage_charge"
    REFUND = "refund"
    SUBSCRIPTION = "subscription"


class CredentialType(str, Enum):
    BASIC_AUTH = "basic_auth"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    COOKIES = "cookies"


class EventSeverity(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"