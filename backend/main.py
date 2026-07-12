from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text
import os
import logging

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 🔹 Database
from app.database.db import Base, SessionLocal, engine

from app.models.user import User
from app.models.upload_history import UploadHistory
from app.models.signup_otp import SignupOtp
from app.models.support_ticket import SupportTicket
from app.models.subscription import BillingRecord, FeatureUsage, PaymentRecord, PlanType, Subscription
from app.services.subscription_service import seed_default_plans

# 🔹 Routes
from app.routes import upload, auth, voice_assistant, language, restore

# 🔥 Create tables (runs once on startup)
Base.metadata.create_all(bind=engine)
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

def run_lightweight_migrations():
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    with engine.begin() as connection:
        if "plan" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN plan VARCHAR NOT NULL DEFAULT 'trial'"))
        if "username" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR"))
        if "qa_queries_used" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN qa_queries_used INTEGER NOT NULL DEFAULT 0"))
        if "trial_start_date" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN trial_start_date TIMESTAMP"))
        if "trial_end_date" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN trial_end_date TIMESTAMP"))
        if "subscription_end_date" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN subscription_end_date TIMESTAMP"))
        if "razorpay_order_id" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN razorpay_order_id VARCHAR"))
        if "reset_token" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN reset_token VARCHAR"))
        if "reset_token_expires_at" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN reset_token_expires_at TIMESTAMP"))
        if "reset_otp_attempts" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN reset_otp_attempts INTEGER NOT NULL DEFAULT 0"))
        if "reset_otp_verified" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN reset_otp_verified BOOLEAN NOT NULL DEFAULT FALSE"))
        if "is_admin" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE"))
        if "email_verified" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT TRUE"))
        if "preferred_language" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN preferred_language VARCHAR NOT NULL DEFAULT 'en'"))
        if "latest_upload_id" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN latest_upload_id INTEGER"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username) WHERE username IS NOT NULL"))

    if "support_tickets" in inspector.get_table_names():
        support_columns = {column["name"] for column in inspector.get_columns("support_tickets")}
        with engine.begin() as connection:
            if "email_sent" not in support_columns:
                connection.execute(text("ALTER TABLE support_tickets ADD COLUMN email_sent BOOLEAN NOT NULL DEFAULT FALSE"))
            if "email_sent_at" not in support_columns:
                connection.execute(text("ALTER TABLE support_tickets ADD COLUMN email_sent_at TIMESTAMP"))
            if "email_error" not in support_columns:
                connection.execute(text("ALTER TABLE support_tickets ADD COLUMN email_error TEXT"))

    if "upload_history" in inspector.get_table_names():
        upload_columns = {column["name"] for column in inspector.get_columns("upload_history")}
        with engine.begin() as connection:
            if "original_filename" not in upload_columns:
                connection.execute(text("ALTER TABLE upload_history ADD COLUMN original_filename VARCHAR"))
            if "file_type" not in upload_columns:
                connection.execute(text("ALTER TABLE upload_history ADD COLUMN file_type VARCHAR"))
            if "row_count" not in upload_columns:
                connection.execute(text("ALTER TABLE upload_history ADD COLUMN row_count INTEGER"))
            if "column_count" not in upload_columns:
                connection.execute(text("ALTER TABLE upload_history ADD COLUMN column_count INTEGER"))
            if "validation_report" not in upload_columns:
                connection.execute(text("ALTER TABLE upload_history ADD COLUMN validation_report JSON"))

    if "signup_otps" not in inspector.get_table_names():
        SignupOtp.__table__.create(bind=engine, checkfirst=True)


run_lightweight_migrations()
with SessionLocal() as db:
    seed_default_plans(db)

# 🔹 Create app FIRST
app = FastAPI()

# 🔹 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔹 Include routers (AFTER app creation)
app.include_router(upload.router)
app.include_router(auth.router)
app.include_router(voice_assistant.router)
app.include_router(language.router)
app.include_router(restore.router)
auth.log_email_configuration()

os.makedirs("static/audio", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 🔹 Test routes
@app.get("/")
def home():
    return {"message": "AutoInsight AI Running 🚀"}

@app.get("/test")
def test():
    return {"status": "working"}
