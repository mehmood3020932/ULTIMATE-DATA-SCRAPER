# services/billing-service/app/services/stripe_service.py

import stripe
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_payment_intent(self, amount: Decimal, payment_method_id: str = None):
        """Create Stripe payment intent."""
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to cents
            currency="usd",
            payment_method=payment_method_id,
            confirm=payment_method_id is not None,
        )
        return {
            "client_secret": intent.client_secret,
            "status": intent.status,
        }
    
    async def handle_webhook(self, payload: bytes, signature: str):
        """Process Stripe webhook."""
        event = stripe.Webhook.construct_event(
            payload, signature, settings.STRIPE_WEBHOOK_SECRET
        )
        
        if event["type"] == "payment_intent.succeeded":
            await self._handle_payment_success(event["data"]["object"])
        elif event["type"] == "payment_intent.payment_failed":
            await self._handle_payment_failure(event["data"]["object"])
        
        return True
    
    async def _handle_payment_success(self, payment_intent: dict):
        """Handle successful payment."""
        # Update user credits, etc.
        pass
    
    async def _handle_payment_failure(self, payment_intent: dict):
        """Handle failed payment."""
        pass