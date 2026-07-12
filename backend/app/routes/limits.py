from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.user import User
from app.services.subscription_service import get_user_subscription, get_plan_limits

router = APIRouter(prefix="/limits", tags=["Limits"])

@router.get("/my")
def my_limits(current_user: User = Depends(), db: Session = Depends(get_db)):
    sub = get_user_subscription(db, current_user.id)
    plan = sub.plan.name if sub else 'Free'
    limits = get_plan_limits(plan)
    return limits
