from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BillingHistoryBase(BaseModel):
    amount: float
    currency: str = "INR"
    status: str = "success"
    payment_id: Optional[str]

class BillingHistoryCreate(BillingHistoryBase):
    pass

class BillingHistoryOut(BillingHistoryBase):
    id: int
    user_id: int
    subscription_id: Optional[int]
    created_at: datetime
    class Config:
        orm_mode = True
