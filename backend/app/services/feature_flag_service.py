# Feature flag logic for premium/future features
from sqlalchemy.orm import Session
from app.models.plan import Plan

def is_feature_enabled(plan: Plan, feature: str) -> bool:
    # Extend this logic for future feature flags
    if plan.name == 'Premium':
        return True
    # Add more advanced logic as needed
    return False
