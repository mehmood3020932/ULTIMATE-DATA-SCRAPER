# services/api-service/app/routers/jobs.py
# Job Management Endpoints (aliases for scraping)

from fastapi import APIRouter, Depends

from app.dependencies import get_current_active_user
from app.models.schemas import UserResponse

router = APIRouter()


@router.get("/status")
async def get_system_status(
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Get current system status and queue information.
    """
    # This would integrate with the job queue system
    return {
        "queue_depth": 0,
        "active_workers": 0,
        "average_wait_time_seconds": 0,
        "system_load": "normal",
    }