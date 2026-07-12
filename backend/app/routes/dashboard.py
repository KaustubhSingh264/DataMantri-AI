from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.user import User
from app.services.subscription_service import get_user_subscription, get_plan_limits, get_usage

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/subscription-summary")
def subscription_summary(current_user: User = Depends(), db: Session = Depends(get_db)):
    sub = get_user_subscription(db, current_user.id)
    plan = sub.plan.name if sub else 'Free'
    limits = get_plan_limits(plan)
    usage = {f: get_usage(db, current_user.id, f) for f in limits.keys()}
    return {
        "plan": plan,
        "limits": limits,
        "usage": usage,
        "subscription": sub
    }
