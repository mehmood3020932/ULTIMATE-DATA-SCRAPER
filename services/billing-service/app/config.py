# services/billing-service/app/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Billing Service"
    ENVIRONMENT: str = "development"
    PORT: int = 8002
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://localhost/billing"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Stripe
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_PUBLISHABLE_KEY: str
    
    # Kafka
    KAFKA_BROKERS: str = "localhost:9092"
    
    class Config:
        env_file = ".env"


settings = Settings()