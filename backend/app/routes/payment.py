from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.services.payment_service import create_payment_order, verify_payment
from app.models.user import User

router = APIRouter(prefix="/payment", tags=["Payment"])

@router.post("/create-order")
def create_order(plan_id: int, current_user: User = Depends(), db: Session = Depends(get_db)):
    # Fetch plan price, create payment order with Razorpay
    # Return order_id and payment details
    pass

@router.post("/verify")
def verify(request: Request, db: Session = Depends(get_db)):
    # Handle payment verification callback
    pass

@router.post("/webhook")
def webhook(request: Request, db: Session = Depends(get_db)):
    # Securely handle Razorpay/Stripe webhook
    pass
