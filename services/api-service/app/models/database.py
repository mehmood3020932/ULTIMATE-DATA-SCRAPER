# services/api-service/app/models/database.py
# SQLAlchemy Database Models & Connection

from datetime import datetime, timezone
from typing import AsyncGenerator, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import (
    declarative_base,
    relationship,
    selectinload,
)
from sqlalchemy.pool import NullPool

from app.config import get_settings

Base = declarative_base()


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class User(Base, TimestampMixin):
    """User account model."""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    company_name = Column(String(255))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    
    # Subscription
    subscription_tier = Column(String(50), default="free")
    subscription_status = Column(String(50), default="active")
    subscription_expires_at = Column(DateTime(timezone=True))
    
    # Credits
    credits_balance = Column(Numeric(15, 2), default=0)
    credits_used_total = Column(Numeric(15, 2), default=0)
    
    # Relations
    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("ScrapingJob", back_populates="user")
    billing_records = relationship("BillingRecord", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class ApiKey(Base, TimestampMixin):
    """API key model."""
    __tablename__ = "api_keys"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Key data
    public_key = Column(String(64), unique=True, nullable=False, index=True)
    key_hash = Column(String(255), nullable=False)
    name = Column(String(100))
    
    # Permissions
    permissions = Column(JSON, default=list)  # ["scraping:read", "scraping:write", "billing:read"]
    
    # Status
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    
    # Relations
    user = relationship("User", back_populates="api_keys")
    
    def __repr__(self):
        return f"<ApiKey(id={self.id}, name={self.name})>"


class ScrapingJob(Base, TimestampMixin):
    """Scraping job model."""
    __tablename__ = "scraping_jobs"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Job configuration
    name = Column(String(255))
    status = Column(String(50), default="pending", index=True)  # pending, running, completed, failed, cancelled
    priority = Column(Integer, default=5)  # 1-10
    
    # Input
    target_url = Column(Text, nullable=False)
    instructions = Column(Text)  # Natural language instructions
    schema_definition = Column(JSON)  # Expected output schema
    
    # Configuration
    config = Column(JSON, default=dict)  # depth, pagination, selectors, etc.
    credentials_id = Column(String(36), ForeignKey("stored_credentials.id"))
    
    # Progress
    pages_scraped = Column(Integer, default=0)
    pages_total = Column(Integer)
    items_extracted = Column(Integer, default=0)
    credits_consumed = Column(Numeric(10, 4), default=0)
    
    # Results
    result_data = Column(JSON)
    result_file_url = Column(String(500))
    error_message = Column(Text)
    
    # Timing
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    estimated_duration_seconds = Column(Integer)
    
    # AI metadata
    agents_used = Column(JSON, default=list)
    llm_calls_made = Column(Integer, default=0)
    confidence_score = Column(Numeric(3, 2))  # 0.00 - 1.00
    
    # Relations
    user = relationship("User", back_populates="jobs")
    credentials = relationship("StoredCredentials")
    events = relationship("JobEvent", back_populates="job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ScrapingJob(id={self.id}, status={self.status})>"


class JobEvent(Base, TimestampMixin):
    """Job lifecycle events."""
    __tablename__ = "job_events"
    
    id = Column(String(36), primary_key=True)
    job_id = Column(String(36), ForeignKey("scraping_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    event_type = Column(String(50), nullable=False)  # started, progress, agent_started, agent_completed, error, completed
    severity = Column(String(20), default="info")  # debug, info, warning, error, critical
    
    message = Column(Text)
    metadata = Column(JSON)
    agent_name = Column(String(50))
    
    # Relations
    job = relationship("ScrapingJob", back_populates="events")
    
    def __repr__(self):
        return f"<JobEvent(id={self.id}, type={self.event_type})>"


class StoredCredentials(Base, TimestampMixin):
    """Encrypted stored credentials for scraping."""
    __tablename__ = "stored_credentials"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(100))
    credential_type = Column(String(50))  # basic_auth, api_key, oauth2, cookies
    
    # Encrypted data
    encrypted_data = Column(Text, nullable=False)
    iv = Column(String(32))  # Initialization vector
    
    # Metadata
    domain = Column(String(255))  # Associated domain
    expires_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<StoredCredentials(id={self.id}, type={self.credential_type})>"


class BillingRecord(Base, TimestampMixin):
    """Billing and usage records."""
    __tablename__ = "billing_records"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    record_type = Column(String(50))  # credit_purchase, usage_charge, refund
    amount = Column(Numeric(10, 2))
    currency = Column(String(3), default="USD")
    
    # Credits
    credits_amount = Column(Numeric(10, 2))
    credits_balance_after = Column(Numeric(15, 2))
    
    # Related job
    job_id = Column(String(36), ForeignKey("scraping_jobs.id"))
    
    # Stripe
    stripe_payment_intent_id = Column(String(100))
    stripe_invoice_id = Column(String(100))
    
    # Status
    status = Column(String(50), default="pending")  # pending, completed, failed, refunded
    
    # Relations
    user = relationship("User", back_populates="billing_records")
    
    def __repr__(self):
        return f"<BillingRecord(id={self.id}, type={self.record_type})>"


class LLMUsageLog(Base):
    """Log of LLM API calls for cost tracking."""
    __tablename__ = "llm_usage_logs"
    
    id = Column(String(36), primary_key=True)
    job_id = Column(String(36), ForeignKey("scraping_jobs.id"), index=True)
    
    provider = Column(String(50))  # openai, anthropic, google, local
    model = Column(String(100))
    
    # Usage
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    
    # Cost
    cost_usd = Column(Numeric(10, 6))
    
    # Performance
    latency_ms = Column(Integer)
    success = Column(Boolean)
    error_message = Column(Text)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<LLMUsageLog(id={self.id}, provider={self.provider})>"


# Database engine and session
_engine = None
_async_session_maker = None


async def init_db():
    """Initialize database tables."""
    settings = get_settings()
    engine = create_async_engine(
        settings.database_async_url,
        echo=settings.is_development,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()


def get_engine():
    """Get or create async engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_async_url,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_timeout=settings.DATABASE_POOL_TIMEOUT,
            pool_recycle=3600,
        )
    return _engine


def get_session_maker():
    """Get or create session maker."""
    global _async_session_maker
    if _async_session_maker is None:
        engine = get_engine()
        _async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _async_session_maker


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for dependency injection."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncSession:
    """Get database session directly."""
    session_maker = get_session_maker()
    return session_maker()