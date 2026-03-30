# services/analytics-service/app/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Analytics Service"
    PORT: int = 8003
    
    # Elasticsearch
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_INDEX_PREFIX: str = "scraping"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Kafka
    KAFKA_BROKERS: str = "localhost:9092"
    
    class Config:
        env_file = ".env"


settings = Settings()