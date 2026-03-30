# services/agent-service/app/events/consumer.py
# Kafka Event Consumer

import json
import structlog

from aiokafka import AIOKafkaConsumer

from app.agents.orchestrator import AgentOrchestrator
from app.config import settings

logger = structlog.get_logger()


class KafkaEventConsumer:
    """Consumes events from Kafka and triggers agent execution."""
    
    def __init__(self, consumer: AIOKafkaConsumer, orchestrator: AgentOrchestrator):
        self.consumer = consumer
        self.orchestrator = orchestrator
        self.logger = logger.bind(component="kafka_consumer")
        self.running = False
    
    @classmethod
    async def create(cls, orchestrator: AgentOrchestrator) -> "KafkaEventConsumer":
        """Factory method to create and initialize consumer."""
        consumer = AIOKafkaConsumer(
            *settings.KAFKA_TOPICS,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=settings.KAFKA_CONSUMER_GROUP,
            auto_offset_reset="earliest",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )
        await consumer.start()
        return cls(consumer, orchestrator)
    
    async def start(self):
        """Start consuming messages."""
        self.running = True
        self.logger.info("kafka_consumer_started")
        
        try:
            async for msg in self.consumer:
                if not self.running:
                    break
                
                await self._process_message(msg)
        except Exception as e:
            self.logger.error("consumer_error", error=str(e))
            raise
    
    async def _process_message(self, msg):
        """Process a single message."""
        try:
            self.logger.info(
                "message_received",
                topic=msg.topic,
                partition=msg.partition,
                offset=msg.offset,
            )
            
            event = msg.value
            
            if msg.topic == "scraping.jobs":
                await self._handle_job_event(event)
            elif msg.topic == "scraping.commands":
                await self._handle_command(event)
                
        except Exception as e:
            self.logger.error("message_processing_error", error=str(e))
    
    async def _handle_job_event(self, event: dict):
        """Handle job-related events."""
        event_type = event.get("event")
        
        if event_type == "job_queued":
            job_id = event.get("job_id")
            job_data = event.get("job_data", {})
            
            self.logger.info("executing_job", job_id=job_id)
            
            try:
                result = await self.orchestrator.execute_job(job_id, job_data)
                self.logger.info("job_completed", job_id=job_id, result=result)
            except Exception as e:
                self.logger.error("job_failed", job_id=job_id, error=str(e))
    
    async def _handle_command(self, event: dict):
        """Handle control commands."""
        command = event.get("command")
        
        if command == "cancel":
            job_id = event.get("job_id")
            self.logger.info("cancel_command_received", job_id=job_id)
            # Implement cancellation logic
    
    async def stop(self):
        """Stop the consumer."""
        self.running = False
        await self.consumer.stop()
        self.logger.info("kafka_consumer_stopped")