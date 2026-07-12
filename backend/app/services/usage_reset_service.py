# Daily/monthly usage reset logic
from sqlalchemy.orm import Session
from app.models.usage_record import UsageRecord
from datetime import date

def reset_daily_usage(db: Session):
    today = date.today()
    db.query(UsageRecord).filter(UsageRecord.date != today).delete()
    db.commit()

# For monthly reset, extend as needed
