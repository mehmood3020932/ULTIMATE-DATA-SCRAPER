# services/billing-service/app/routers/billing.py

from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.stripe_service import StripeService

router = APIRouter()


async def get_db():
    # Database session dependency
    pass


@router.post("/credits/purchase")
async def purchase_credits(
    amount: Decimal,
    payment_method_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Purchase credits via Stripe."""
    stripe_service = StripeService(db)
    result = await stripe_service.create_payment_intent(amount, payment_method_id)
    return result


@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db),
):
    """Handle Stripe webhooks."""
    payload = await request.body()
    stripe_service = StripeService(db)
    await stripe_service.handle_webhook(payload, stripe_signature)
    return {"status": "processed"}


@router.get("/plans")
async def get_plans():
    """Get available subscription plans."""
    return {
        "plans": [
            {"id": "free", "name": "Free", "price": 0, "credits": 100},
            {"id": "starter", "name": "Starter", "price": 49, "credits": 1000},
            {"id": "professional", "name": "Professional", "price": 199, "credits": 5000},
            {"id": "enterprise", "name": "Enterprise", "price": None, "credits": None},
        ]
    }