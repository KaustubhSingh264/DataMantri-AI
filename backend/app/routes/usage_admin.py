from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.services.usage_reset_service import reset_daily_usage

router = APIRouter(prefix="/usage-admin", tags=["UsageAdmin"])

@router.post("/reset-daily")
def reset_daily(db: Session = Depends(get_db)):
    reset_daily_usage(db)
    return {"success": True}
