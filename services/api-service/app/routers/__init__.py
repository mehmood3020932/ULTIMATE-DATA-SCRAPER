# app/routers/__init__.py
from app.routers.auth import router as auth_router
from app.routers.jobs import router as jobs_router
from app.routers.scraping import router as scraping_router
from app.routers.billing import router as billing_router
from app.routers.analytics import router as analytics_router
from app.routers.webhooks import router as webhooks_router
from app.routers.health import router as health_router

__all__ = [
    "auth_router",
    "jobs_router",
    "scraping_router",
    "billing_router",
    "analytics_router",
    "webhooks_router",
    "health_router",
]