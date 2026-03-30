# services/agent-service/app/events/producer.py
# Kafka Event Producer

import json
import structlog
from typing import Any, Dict

from aiokafka import AIOKafkaProducer

from app.config import settings

logger = structlog.get_logger()


class KafkaEventProducer:
    """Produces events to Kafka topics."""
    
    def __init__(self, producer: AIOKafkaProducer):
        self.producer = producer
        self.logger = logger.bind(component="kafka_producer")
    
    @classmethod
    async def create(cls) -> "KafkaEventProducer":
        """Factory method to create producer."""
        producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
        )
        await producer.start()
        return cls(producer)
    
    async def send_event(
        self,
        topic: str,
        event: Dict[str, Any],
        key: str = None,
    ):
        """Send event to Kafka topic."""
        try:
            await self.producer.send(topic, value=event, key=key)
            self.logger.debug(
                "event_sent",
                topic=topic,
                event_type=event.get("event", "unknown"),
            )
        except Exception as e:
            self.logger.error("event_send_failed", topic=topic, error=str(e))
            raise
    
    async def send_job_update(
        self,
        job_id: str,
        status: str,
        data: Dict[str, Any] = None,
    ):
        """Send job status update."""
        await self.send_event(
            topic="scraping.updates",
            event={
                "job_id": job_id,
                "status": status,
                "data": data or {},
                "timestamp": json.dumps({}),  # Use proper timestamp
            },
            key=job_id,
        )
    
    async def stop(self):
        """Stop the producer."""
        await self.producer.stop()
        self.logger.info("kafka_producer_stopped")