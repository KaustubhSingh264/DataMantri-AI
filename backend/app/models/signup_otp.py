from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func
from app.database.db import Base


class SignupOtp(Base):
    __tablename__ = "signup_otps"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    otp_hash = Column(String, nullable=False)
    otp_expiry = Column(DateTime(timezone=True), nullable=False)
    attempts = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
