from sqlalchemy import Column, Integer, String, Boolean, Float
from app.database.db import Base

class Plan(Base):
    __tablename__ = "plans"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    price_monthly = Column(Float, nullable=False)
    price_yearly = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    # Feature flags and limits as JSON or columns
