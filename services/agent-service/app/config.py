# services/agent-service/app/config.py
# Agent Service Configuration

from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Agent service settings."""
    
    # Application
    APP_NAME: str = "AI Agent Service"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    
    # LLM Providers
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"
    
    GOOGLE_API_KEY: Optional[str] = None
    GOOGLE_MODEL: str = "gemini-pro"
    
    LOCAL_LLM_URL: Optional[str] = None
    LOCAL_LLM_MODEL: str = "llama2-70b"
    
    # Default LLM routing
    DEFAULT_PROVIDER: str = "openai"
    FALLBACK_PROVIDERS: List[str] = ["anthropic", "google", "local"]
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_CONSUMER_GROUP: str = "agent-service"
    KAFKA_TOPICS: List[str] = ["scraping.jobs", "scraping.commands"]
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Agent Configuration
    MAX_AGENT_ITERATIONS: int = 50
    AGENT_TIMEOUT_SECONDS: int = 300
    PARALLEL_AGENTS: int = 4
    
    # Consensus
    CONSENSUS_THRESHOLD: float = 0.7
    MIN_CONFIDENCE_SCORE: float = 0.6
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()