from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PaymentRecordBase(BaseModel):
    amount: float
    currency: str = "INR"
    status: str = "pending"
    payment_gateway: str = "razorpay"
    payment_id: Optional[str]

class PaymentRecordCreate(PaymentRecordBase):
    pass

class PaymentRecordOut(PaymentRecordBase):
    id: int
    user_id: int
    subscription_id: Optional[int]
    created_at: datetime
    class Config:
        orm_mode = True
