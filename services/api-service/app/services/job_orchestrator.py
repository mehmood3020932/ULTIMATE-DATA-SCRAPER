# services/api-service/app/services/job_orchestrator.py
# Job Orchestration Service

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import aiokafka
import redis.asyncio as redis
import ulid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import (
    ResourceNotFoundError,
    ScrapingError,
    ValidationError,
)
from app.models.database import JobEvent, ScrapingJob
from app.models.schemas import (
    ScrapingInstruction,
    ScrapingJobDetail,
    ScrapingJobResponse,
)


class JobOrchestrator:
    """Orchestrates scraping jobs across the distributed system."""
    
    KAFKA_TOPIC_JOBS = "scraping.jobs"
    KAFKA_TOPIC_COMMANDS = "scraping.commands"
    REDIS_JOB_PREFIX = "job:"
    REDIS_QUEUE_KEY = "scraping:queue"
    
    def __init__(
        self,
        db: AsyncSession,
        redis_pool: redis.Redis,
        kafka_producer: aiokafka.AIOKafkaProducer,
    ):
        self.db = db
        self.redis = redis_pool
        self.kafka = kafka_producer
    
    async def create_job(
        self,
        user_id: str,
        name: Optional[str],
        instructions: ScrapingInstruction,
    ) -> ScrapingJobResponse:
        """Create a new scraping job."""
        job_id = str(ulid.new())
        
        # Estimate credits needed
        estimated_credits = self._estimate_credits(instructions)
        
        job = ScrapingJob(
            id=job_id,
            user_id=user_id,
            name=name or f"Job {job_id[:8]}",
            status="pending",
            target_url=str(instructions.target_url),
            instructions=instructions.instructions,
            schema_definition=instructions.output_schema,
            config=instructions.config.model_dump(),
            pages_total=instructions.config.max_pages,
            estimated_duration_seconds=self._estimate_duration(instructions),
        )
        
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        
        return ScrapingJobResponse.model_validate(job)
    
    async def queue_job(self, job_id: str) -> None:
        """Queue job for processing."""
        # Add to Redis queue
        await self.redis.lpush(self.REDIS_QUEUE_KEY, job_id)
        
        # Update job status
        result = await self.db.execute(
            select(ScrapingJob).where(ScrapingJob.id == job_id)
        )
        job = result.scalar_one()
        job.status = "queued"
        await self.db.commit()
        
        # Publish to Kafka for agent service
        await self.kafka.send(
            self.KAFKA_TOPIC_JOBS,
            json.dumps({
                "event": "job_queued",
                "job_id": job_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }).encode(),
        )
    
    async def list_jobs(
        self,
        user_id: str,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ScrapingJobResponse], int]:
        """List user's jobs with pagination."""
        query = select(ScrapingJob).where(ScrapingJob.user_id == user_id)
        
        if status:
            query = query.where(ScrapingJob.status == status)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.order_by(ScrapingJob.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        jobs = result.scalars().all()
        
        return [ScrapingJobResponse.model_validate(job) for job in jobs], total
    
    async def get_job_detail(
        self,
        job_id: str,
        user_id: str,
    ) -> ScrapingJobDetail:
        """Get detailed job information."""
        result = await self.db.execute(
            select(ScrapingJob).where(
                ScrapingJob.id == job_id,
                ScrapingJob.user_id == user_id,
            )
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise ResourceNotFoundError("Job not found")
        
        # Get events
        events_result = await self.db.execute(
            select(JobEvent).where(JobEvent.job_id == job_id)
            .order_by(JobEvent.created_at.desc())
        )
        events = events_result.scalars().all()
        
        job_detail = ScrapingJobDetail.model_validate(job)
        job_detail.events = [
            {
                "id": e.id,
                "type": e.event_type,
                "severity": e.severity,
                "message": e.message,
                "agent": e.agent_name,
                "timestamp": e.created_at.isoformat(),
            }
            for e in events
        ]
        
        return job_detail
    
    async def cancel_job(self, job_id: str, user_id: str) -> ScrapingJobResponse:
        """Cancel a job."""
        result = await self.db.execute(
            select(ScrapingJob).where(
                ScrapingJob.id == job_id,
                ScrapingJob.user_id == user_id,
            )
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise ResourceNotFoundError("Job not found")
        
        if job.status not in ["pending", "queued", "running"]:
            raise ValidationError(f"Cannot cancel job with status: {job.status}")
        
        # Remove from queue if pending
        if job.status == "queued":
            await self.redis.lrem(self.REDIS_QUEUE_KEY, 0, job_id)
        
        # Send cancel command
        await self.kafka.send(
            self.KAFKA_TOPIC_COMMANDS,
            json.dumps({
                "command": "cancel",
                "job_id": job_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }).encode(),
        )
        
        job.status = "cancelled"
        await self.db.commit()
        await self.db.refresh(job)
        
        return ScrapingJobResponse.model_validate(job)
    
    async def retry_job(self, job_id: str, user_id: str) -> ScrapingJobResponse:
        """Retry a failed job."""
        result = await self.db.execute(
            select(ScrapingJob).where(
                ScrapingJob.id == job_id,
                ScrapingJob.user_id == user_id,
            )
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise ResourceNotFoundError("Job not found")
        
        if job.status != "failed":
            raise ValidationError("Only failed jobs can be retried")
        
        # Reset job state
        job.status = "pending"
        job.error_message = None
        job.pages_scraped = 0
        job.items_extracted = 0
        job.credits_consumed = 0
        
        await self.db.commit()
        
        # Re-queue
        await self.queue_job(job_id)
        
        return ScrapingJobResponse.model_validate(job)
    
    async def get_download_url(
        self,
        job_id: str,
        user_id: str,
        format: str,
    ) -> str:
        """Generate presigned download URL for job results."""
        result = await self.db.execute(
            select(ScrapingJob).where(
                ScrapingJob.id == job_id,
                ScrapingJob.user_id == user_id,
            )
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise ResourceNotFoundError("Job not found")
        
        if job.status != "completed":
            raise ValidationError("Job not completed yet")
        
        # Generate presigned URL (implementation depends on storage backend)
        # This is a placeholder
        return f"https://storage.example.com/jobs/{job_id}/results.{format}?token=signed"
    
    async def get_job_events(
        self,
        job_id: str,
        user_id: str,
    ) -> List[Dict[str, Any]]:
        """Get job events."""
        # Verify job ownership
        result = await self.db.execute(
            select(ScrapingJob).where(
                ScrapingJob.id == job_id,
                ScrapingJob.user_id == user_id,
            )
        )
        if not result.scalar_one_or_none():
            raise ResourceNotFoundError("Job not found")
        
        events_result = await self.db.execute(
            select(JobEvent).where(JobEvent.job_id == job_id)
            .order_by(JobEvent.created_at.desc())
        )
        events = events_result.scalars().all()
        
        return [
            {
                "id": e.id,
                "type": e.event_type,
                "severity": e.severity,
                "message": e.message,
                "agent": e.agent_name,
                "metadata": e.metadata,
                "timestamp": e.created_at.isoformat(),
            }
            for e in events
        ]
    
    async def analyze_instructions(
        self,
        instructions: ScrapingInstruction,
    ) -> Dict[str, Any]:
        """Analyze instructions and estimate cost/complexity."""
        # This would call the agent service for analysis
        estimated_credits = self._estimate_credits(instructions)
        estimated_duration = self._estimate_duration(instructions)
        
        return {
            "complexity": "medium",  # simple, medium, complex
            "estimated_credits": estimated_credits,
            "estimated_duration_seconds": estimated_duration,
            "max_pages": instructions.config.max_pages,
            "recommendations": [
                "Consider reducing max_pages for faster results",
                "Enable JavaScript for dynamic content",
            ],
        }
    
    def _estimate_credits(self, instructions: ScrapingInstruction) -> float:
        """Estimate credits needed for job."""
        base_cost = 1.0
        page_cost = 0.1 * instructions.config.max_pages
        ai_cost = 0.5 if instructions.instructions else 0
        
        return base_cost + page_cost + ai_cost
    
    def _estimate_duration(self, instructions: ScrapingInstruction) -> int:
        """Estimate job duration in seconds."""
        base_time = 10
        page_time = 5 * instructions.config.max_pages
        ai_time = 30 if instructions.instructions else 0
        
        return base_time + page_time + ai_time