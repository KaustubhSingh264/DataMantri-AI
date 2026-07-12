from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.services.plan_service import get_active_plans
from app.schemas.plan import PlanOut
from typing import List

router = APIRouter(prefix="/plan", tags=["Plan"])

@router.get("/all", response_model=List[PlanOut])
def all_plans(db: Session = Depends(get_db)):
    return get_active_plans(db)
