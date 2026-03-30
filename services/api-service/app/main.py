# services/api-service/app/main.py
# FastAPI Application Entry Point - Production Ready

import asyncio
import signal
import sys
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessLogicError,
    RateLimitError,
    ScrapingError,
    ValidationError,
)
from app.core.middleware import (
    LoggingMiddleware,
    MetricsMiddleware,
    RequestIDMiddleware,
    TimingMiddleware,
)
from app.dependencies import get_kafka_producer, get_redis_pool
from app.models.database import init_db
from app.routers import (
    analytics,
    auth,
    billing,
    health,
    jobs,
    scraping,
    webhooks,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    settings = get_settings()
    
    # Startup
    logger.info(
        "api_service_starting",
        version=app.version,
        environment=settings.ENVIRONMENT,
    )
    
    try:
        # Initialize database
        await init_db()
        logger.info("database_initialized")
        
        # Initialize Redis connection pool
        redis_pool = await get_redis_pool()
        app.state.redis_pool = redis_pool
        logger.info("redis_connected")
        
        # Initialize Kafka producer
        kafka_producer = await get_kafka_producer()
        app.state.kafka_producer = kafka_producer
        logger.info("kafka_producer_ready")
        
        # Setup signal handlers for graceful shutdown
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(app)))
        
        logger.info("api_service_ready")
        yield
        
    except Exception as e:
        logger.error("startup_failed", error=str(e))
        raise
    finally:
        # Shutdown
        await shutdown(app)


async def shutdown(app: FastAPI):
    """Graceful shutdown handler."""
    logger.info("api_service_shutting_down")
    
    try:
        # Close Kafka producer
        if hasattr(app.state, "kafka_producer"):
            await app.state.kafka_producer.stop()
            logger.info("kafka_producer_closed")
        
        # Close Redis pool
        if hasattr(app.state, "redis_pool"):
            await app.state.redis_pool.close()
            logger.info("redis_pool_closed")
        
        logger.info("api_service_shutdown_complete")
    except Exception as e:
        logger.error("shutdown_error", error=str(e))
    
    sys.exit(0)


def create_application() -> FastAPI:
    """Application factory."""
    settings = get_settings()
    
    app = FastAPI(
        title="AI Scraping SaaS API",
        description="Enterprise-grade AI-powered web scraping platform",
        version="1.0.0",
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan,
    )
    
    # Middleware stack (order matters)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )
    
    # Exception handlers
    app.add_exception_handler(AuthenticationError, handle_auth_error)
    app.add_exception_handler(AuthorizationError, handle_authz_error)
    app.add_exception_handler(ValidationError, handle_validation_error)
    app.add_exception_handler(RateLimitError, handle_rate_limit_error)
    app.add_exception_handler(ScrapingError, handle_scraping_error)
    app.add_exception_handler(BusinessLogicError, handle_business_error)
    app.add_exception_handler(Exception, handle_generic_error)
    
    # Routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(scraping.router, prefix="/api/v1/scraping", tags=["Scraping"])
    app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
    app.include_router(billing.router, prefix="/api/v1/billing", tags=["Billing"])
    app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
    app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])
    
    return app


# Exception handlers
async def handle_auth_error(request: Request, exc: AuthenticationError):
    logger.warning("authentication_error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": str(exc), "type": "authentication_error"},
    )


async def handle_authz_error(request: Request, exc: AuthorizationError):
    logger.warning("authorization_error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": str(exc), "type": "authorization_error"},
    )


async def handle_validation_error(request: Request, exc: ValidationError):
    logger.warning("validation_error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc), "type": "validation_error", "errors": exc.errors},
    )


async def handle_rate_limit_error(request: Request, exc: RateLimitError):
    logger.warning("rate_limit_exceeded", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": str(exc), "type": "rate_limit_error", "retry_after": exc.retry_after},
        headers={"Retry-After": str(exc.retry_after)},
    )


async def handle_scraping_error(request: Request, exc: ScrapingError):
    logger.error("scraping_error", error=str(exc), path=request.url.path, job_id=exc.job_id)
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": str(exc), "type": "scraping_error", "job_id": exc.job_id},
    )


async def handle_business_error(request: Request, exc: BusinessLogicError):
    logger.warning("business_logic_error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "type": "business_error"},
    )


async def handle_generic_error(request: Request, exc: Exception):
    logger.exception("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "type": "internal_error"},
    )


# Create application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)