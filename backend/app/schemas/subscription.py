from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SubscriptionBase(BaseModel):
    plan_id: int
    status: Optional[str] = "active"
    auto_renew: Optional[bool] = True

class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionOut(SubscriptionBase):
    id: int
    user_id: int
    start_date: datetime
    end_date: Optional[datetime]
    payment_id: Optional[str]
    class Config:
        orm_mode = True
