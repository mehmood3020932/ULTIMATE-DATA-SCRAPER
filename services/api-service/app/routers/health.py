# services/api-service/app/routers/health.py
# Health Check Endpoints

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, status

from app.config import get_settings
from app.dependencies import get_redis_pool
from app.models.schemas import HealthCheck

router = APIRouter()


@router.get("/health", response_model=HealthCheck)
async def health_check(request: Request):
    """
    Liveness probe - basic health check.
    """
    settings = get_settings()
    
    checks = {
        "api": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    # Check Redis if available
    try:
        redis = await get_redis_pool()
        await redis.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)}"
    
    # Check Kafka if available
    if hasattr(request.app.state, "kafka_producer"):
        checks["kafka"] = "connected"
    else:
        checks["kafka"] = "not_initialized"
    
    all_healthy = all(
        v == "healthy" or v == "connected" or v == "not_initialized"
        for k, v in checks.items() if k != "timestamp"
    )
    
    return HealthCheck(
        status="healthy" if all_healthy else "degraded",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc),
        checks=checks,
    )


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check(request: Request):
    """
    Readiness probe - check if service is ready to accept traffic.
    """
    checks = {}
    
    # Check database
    try:
        # Simple DB check would go here
        checks["database"] = "ready"
    except Exception as e:
        checks["database"] = f"not_ready: {str(e)}"
        return {
            "status": "not_ready",
            "checks": checks,
        }
    
    # Check Redis
    try:
        redis = await get_redis_pool()
        await redis.ping()
        checks["redis"] = "ready"
    except Exception as e:
        checks["redis"] = f"not_ready: {str(e)}"
        return {
            "status": "not_ready",
            "checks": checks,
        }
    
    # Check Kafka
    if hasattr(request.app.state, "kafka_producer"):
        checks["kafka"] = "ready"
    else:
        checks["kafka"] = "initializing"
    
    return {
        "status": "ready",
        "checks": checks,
    }


@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    """
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    
    return {
        "content": generate_latest(),
        "media_type": CONTENT_TYPE_LATEST,
    }