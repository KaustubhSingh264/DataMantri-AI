from pydantic import BaseModel
from typing import Optional

class PlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    price_monthly: float
    price_yearly: float
    is_active: Optional[bool] = True

class PlanCreate(PlanBase):
    pass

class PlanOut(PlanBase):
    id: int
    class Config:
        orm_mode = True
