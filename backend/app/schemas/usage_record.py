from pydantic import BaseModel
from typing import Optional
from datetime import date

class UsageRecordBase(BaseModel):
    feature: str
    date: Optional[date]
    count: int

class UsageRecordCreate(UsageRecordBase):
    pass

class UsageRecordOut(UsageRecordBase):
    id: int
    user_id: int
    class Config:
        orm_mode = True
