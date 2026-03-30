# services/analytics-service/app/main.py

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.analytics import router as analytics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(
    title="Analytics Service",
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

app.include_router(analytics_router, prefix="/analytics")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "analytics-service"}