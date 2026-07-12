from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.user import User
from app.services.subscription_service import get_user_subscription
from app.services.feature_flag_service import is_feature_enabled

router = APIRouter(prefix="/feature-flag", tags=["FeatureFlag"])

@router.get("/is-enabled")
def is_enabled(feature: str, current_user: User = Depends(), db: Session = Depends(get_db)):
    sub = get_user_subscription(db, current_user.id)
    plan = sub.plan if sub else None
    if not plan:
        return {"enabled": False}
    return {"enabled": is_feature_enabled(plan, feature)}
