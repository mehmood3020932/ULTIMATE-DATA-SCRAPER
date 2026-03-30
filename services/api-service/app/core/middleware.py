# services/api-service/app/core/middleware.py
# Custom Middleware - Request ID, Logging, Metrics, Timing

import time
import uuid
from typing import Callable

import structlog
from fastapi import Request, Response
from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"],
)
ACTIVE_REQUESTS = Counter(
    "http_active_requests",
    "Active HTTP requests",
    ["method"],
)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get request ID from header or generate new
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        # Add to logger context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            path=request.url.path,
            method=request.method,
        )
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with structured logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request
        logger.info(
            "request_started",
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            content_length=request.headers.get("content-length"),
        )
        
        response = await call_next(request)
        
        # Log response
        duration = time.time() - start_time
        logger.info(
            "request_completed",
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2),
            content_length=response.headers.get("content-length"),
        )
        
        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """Record Prometheus metrics for requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        ACTIVE_REQUESTS.labels(method=request.method).inc()
        
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Record metrics
        endpoint = request.url.path
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code,
        ).inc()
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=endpoint,
        ).observe(duration)
        ACTIVE_REQUESTS.labels(method=request.method).dec()
        
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Add timing headers to responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        return response