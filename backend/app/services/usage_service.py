from sqlalchemy.orm import Session
from app.models.usage_record import UsageRecord
from datetime import date

def get_today_usage(db: Session, user_id: int, feature: str):
    today = date.today()
    usage = db.query(UsageRecord).filter(UsageRecord.user_id == user_id, UsageRecord.feature == feature, UsageRecord.date == today).first()
    return usage.count if usage else 0

def increment_usage(db: Session, user_id: int, feature: str):
    today = date.today()
    usage = db.query(UsageRecord).filter(UsageRecord.user_id == user_id, UsageRecord.feature == feature, UsageRecord.date == today).first()
    if usage:
        usage.count += 1
    else:
        usage = UsageRecord(user_id=user_id, feature=feature, date=today, count=1)
        db.add(usage)
    db.commit()
    return usage
