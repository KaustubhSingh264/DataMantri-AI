from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.subscription_service import get_user_subscription, get_plan_limits, get_usage
from app.database.db import get_db

class SubscriptionLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only check for protected endpoints
        path = request.url.path
        protected_features = {
            '/upload': 'csv_upload',
            '/ask': 'chatbot',
            '/voice-assistant/ask': 'voice',
            '/generate-report': 'report_download',
            '/recommend': 'recommendation',
        }
        feature = None
        for k, v in protected_features.items():
            if path.startswith(k):
                feature = v
                break
        if feature:
            db = get_db()
            user = getattr(request.state, 'user', None)
            if user:
                sub = get_user_subscription(db, user.id)
                plan = sub.plan.name if sub else 'Free'
                limits = get_plan_limits(plan)
                usage = get_usage(db, user.id, feature)
                if limits[feature] is not None and usage >= limits[feature]:
                    raise HTTPException(status_code=429, detail=f"You have reached your daily limit for {feature}. Upgrade to Premium for unlimited access.")
        response = await call_next(request)
        return response
