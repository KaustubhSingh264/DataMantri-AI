from sqlalchemy.orm import Session
from app.models.plan import Plan

def get_active_plans(db: Session):
    return db.query(Plan).filter(Plan.is_active == True).all()
