from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from app.database.db import Base
import datetime

class BillingHistory(Base):
    __tablename__ = "billing_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    amount = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    status = Column(String, default="success")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    payment_id = Column(String)
