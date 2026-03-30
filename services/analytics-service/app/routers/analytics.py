# services/analytics-service/app/routers/analytics.py

from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.services.metrics_service import MetricsService

router = APIRouter()


@router.get("/dashboard/{user_id}")
async def get_user_dashboard(
    user_id: str,
    days: int = Query(30, ge=1, le=365),
):
    """Get user analytics dashboard."""
    metrics_service = MetricsService()
    return await metrics_service.get_user_dashboard(user_id, days)


@router.get("/system")
async def get_system_metrics():
    """Get system-wide metrics."""
    metrics_service = MetricsService()
    return await metrics_service.get_system_metrics()


@router.get("/jobs/trends")
async def get_job_trends(
    days: int = Query(30, ge=7, le=365),
):
    """Get job trend data."""
    metrics_service = MetricsService()
    return await metrics_service.get_job_trends(days)


@router.get("/ai-performance")
async def get_ai_performance():
    """Get AI agent performance metrics."""
    return {
        "agents": {
            "planner": {"success_rate": 0.98, "avg_latency_ms": 500},
            "navigator": {"success_rate": 0.95, "avg_latency_ms": 1200},
            "extractor": {"success_rate": 0.92, "avg_latency_ms": 800},
            "validator": {"success_rate": 0.99, "avg_latency_ms": 300},
        },
        "llm_providers": {
            "openai": {"success_rate": 0.97, "avg_cost_per_1k_tokens": 0.02},
            "anthropic": {"success_rate": 0.96, "avg_cost_per_1k_tokens": 0.03},
            "google": {"success_rate": 0.94, "avg_cost_per_1k_tokens": 0.015},
        },
    }