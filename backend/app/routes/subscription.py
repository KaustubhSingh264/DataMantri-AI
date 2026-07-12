from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.services.subscription_service import *
from app.schemas.subscription import SubscriptionOut
from app.schemas.plan import PlanOut
from app.models.plan import Plan
from app.models.subscription import Subscription
from app.models.user import User
from typing import List

router = APIRouter(prefix="/subscription", tags=["Subscription"])

@router.get("/plans", response_model=List[PlanOut])
def get_plans(db: Session = Depends(get_db)):
    return db.query(Plan).filter(Plan.is_active == True).all()

@router.get("/my", response_model=SubscriptionOut)
def get_my_subscription(current_user: User = Depends(), db: Session = Depends(get_db)):
    sub = get_user_subscription(db, current_user.id)
    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription")
    return sub

@router.post("/upgrade")
def upgrade_plan(plan_id: int, current_user: User = Depends(), db: Session = Depends(get_db)):
    # Payment flow handled separately
    sub = create_subscription(db, current_user.id, plan_id)
    return {"success": True, "subscription_id": sub.id}

@router.post("/cancel")
def cancel(current_user: User = Depends(), db: Session = Depends(get_db)):
    sub = cancel_subscription(db, current_user.id)
    return {"success": True}
