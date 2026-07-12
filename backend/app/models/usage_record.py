from sqlalchemy import Column, Integer, String, Date, ForeignKey
from app.database.db import Base
import datetime

class UsageRecord(Base):
    __tablename__ = "usage_records"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    feature = Column(String, nullable=False)  # e.g., 'csv_upload', 'chatbot', 'voice', 'report_download'
    date = Column(Date, default=datetime.date.today)
    count = Column(Integer, default=0)
