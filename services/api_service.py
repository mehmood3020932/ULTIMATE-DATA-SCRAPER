from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uuid
from typing import Optional

from shared.config import get_settings
from shared.models import JobCreateRequest, JobResponse, JobStatus, ScrapingJob
from shared.exceptions import ValidationError, ScraperJobError
from shared.logger import setup_logger

logger = setup_logger(__name__)
settings = get_settings()

# In-memory job storage (replace with database in production)
jobs_db = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("API Service starting up")
    yield
    # Shutdown
    logger.info("API Service shutting down")

app = FastAPI(
    title="AI Scraping SaaS API",
    description="Enterprise-grade web scraping platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }

@app.post("/jobs", response_model=JobResponse, tags=["Jobs"])
async def create_job(request: JobCreateRequest):
    """Create a new scraping job"""
    try:
        job_id = str(uuid.uuid4())
        job = ScrapingJob(
            id=job_id,
            user_id="default_user",  # Replace with actual user from auth
            url=request.url,
            instruction=request.instruction
        )
        jobs_db[job_id] = job
        logger.info(f"Created job {job_id} for URL {request.url}")
        
        return JobResponse(
            id=job.id,
            status=job.status,
            result=job.result,
            error=job.error,
            created_at=job.created_at
        )
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/jobs/{job_id}", response_model=JobResponse, tags=["Jobs"])
async def get_job(job_id: str):
    """Get job status and results"""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_db[job_id]
    return JobResponse(
        id=job.id,
        status=job.status,
        result=job.result,
        error=job.error,
        created_at=job.created_at
    )

@app.get("/jobs", tags=["Jobs"])
async def list_jobs(limit: int = 10, offset: int = 0):
    """List all jobs"""
    jobs_list = list(jobs_db.values())[offset:offset+limit]
    return {
        "total": len(jobs_db),
        "limit": limit,
        "offset": offset,
        "jobs": [
            JobResponse(
                id=job.id,
                status=job.status,
                result=job.result,
                error=job.error,
                created_at=job.created_at
            ) for job in jobs_list
        ]
    }

@app.get("/stats", tags=["Analytics"])
async def get_stats():
    """Get scraping statistics"""
    total_jobs = len(jobs_db)
    completed = sum(1 for j in jobs_db.values() if j.status == JobStatus.COMPLETED)
    failed = sum(1 for j in jobs_db.values() if j.status == JobStatus.FAILED)
    
    return {
        "total_jobs": total_jobs,
        "completed": completed,
        "failed": failed,
        "success_rate": (completed / total_jobs * 100) if total_jobs > 0 else 0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        debug=settings.DEBUG
    )