# services/billing-service/app/models.py

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, Numeric, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class BillingRecord(Base):
    __tablename__ = "billing_records"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    record_type = Column(String(50))  # credit_purchase, usage_charge, refund
    amount = Column(Numeric(10, 2))
    currency = Column(String(3), default="USD")
    credits_amount = Column(Numeric(10, 2))
    credits_balance_after = Column(Numeric(15, 2))
    job_id = Column(String(36))
    stripe_payment_intent_id = Column(String(100))
    stripe_invoice_id = Column(String(100))
    status = Column(String(50), default="pending")
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    stripe_subscription_id = Column(String(100), unique=True)
    stripe_customer_id = Column(String(100))
    plan_id = Column(String(50))
    status = Column(String(50))
    current_period_start = Column(DateTime(timezone=True))
    current_period_end = Column(DateTime(timezone=True))
    cancel_at_period_end = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))