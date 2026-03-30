# services/notification-service/app/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Notification Service"
    PORT: int = 8004
    
    # SMTP
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    EMAIL_FROM: str
    
    # Kafka
    KAFKA_BROKERS: str = "localhost:9092"
    
    # Templates
    TEMPLATE_DIR: str = "app/templates"
    
    class Config:
        env_file = ".env"


settings = Settings()