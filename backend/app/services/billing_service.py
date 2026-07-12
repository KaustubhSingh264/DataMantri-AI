from sqlalchemy.orm import Session
from app.models.billing_history import BillingHistory

def get_billing_history(db: Session, user_id: int):
    return db.query(BillingHistory).filter(BillingHistory.user_id == user_id).order_by(BillingHistory.created_at.desc()).all()
