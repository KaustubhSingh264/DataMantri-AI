from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, Numeric, String, UniqueConstraint
from sqlalchemy.sql import func

from app.database.db import Base


class PlanType(Base):
    __tablename__ = "plan_types"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    price_monthly_paise = Column(Integer, nullable=False, default=0)
    price_yearly_paise = Column(Integer, nullable=False, default=0)
    currency = Column(String, nullable=False, default="INR")
    limits_json = Column(JSON, nullable=False, default=dict)
    feature_flags_json = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan_code = Column(String, nullable=False, default="free")
    status = Column(String, nullable=False, default="active")
    interval = Column(String, nullable=False, default="monthly")
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, nullable=False, default=False)
    provider = Column(String, nullable=False, default="razorpay")
    provider_subscription_id = Column(String, nullable=True)
    grace_period_end = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class FeatureUsage(Base):
    __tablename__ = "feature_usage"
    __table_args__ = (
        UniqueConstraint("user_id", "feature", "period_key", name="uq_feature_usage_user_feature_period"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    feature = Column(String, nullable=False, index=True)
    period = Column(String, nullable=False, default="daily")
    period_key = Column(String, nullable=False, index=True)
    used = Column(Integer, nullable=False, default=0)
    limit = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class BillingRecord(Base):
    __tablename__ = "billing_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan_code = Column(String, nullable=False)
    interval = Column(String, nullable=False, default="monthly")
    amount_paise = Column(Integer, nullable=False)
    currency = Column(String, nullable=False, default="INR")
    status = Column(String, nullable=False, default="created")
    provider = Column(String, nullable=False, default="razorpay")
    provider_order_id = Column(String, nullable=True, index=True)
    provider_payment_id = Column(String, nullable=True)
    provider_signature = Column(String, nullable=True)
    receipt = Column(String, nullable=True)
    meta_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PaymentRecord(Base):
    __tablename__ = "payment_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    billing_record_id = Column(Integer, ForeignKey("billing_records.id"), nullable=True)
    provider = Column(String, nullable=False, default="razorpay")
    event_type = Column(String, nullable=False)
    provider_payment_id = Column(String, nullable=True, index=True)
    provider_order_id = Column(String, nullable=True, index=True)
    amount_paise = Column(Integer, nullable=True)
    currency = Column(String, nullable=False, default="INR")
    status = Column(String, nullable=False, default="received")
    payload_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
