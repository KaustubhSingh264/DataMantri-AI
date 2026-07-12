from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.subscription import BillingRecord, FeatureUsage, PlanType, Subscription


TRIAL_DAYS = 0
SUBSCRIPTION_DAYS = 30
BASIC_QUERY_LIMIT = 4
PREMIUM_PRICE_INR = 100
PREMIUM_PRICE_PAISE = PREMIUM_PRICE_INR * 100
PREMIUM_YEARLY_PRICE_INR = 999
PREMIUM_YEARLY_PRICE_PAISE = PREMIUM_YEARLY_PRICE_INR * 100
GRACE_DAYS = 3

PLAN_FREE = "free"
PLAN_PREMIUM = "premium"
LEGACY_FREE_PLANS = {"basic", "trial", "free"}
FULL_ACCESS_PLANS = {PLAN_PREMIUM}

FEATURE_UPLOAD = "csv_upload"
FEATURE_CHAT = "chatbot_query"
FEATURE_VOICE = "voice_advisor"
FEATURE_REPORT = "report_download"
FEATURE_CLEAN = "auto_clean"
FEATURE_RECOMMENDATION = "recommendations"
FEATURE_HISTORY = "history_storage"

FEATURE_LABELS = {
    FEATURE_UPLOAD: "CSV uploads",
    FEATURE_CHAT: "AI chatbot queries",
    FEATURE_VOICE: "Mitra voice interactions",
    FEATURE_REPORT: "Report downloads",
    FEATURE_CLEAN: "Auto-clean runs",
    FEATURE_RECOMMENDATION: "AI recommendations",
    FEATURE_HISTORY: "Stored history items",
}

DEFAULT_PLAN_CONFIG = {
    PLAN_FREE: {
        "name": "Free",
        "monthly": 0,
        "yearly": 0,
        "limits": {
            FEATURE_UPLOAD: {"limit": 4, "period": "daily"},
            FEATURE_CHAT: {"limit": 4, "period": "daily"},
            FEATURE_VOICE: {"limit": 4, "period": "daily"},
            FEATURE_REPORT: {"limit": 2, "period": "monthly"},
            FEATURE_CLEAN: {"limit": 2, "period": "daily"},
            FEATURE_RECOMMENDATION: {"limit": 6, "period": "daily"},
            FEATURE_HISTORY: {"limit": 10, "period": "lifetime"},
        },
        "flags": {"advanced_ai": False, "priority_processing": False},
    },
    PLAN_PREMIUM: {
        "name": "Premium",
        "monthly": PREMIUM_PRICE_PAISE,
        "yearly": PREMIUM_YEARLY_PRICE_PAISE,
        "limits": {
            FEATURE_UPLOAD: {"limit": None, "period": "daily"},
            FEATURE_CHAT: {"limit": None, "period": "daily"},
            FEATURE_VOICE: {"limit": None, "period": "daily"},
            FEATURE_REPORT: {"limit": None, "period": "monthly"},
            FEATURE_CLEAN: {"limit": None, "period": "daily"},
            FEATURE_RECOMMENDATION: {"limit": None, "period": "daily"},
            FEATURE_HISTORY: {"limit": None, "period": "lifetime"},
        },
        "flags": {"advanced_ai": True, "priority_processing": True, "future_premium_features": True},
    },
}


def utc_now():
    return datetime.now(timezone.utc)


def ensure_aware(value):
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def normalize_plan(plan: str | None):
    plan = (plan or PLAN_FREE).lower()
    return PLAN_PREMIUM if plan == PLAN_PREMIUM else PLAN_FREE


def period_key(period: str, now: datetime | None = None):
    now = now or utc_now()
    if period == "monthly":
        return now.strftime("%Y-%m")
    if period == "lifetime":
        return "lifetime"
    return now.strftime("%Y-%m-%d")


def seed_default_plans(db: Session):
    for code, config in DEFAULT_PLAN_CONFIG.items():
        plan = db.query(PlanType).filter(PlanType.code == code).first()
        if not plan:
            plan = PlanType(code=code, name=config["name"])
        plan.name = config["name"]
        plan.price_monthly_paise = config["monthly"]
        plan.price_yearly_paise = config["yearly"]
        plan.currency = "INR"
        plan.limits_json = config["limits"]
        plan.feature_flags_json = config["flags"]
        plan.is_active = True
        db.add(plan)
    db.commit()


def get_plan_config(plan_code: str | None):
    return DEFAULT_PLAN_CONFIG.get(normalize_plan(plan_code), DEFAULT_PLAN_CONFIG[PLAN_FREE])


def get_feature_limit(plan_code: str | None, feature: str):
    limits = get_plan_config(plan_code)["limits"]
    return limits.get(feature, {"limit": None, "period": "daily"})


def start_trial(user):
    user.plan = PLAN_FREE
    user.trial_start_date = None
    user.trial_end_date = None
    user.subscription_end_date = None
    return user


def activate_premium(user, interval: str = "monthly"):
    now = utc_now()
    days = 365 if interval == "yearly" else SUBSCRIPTION_DAYS
    user.plan = PLAN_PREMIUM
    user.subscription_end_date = now + timedelta(days=days)
    return user


def get_or_create_subscription(user, db: Session, interval: str = "monthly"):
    subscription = (
        db.query(Subscription)
        .filter(Subscription.user_id == user.id)
        .order_by(Subscription.id.desc())
        .first()
    )
    if not subscription:
        subscription = Subscription(
            user_id=user.id,
            plan_code=normalize_plan(user.plan),
            status="active",
            interval=interval,
            current_period_start=utc_now(),
            current_period_end=user.subscription_end_date,
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
    return subscription


def refresh_user_plan(user, db: Session | None = None):
    now = utc_now()
    changed = False
    plan = normalize_plan(user.plan)

    if user.plan != plan:
        user.plan = plan
        changed = True

    subscription_end = ensure_aware(user.subscription_end_date)
    if plan == PLAN_PREMIUM and subscription_end and now > subscription_end:
        grace_end = subscription_end + timedelta(days=GRACE_DAYS)
        if now > grace_end:
            user.plan = PLAN_FREE
            changed = True

    if db is not None:
        subscription = get_or_create_subscription(user, db)
        if subscription.plan_code != normalize_plan(user.plan):
            subscription.plan_code = normalize_plan(user.plan)
            subscription.status = "active"
            changed = True
        if normalize_plan(user.plan) == PLAN_PREMIUM:
            subscription.current_period_end = user.subscription_end_date
        elif subscription.plan_code == PLAN_FREE:
            subscription.current_period_end = None
        if changed:
            db.add(user)
            db.add(subscription)
            db.commit()
            db.refresh(user)
    return user


def has_full_access(user):
    return normalize_plan(user.plan) in FULL_ACCESS_PLANS


def is_premium(user):
    return has_full_access(user)


def days_until(value):
    value = ensure_aware(value)
    if value is None:
        return None
    seconds = (value - utc_now()).total_seconds()
    return max(0, int((seconds + 86399) // 86400))


def get_usage_record(db: Session, user_id: int, feature: str, limit_config: dict[str, Any]):
    period = limit_config.get("period", "daily")
    key = period_key(period)
    usage = (
        db.query(FeatureUsage)
        .filter(FeatureUsage.user_id == user_id, FeatureUsage.feature == feature, FeatureUsage.period_key == key)
        .first()
    )
    if not usage:
        usage = FeatureUsage(
            user_id=user_id,
            feature=feature,
            period=period,
            period_key=key,
            used=0,
            limit=limit_config.get("limit"),
        )
        db.add(usage)
        db.commit()
        db.refresh(usage)
    return usage


def get_usage_snapshot(user, db: Session):
    plan = normalize_plan(user.plan)
    snapshot = {}
    for feature, label in FEATURE_LABELS.items():
        config = get_feature_limit(plan, feature)
        usage = get_usage_record(db, user.id, feature, config)
        limit = None if has_full_access(user) else config.get("limit")
        snapshot[feature] = {
            "label": label,
            "used": usage.used,
            "limit": limit,
            "remaining": None if limit is None else max(0, limit - usage.used),
            "period": config.get("period", "daily"),
            "unlimited": limit is None,
        }
    return snapshot


def assert_usage_allowed(user, db: Session, feature: str):
    refresh_user_plan(user, db)
    config = get_feature_limit(user.plan, feature)
    usage = get_usage_record(db, user.id, feature, config)
    limit = None if has_full_access(user) else config.get("limit")
    if limit is not None and usage.used >= limit:
        raise HTTPException(
            status_code=429,
            detail={
                "message": f"You have used {usage.used}/{limit} {FEATURE_LABELS.get(feature, feature)} for this {usage.period}. Upgrade to Premium for unlimited access.",
                "feature": feature,
                "used": usage.used,
                "limit": limit,
                "period": usage.period,
                "upgrade_required": True,
            },
        )
    return usage, limit


def record_feature_usage(user, db: Session, feature: str, amount: int = 1):
    config = get_feature_limit(user.plan, feature)
    usage = get_usage_record(db, user.id, feature, config)
    usage.used = (usage.used or 0) + amount
    usage.limit = None if has_full_access(user) else config.get("limit")
    db.add(usage)
    db.commit()
    db.refresh(usage)
    return usage


def consume_feature(user, db: Session, feature: str, amount: int = 1):
    usage, _ = assert_usage_allowed(user, db, feature)
    usage.used = (usage.used or 0) + amount
    db.add(usage)
    db.commit()
    db.refresh(usage)
    return usage


def create_billing_record(user, db: Session, interval: str, order: dict):
    interval = "yearly" if interval == "yearly" else "monthly"
    amount = PREMIUM_YEARLY_PRICE_PAISE if interval == "yearly" else PREMIUM_PRICE_PAISE
    billing = BillingRecord(
        user_id=user.id,
        plan_code=PLAN_PREMIUM,
        interval=interval,
        amount_paise=amount,
        currency="INR",
        status="created",
        provider_order_id=order.get("id"),
        receipt=order.get("receipt"),
        meta_json=order,
    )
    db.add(billing)
    db.commit()
    db.refresh(billing)
    return billing


def get_billing_history(user, db: Session):
    records = (
        db.query(BillingRecord)
        .filter(BillingRecord.user_id == user.id)
        .order_by(BillingRecord.created_at.desc())
        .all()
    )
    return [
        {
            "id": record.id,
            "plan_code": record.plan_code,
            "interval": record.interval,
            "amount": record.amount_paise / 100,
            "amount_paise": record.amount_paise,
            "currency": record.currency,
            "status": record.status,
            "provider_order_id": record.provider_order_id,
            "provider_payment_id": record.provider_payment_id,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }
        for record in records
    ]
