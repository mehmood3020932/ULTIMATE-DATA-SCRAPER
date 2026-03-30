# services/api-service/app/routers/scraping.py
# Scraping Job Endpoints

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.dependencies import (
    get_current_active_user,
    get_db_session,
    get_job_orchestrator,
)
from app.models.schemas import (
    ScrapingInstruction,
    ScrapingJobCreate,
    ScrapingJobDetail,
    ScrapingJobResponse,
    JobListResponse,
    UserResponse,
)
from app.services.job_orchestrator import JobOrchestrator

router = APIRouter()


@router.post("/jobs", response_model=ScrapingJobResponse, status_code=status.HTTP_201_CREATED)
async def create_scraping_job(
    job_data: ScrapingJobCreate,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_active_user),
    orchestrator: JobOrchestrator = Depends(get_job_orchestrator),
):
    """
    Create a new AI-powered scraping job.
    
    The job will be queued and processed by the agent service.
    """
    # Validate user has sufficient credits
    if current_user.credits_balance <= 0 and current_user.subscription_tier == "free":
        raise ValidationError("Insufficient credits. Please purchase credits or upgrade your plan.")
    
    # Create job
    job = await orchestrator.create_job(
        user_id=current_user.id,
        name=job_data.name,
        instructions=job_data.instructions,
    )
    
    # Queue job for processing
    await orchestrator.queue_job(job.id)
    
    return job


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_active_user),
    orchestrator: JobOrchestrator = Depends(get_job_orchestrator),
):
    """
    List user's scraping jobs with pagination.
    """
    jobs, total = await orchestrator.list_jobs(
        user_id=current_user.id,
        status=status,
        page=page,
        page_size=page_size,
    )
    
    return JobListResponse(
        jobs=jobs,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/jobs/{job_id}", response_model=ScrapingJobDetail)
async def get_job(
    job_id: str,
    current_user: UserResponse = Depends(get_current_active_user),
    orchestrator: JobOrchestrator = Depends(get_job_orchestrator),
):
    """
    Get detailed information about a scraping job.
    """
    job = await orchestrator.get_job_detail(job_id, current_user.id)
    return job


@router.post("/jobs/{job_id}/cancel", response_model=ScrapingJobResponse)
async def cancel_job(
    job_id: str,
    current_user: UserResponse = Depends(get_current_active_user),
    orchestrator: JobOrchestrator = Depends(get_job_orchestrator),
):
    """
    Cancel a running or pending scraping job.
    """
    job = await orchestrator.cancel_job(job_id, current_user.id)
    return job


@router.get("/jobs/{job_id}/download")
async def download_results(
    job_id: str,
    format: str = Query("json", regex="^(json|csv|xlsx)$"),
    current_user: UserResponse = Depends(get_current_active_user),
    orchestrator: JobOrchestrator = Depends(get_job_orchestrator),
):
    """
    Download job results in specified format.
    """
    download_url = await orchestrator.get_download_url(
        job_id=job_id,
        user_id=current_user.id,
        format=format,
    )
    
    return {"download_url": download_url, "format": format, "expires_in": 3600}


@router.post("/jobs/{job_id}/retry", response_model=ScrapingJobResponse)
async def retry_job(
    job_id: str,
    current_user: UserResponse = Depends(get_current_active_user),
    orchestrator: JobOrchestrator = Depends(get_job_orchestrator),
):
    """
    Retry a failed scraping job.
    """
    job = await orchestrator.retry_job(job_id, current_user.id)
    return job


@router.get("/jobs/{job_id}/events")
async def get_job_events(
    job_id: str,
    current_user: UserResponse = Depends(get_current_active_user),
    orchestrator: JobOrchestrator = Depends(get_job_orchestrator),
):
    """
    Get real-time events for a job.
    """
    events = await orchestrator.get_job_events(job_id, current_user.id)
    return events


@router.post("/validate-instructions")
async def validate_instructions(
    instructions: ScrapingInstruction,
    current_user: UserResponse = Depends(get_current_active_user),
    orchestrator: JobOrchestrator = Depends(get_job_orchestrator),
):
    """
    Validate scraping instructions without creating a job.
    Returns estimated cost and complexity analysis.
    """
    analysis = await orchestrator.analyze_instructions(instructions)
    return analysis