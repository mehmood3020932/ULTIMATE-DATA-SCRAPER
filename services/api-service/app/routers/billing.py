# services/api-service/app/routers/billing.py
# Billing & Credits Endpoints

from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_current_user, get_db_session
from app.models.schemas import (
    CreditPurchaseRequest,
    CreditPurchaseResponse,
    UsageReport,
    UserResponse,
)
from app.services.billing_service import BillingService

router = APIRouter()


@router.get("/credits/balance")
async def get_credits_balance(
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Get current credit balance.
    """
    return {
        "balance": current_user.credits_balance,
        "currency": "USD",
        "subscription_tier": current_user.subscription_tier,
    }


@router.post("/credits/purchase", response_model=CreditPurchaseResponse, status_code=status.HTTP_201_CREATED)
async def purchase_credits(
    purchase_data: CreditPurchaseRequest,
    request: Request,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
):
    """
    Purchase credits using Stripe.
    """
    billing_service = BillingService(db)
    
    # Get client IP for fraud detection
    client_ip = request.client.host if request.client else None
    
    result = await billing_service.purchase_credits(
        user_id=current_user.id,
        amount_usd=purchase_data.amount_usd,
        payment_method_id=purchase_data.payment_method_id,
        client_ip=client_ip,
    )
    
    return result


@router.post("/webhooks/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
):
    """
    Handle Stripe webhooks for payment events.
    """
    payload = await request.body()
    
    billing_service = BillingService(db)
    await billing_service.handle_stripe_webhook(payload, stripe_signature)
    
    return {"status": "processed"}


@router.get("/usage", response_model=UsageReport)
async def get_usage_report(
    period_days: int = 30,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get usage report for the specified period.
    """
    billing_service = BillingService(db)
    report = await billing_service.get_usage_report(
        user_id=current_user.id,
        period_days=period_days,
    )
    return report


@router.get("/history")
async def get_billing_history(
    page: int = 1,
    page_size: int = 20,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get billing history.
    """
    billing_service = BillingService(db)
    history = await billing_service.get_billing_history(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    return history


@router.get("/plans")
async def get_subscription_plans():
    """
    Get available subscription plans.
    """
    return {
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "price_monthly": 0,
                "credits_included": 100,
                "features": ["Basic scraping", "Standard support"],
            },
            {
                "id": "starter",
                "name": "Starter",
                "price_monthly": 49,
                "credits_included": 1000,
                "features": ["Advanced AI", "Priority queue", "Email support"],
            },
            {
                "id": "professional",
                "name": "Professional",
                "price_monthly": 199,
                "credits_included": 5000,
                "features": ["All AI models", "API access", "Priority support", "Custom schemas"],
            },
            {
                "id": "enterprise",
                "name": "Enterprise",
                "price_monthly": None,
                "credits_included": None,
                "features": ["Unlimited", "Dedicated infrastructure", "SLA", "Custom contracts"],
            },
        ]
    }


@router.post("/subscriptions", status_code=status.HTTP_201_CREATED)
async def create_subscription(
    plan_id: str,
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Create or update subscription.
    """
    billing_service = BillingService(db)
    subscription = await billing_service.create_subscription(
        user_id=current_user.id,
        plan_id=plan_id,
    )
    return subscription


@router.delete("/subscriptions", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_subscription(
    current_user: UserResponse = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Cancel subscription at period end.
    """
    billing_service = BillingService(db)
    await billing_service.cancel_subscription(current_user.id)
    return None