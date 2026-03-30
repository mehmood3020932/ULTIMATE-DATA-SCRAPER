# services/notification-service/app/main.py

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.events.consumer import start_consumer


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start Kafka consumer
    consumer_task = await start_consumer()
    yield
    # Stop consumer
    consumer_task.cancel()

app = FastAPI(
    title="Notification Service",
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
    return {"status": "healthy", "service": "notification-service"}