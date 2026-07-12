from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.services.billing_service import get_billing_history
from app.models.user import User
from typing import List
from app.schemas.billing_history import BillingHistoryOut

router = APIRouter(prefix="/billing", tags=["Billing"])

@router.get("/history", response_model=List[BillingHistoryOut])
def billing_history(current_user: User = Depends(), db: Session = Depends(get_db)):
    return get_billing_history(db, current_user.id)
