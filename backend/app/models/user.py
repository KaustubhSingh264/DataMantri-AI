from sqlalchemy import Boolean, Column, DateTime, Integer, String, ForeignKey
from app.database.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, nullable=True, index=True)
    password = Column(String)
    plan = Column(String, nullable=False, default="trial")
    qa_queries_used = Column(Integer, nullable=False, default=0)
    trial_start_date = Column(DateTime(timezone=True), nullable=True)
    trial_end_date = Column(DateTime(timezone=True), nullable=True)
    subscription_end_date = Column(DateTime(timezone=True), nullable=True)
    razorpay_order_id = Column(String, nullable=True)
    reset_token = Column(String, nullable=True)
    reset_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    reset_otp_attempts = Column(Integer, nullable=False, default=0)
    reset_otp_verified = Column(Boolean, nullable=False, default=False)
    is_admin = Column(Boolean, nullable=False, default=False)
    email_verified = Column(Boolean, nullable=False, default=True)
    #verification_token = Column(String, nullable=True)
    # Language preferences - i18n support
    preferred_language = Column(String, nullable=False, default="en")  # en, hi, hinglish
    latest_upload_id = Column(Integer, ForeignKey("upload_history.id"), nullable=True)  # Quick restore
