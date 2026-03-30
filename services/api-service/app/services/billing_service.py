# services/api-service/app/services/billing_service.py
# Billing & Payment Service

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import BusinessLogicError, ExternalServiceError
from app.models.database import BillingRecord, User


class BillingService:
    """Handle billing, payments, and credit management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        settings = get_settings()
        stripe.api_key = settings.STRIPE_SECRET_KEY
    
    async def purchase_credits(
        self,
        user_id: str,
        amount_usd: Decimal,
        payment_method_id: Optional[str] = None,
        client_ip: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process credit purchase via Stripe."""
        settings = get_settings()
        
        # Calculate credits (1 USD = 100 credits)
        credits_to_add = amount_usd * 100
        
        try:
            # Create payment intent
            intent_data = {
                "amount": int(amount_usd * 100),  # Convert to cents
                "currency": "usd",
                "metadata": {
                    "user_id": user_id,
                    "credits": str(credits_to_add),
                },
            }
            
            if payment_method_id:
                intent_data["payment_method"] = payment_method_id
                intent_data["confirm"] = True
            
            if client_ip:
                intent_data["description"] = f"Credit purchase from {client_ip}"
            
            intent = stripe.PaymentIntent.create(**intent_data)
            
            # Create billing record
            record = BillingRecord(
                id=intent.id,
                user_id=user_id,
                record_type="credit_purchase",
                amount=amount_usd,
                credits_amount=credits_to_add,
                credits_balance_after=0,  # Will be updated after confirmation
                stripe_payment_intent_id=intent.id,
                status="pending" if intent.status != "succeeded" else "completed",
            )
            self.db.add(record)
            await self.db.commit()
            
            # If payment succeeded immediately, add credits
            if intent.status == "succeeded":
                await self._add_credits(user_id, credits_to_add)
                record.status = "completed"
                await self.db.commit()
            
            return {
                "id": record.id,
                "credits_added": credits_to_add,
                "amount_paid": amount_usd,
                "status": record.status,
                "stripe_payment_intent_id": intent.id,
                "client_secret": intent.client_secret if hasattr(intent, 'client_secret') else None,
            }
            
        except stripe.error.StripeError as e:
            raise ExternalServiceError(f"Payment processing failed: {str(e)}")
    
    async def handle_stripe_webhook(
        self,
        payload: bytes,
        signature: Optional[str],
    ) -> None:
        """Process Stripe webhook events."""
        settings = get_settings()
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            raise BusinessLogicError("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise BusinessLogicError("Invalid signature")
        
        # Handle events
        if event["type"] == "payment_intent.succeeded":
            await self._handle_payment_success(event["data"]["object"])
        elif event["type"] == "payment_intent.payment_failed":
            await self._handle_payment_failure(event["data"]["object"])
        elif event["type"] == "invoice.payment_succeeded":
            await self._handle_subscription_payment(event["data"]["object"])
    
    async def _handle_payment_success(self, payment_intent: Dict) -> None:
        """Handle successful payment."""
        user_id = payment_intent["metadata"].get("user_id")
        credits = Decimal(payment_intent["metadata"].get("credits", 0))
        
        if user_id and credits > 0:
            await self._add_credits(user_id, credits)
            
            # Update billing record
            result = await self.db.execute(
                select(BillingRecord).where(
                    BillingRecord.stripe_payment_intent_id == payment_intent["id"]
                )
            )
            record = result.scalar_one_or_none()
            if record:
                record.status = "completed"
                await self.db.commit()
    
    async def _handle_payment_failure(self, payment_intent: Dict) -> None:
        """Handle failed payment."""
        result = await self.db.execute(
            select(BillingRecord).where(
                BillingRecord.stripe_payment_intent_id == payment_intent["id"]
            )
        )
        record = result.scalar_one_or_none()
        if record:
            record.status = "failed"
            record.error_message = payment_intent.get("last_payment_error", {}).get("message")
            await self.db.commit()
    
    async def _handle_subscription_payment(self, invoice: Dict) -> None:
        """Handle subscription payment."""
        # Implementation for subscription handling
        pass
    
    async def _add_credits(self, user_id: str, amount: Decimal) -> None:
        """Add credits to user account."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one()
        
        user.credits_balance += amount
        await self.db.commit()
    
    async def consume_credits(
        self,
        user_id: str,
        amount: Decimal,
        job_id: str,
    ) -> bool:
        """Consume credits for job execution."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one()
        
        if user.credits_balance < amount:
            return False
        
        user.credits_balance -= amount
        user.credits_used_total += amount
        
        # Create usage record
        record = BillingRecord(
            user_id=user_id,
            record_type="usage_charge",
            credits_amount=-amount,
            credits_balance_after=user.credits_balance,
            job_id=job_id,
            status="completed",
        )
        self.db.add(record)
        await self.db.commit()
        
        return True
    
    async def get_usage_report(
        self,
        user_id: str,
        period_days: int = 30,
    ) -> Dict[str, Any]:
        """Generate usage report."""
        since = datetime.now(timezone.utc) - timedelta(days=period_days)
        
        # Get records for period
        result = await self.db.execute(
            select(BillingRecord).where(
                BillingRecord.user_id == user_id,
                BillingRecord.created_at >= since,
            )
        )
        records = result.scalars().all()
        
        total_jobs = len([r for r in records if r.record_type == "usage_charge"])
        total_credits = sum(
            abs(r.credits_amount) for r in records if r.record_type == "usage_charge"
        )
        
        return {
            "period_start": since,
            "period_end": datetime.now(timezone.utc),
            "total_jobs": total_jobs,
            "total_pages_scraped": 0,  # Would need to aggregate from jobs
            "total_credits_consumed": total_credits,
            "top_domains": [],  # Would need to aggregate from jobs
            "cost_breakdown": {
                "scraping": total_credits * Decimal("0.01"),
                "ai_processing": 0,
                "storage": 0,
            },
        }
    
    async def get_billing_history(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get billing history."""
        result = await self.db.execute(
            select(BillingRecord).where(
                BillingRecord.user_id == user_id,
            )
            .order_by(BillingRecord.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        records = result.scalars().all()
        
        return [
            {
                "id": r.id,
                "type": r.record_type,
                "amount": float(r.amount) if r.amount else None,
                "credits": float(r.credits_amount),
                "balance_after": float(r.credits_balance_after),
                "status": r.status,
                "created_at": r.created_at.isoformat(),
            }
            for r in records
        ]
    
    async def create_subscription(
        self,
        user_id: str,
        plan_id: str,
    ) -> Dict[str, Any]:
        """Create or update subscription."""
        # Implementation for Stripe subscription
        return {"status": "created", "plan_id": plan_id}
    
    async def cancel_subscription(self, user_id: str) -> None:
        """Cancel subscription."""
        # Implementation for cancellation
        pass