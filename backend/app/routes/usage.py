from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.services.usage_service import get_today_usage, increment_usage
from app.models.user import User
from typing import Dict

router = APIRouter(prefix="/usage", tags=["Usage"])

@router.get("/my", response_model=Dict[str, int])
def get_my_usage(current_user: User = Depends(), db: Session = Depends(get_db)):
    features = ['csv_upload', 'chatbot', 'voice', 'report_download', 'recommendation']
    usage = {f: get_today_usage(db, current_user.id, f) for f in features}
    return usage
