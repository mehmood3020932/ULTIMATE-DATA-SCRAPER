# app/events/consumer.py
# Kafka consumer for notifications

import asyncio
import json

import aiokafka
import structlog

from app.config import settings
from app.services.email_service import EmailService

logger = structlog.get_logger()


class NotificationConsumer:
    """Consumes notification events from Kafka."""
    
    def __init__(self):
        self.consumer = None
        self.email_service = EmailService()
    
    async def start(self):
        """Start consuming."""
        self.consumer = aiokafka.AIOKafkaConsumer(
            "notifications",
            bootstrap_servers=settings.KAFKA_BROKERS,
            group_id="notification-service",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )
        await self.consumer.start()
        
        logger.info("notification_consumer_started")
        
        try:
            async for msg in self.consumer:
                await self._process_message(msg.value)
        finally:
            await self.consumer.stop()
    
    async def _process_message(self, event: dict):
        """Process notification event."""
        event_type = event.get("type")
        
        if event_type == "email":
            await self.email_service.send_email(
                to_email=event["to"],
                subject=event["subject"],
                template_name=event["template"],
                context=event["context"],
            )
        elif event_type == "job_complete":
            await self.email_service.send_job_completion(
                to_email=event["to_email"],
                job_id=event["job_id"],
                success=event["success"],
            )
        
        logger.info("notification_sent", type=event_type)


async def start_consumer():
    """Entry point for starting consumer."""
    consumer = NotificationConsumer()
    await consumer.start()