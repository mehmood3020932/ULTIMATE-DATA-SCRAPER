# services/api-service/app/services/notification_service.py
# Notification Service - Multi-channel notifications

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import aiohttp
import structlog

from app.config import get_settings

logger = structlog.get_logger()


class NotificationService:
    """Handles multi-channel notifications."""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logger.bind(service="notification")
    
    async def send_job_completion(
        self,
        user_id: str,
        job_id: str,
        email: Optional[str],
        webhook_url: Optional[str],
        success: bool,
        items_count: int,
    ):
        """Send job completion notification."""
        tasks = []
        
        if email:
            tasks.append(self._send_email_notification(
                email=email,
                subject=f"Scraping Job {'Completed' if success else 'Failed'}",
                template="job_complete",
                context={
                    "job_id": job_id,
                    "success": success,
                    "items_count": items_count,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            ))
        
        if webhook_url:
            tasks.append(self._send_webhook(
                url=webhook_url,
                payload={
                    "event": "job.completed",
                    "job_id": job_id,
                    "user_id": user_id,
                    "success": success,
                    "items_extracted": items_count,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            ))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_email_notification(
        self,
        email: str,
        subject: str,
        template: str,
        context: Dict[str, Any],
    ):
        """Send email notification."""
        try:
            # Implementation would use SMTP or email service
            self.logger.info(
                "email_sent",
                to=email,
                subject=subject,
                template=template,
            )
        except Exception as e:
            self.logger.error("email_failed", error=str(e))
    
    async def _send_webhook(self, url: str, payload: Dict[str, Any]):
        """Send webhook notification."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-Webhook-Secret": self.settings.WEBHOOK_SECRET or "",
                    },
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status >= 400:
                        self.logger.warning(
                            "webhook_failed",
                            url=url,
                            status=response.status,
                        )
                    else:
                        self.logger.info("webhook_sent", url=url)
        except Exception as e:
            self.logger.error("webhook_error", url=url, error=str(e))
    
    async def send_low_credits_alert(self, email: str, balance: float):
        """Send low credits alert."""
        await self._send_email_notification(
            email=email,
            subject="Low Credits Alert",
            template="low_credits",
            context={"balance": balance},
        )