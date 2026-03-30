# services/agent-service/app/main.py
# Agent Service - AI Agent Orchestration

import asyncio
import signal
import sys
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents.orchestrator import AgentOrchestrator
from app.config import Settings
from app.events.consumer import KafkaEventConsumer
from app.events.producer import KafkaEventProducer

logger = structlog.get_logger()
settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("agent_service_starting")
    
    # Initialize components
    app.state.kafka_producer = await KafkaEventProducer.create()
    app.state.agent_orchestrator = AgentOrchestrator(app.state.kafka_producer)
    app.state.kafka_consumer = await KafkaEventConsumer.create(
        app.state.agent_orchestrator
    )
    
    # Start consumer in background
    consumer_task = asyncio.create_task(app.state.kafka_consumer.start())
    
    logger.info("agent_service_ready")
    
    yield
    
    # Shutdown
    logger.info("agent_service_shutting_down")
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass
    
    await app.state.kafka_consumer.stop()
    await app.state.kafka_producer.stop()
    logger.info("agent_service_shutdown_complete")


app = FastAPI(
    title="AI Agent Service",
    description="Multi-agent AI scraping orchestration",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "agent-service"}


@app.get("/agents")
async def list_agents():
    """List available agents."""
    return {
        "agents": [
            {"name": "planner", "description": "Plans scraping strategy"},
            {"name": "auth", "description": "Handles authentication"},
            {"name": "browser", "description": "Manages browser interactions"},
            {"name": "navigator", "description": "Navigates websites"},
            {"name": "dom_analyzer", "description": "Analyzes DOM structure"},
            {"name": "pattern_detector", "description": "Detects data patterns"},
            {"name": "extractor", "description": "Extracts data"},
            {"name": "pagination", "description": "Handles pagination"},
            {"name": "anti_block", "description": "Manages anti-blocking"},
            {"name": "validator", "description": "Validates extracted data"},
            {"name": "cleaner", "description": "Cleans and formats data"},
            {"name": "output", "description": "Generates output formats"},
            {"name": "memory", "description": "Manages context memory"},
        ]
    }


@app.post("/execute")
async def execute_job(job_id: str, instructions: dict):
    """Manually trigger job execution (for testing)."""
    result = await app.state.agent_orchestrator.execute_job(job_id, instructions)
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)