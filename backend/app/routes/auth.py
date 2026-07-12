from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
import base64
import hashlib
import hmac
import html
import json
import logging
import os
import re
import secrets
import smtplib
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import timedelta
from collections import defaultdict, deque
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.database.db import SessionLocal
from app.models.user import User
from app.models.signup_otp import SignupOtp
from app.models.upload_history import UploadHistory
from app.models.support_ticket import SupportTicket
from app.models.subscription import BillingRecord, PaymentRecord, Subscription
import requests

try:
    from email_validator import validate_email, EmailNotValidError
except ModuleNotFoundError:
    validate_email = None

    class EmailNotValidError(ValueError):
        pass
from app.services.subscription_service import (
    BASIC_QUERY_LIMIT,
    FEATURE_CHAT,
    FEATURE_CLEAN,
    FEATURE_LABELS,
    FEATURE_REPORT,
    FEATURE_UPLOAD,
    FEATURE_VOICE,
    PLAN_FREE,
    PLAN_PREMIUM,
    PREMIUM_YEARLY_PRICE_INR,
    PREMIUM_YEARLY_PRICE_PAISE,
    PREMIUM_PRICE_INR,
    PREMIUM_PRICE_PAISE,
    activate_premium,
    assert_usage_allowed,
    create_billing_record,
    days_until,
    get_billing_history,
    get_or_create_subscription,
    get_usage_snapshot,
    has_full_access,
    normalize_plan,
    record_feature_usage,
    refresh_user_plan,
    start_trial,
    utc_now,
)
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_token,
    decode_token,
)

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger("uvicorn.error")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")

SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "")
DEFAULT_ADMIN_EMAILS = SUPPORT_EMAIL
ADMIN_EMAILS = {email.strip().lower() for email in os.getenv("ADMIN_EMAILS", DEFAULT_ADMIN_EMAILS).split(",") if email.strip()}
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USERNAME or SUPPORT_EMAIL)
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "smtp").lower()
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
RESET_TOKEN_EXPIRE_MINUTES = int(os.getenv("RESET_TOKEN_EXPIRE_MINUTES", "30"))
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_][a-zA-Z0-9_.-]{2,31}$")
AUTH_RATE_LIMITS = defaultdict(deque)


def log_email_configuration():
    logger.info(
        "Email configuration provider=%s support_email_configured=%s smtp_host=%s smtp_port=%s "
        "smtp_username_configured=%s smtp_password_configured=%s resend_key_configured=%s "
        "sendgrid_key_configured=%s tls=%s ssl=%s",
        EMAIL_PROVIDER,
        bool(SUPPORT_EMAIL),
        SMTP_HOST or "<not configured>",
        SMTP_PORT,
        bool(SMTP_USERNAME),
        bool(SMTP_PASSWORD),
        bool(RESEND_API_KEY),
        bool(SENDGRID_API_KEY),
        SMTP_USE_TLS,
        SMTP_USE_SSL,
    )


class UserCredentials(BaseModel):
    email: str
    password: str
    username: str | None = None


class VerifySignupOtpRequest(BaseModel):
    email: str
    otp: str


class LoginCredentials(BaseModel):
    email: str | None = None
    username: str | None = None
    identifier: str | None = None
    password: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def normalize_email(email: str | None) -> str:
    email = (email or "").strip().lower()
    if not email or not EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Enter a valid email address.")
    return email


def normalize_username(username: str | None) -> str | None:
    username = (username or "").strip().lower()
    if not username:
        return None
    if not USERNAME_RE.match(username):
        raise HTTPException(
            status_code=400,
            detail="Username must be 3-32 characters and use only letters, numbers, dots, dashes, or underscores.",
        )
    return username


def validate_password_strength(password: str):
    if len(password or "") < 8:
        raise HTTPException(status_code=400, detail="Password must contain at least 8 characters.")
    if len(password) > 128:
        raise HTTPException(status_code=400, detail="Password must be 128 characters or fewer.")


def check_rate_limit(bucket: str, identifier: str, limit: int = 8, window_seconds: int = 60):
    now = time.monotonic()
    key = f"{bucket}:{identifier}"
    attempts = AUTH_RATE_LIMITS[key]
    while attempts and now - attempts[0] > window_seconds:
        attempts.popleft()
    if len(attempts) >= limit:
        raise HTTPException(status_code=429, detail="Too many attempts. Please try again shortly.")
    attempts.append(now)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    return email


def get_current_user(email: str = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    refresh_user_plan(user, db)
    return user


def require_admin(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def post_json(url: str, headers: dict, payload: dict):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return 200 <= response.status < 300


def send_email(to_email: str, subject: str, body: str, html_body: str | None = None):
    logger.info("Email send attempt provider=%s to=%s subject=%s", EMAIL_PROVIDER, to_email, subject)
    if EMAIL_PROVIDER == "resend":
        if not RESEND_API_KEY:
            raise RuntimeError("RESEND_API_KEY is not configured.")
        sent = post_json(
                "https://api.resend.com/emails",
                {"Authorization": f"Bearer {RESEND_API_KEY}"},
                {
                    "from": SMTP_FROM,
                    "to": [to_email],
                    "subject": subject,
                    "text": body,
                    "html": html_body or body,
                },
            )
        if not sent:
            raise RuntimeError("Resend rejected the email request.")
        logger.info("Email send success provider=resend to=%s", to_email)
        return True

    if EMAIL_PROVIDER == "sendgrid":
        if not SENDGRID_API_KEY:
            raise RuntimeError("SENDGRID_API_KEY is not configured.")
        sent = post_json(
            "https://api.sendgrid.com/v3/mail/send",
            {"Authorization": f"Bearer {SENDGRID_API_KEY}"},
            {
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": SMTP_FROM},
                "subject": subject,
                "content": [
                    {"type": "text/plain", "value": body},
                    {"type": "text/html", "value": html_body or body},
                ],
            },
        )
        if not sent:
            raise RuntimeError("SendGrid rejected the email request.")
        logger.info("Email send success provider=sendgrid to=%s", to_email)
        return True

    if not SMTP_HOST or not SMTP_USERNAME or not SMTP_PASSWORD:
        raise RuntimeError("SMTP is not configured. Set SMTP_HOST, SMTP_USERNAME, and SMTP_PASSWORD.")

    if html_body:
        email = MIMEMultipart("alternative")
        email.attach(MIMEText(body, "plain"))
        email.attach(MIMEText(html_body, "html"))
    else:
        email = MIMEText(body)
    email["Subject"] = subject
    email["From"] = SMTP_FROM
    email["To"] = to_email

    smtp_class = smtplib.SMTP_SSL if SMTP_USE_SSL else smtplib.SMTP
    logger.info(
        "SMTP connection attempt host=%s port=%s tls=%s ssl=%s username=%s",
        SMTP_HOST,
        SMTP_PORT,
        SMTP_USE_TLS,
        SMTP_USE_SSL,
        SMTP_USERNAME,
    )
    try:
        with smtp_class(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            if not SMTP_USE_SSL and SMTP_USE_TLS:
                server.ehlo()
                server.starttls()
                server.ehlo()
                logger.info("SMTP TLS negotiation successful host=%s port=%s", SMTP_HOST, SMTP_PORT)
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            logger.info("SMTP authentication successful username=%s", SMTP_USERNAME)
            refused = server.sendmail(SMTP_FROM, [to_email], email.as_string())
            if refused:
                raise RuntimeError(f"SMTP refused recipients: {list(refused)}")
    except Exception:
        logger.exception("Email send failure provider=smtp to=%s subject=%s", to_email, subject)
        raise
    logger.info("Email send success provider=smtp to=%s", to_email)
    return True


def build_reset_url(email: str, token: str):
    query = urllib.parse.urlencode({"token": token, "email": email})
    return f"{FRONTEND_URL}/#reset?{query}"


def send_password_reset_email(to_email: str, reset_url: str):
    
    text = (
        "Reset your Data Mantri password\n\n"
        f"Open this secure link to create a new password: {reset_url}\n\n"
        f"This link expires in {RESET_TOKEN_EXPIRE_MINUTES} minutes and can be used only once.\n"
        "If you did not request this, you can ignore this email."
    )
    html = f"""
    <div style="font-family:Arial,sans-serif;line-height:1.55;color:#0f172a">
      <h2>Reset your Data Mantri password</h2>
      <p>Open this secure link to create a new password:</p>
      <p><a href="{reset_url}" style="background:#059669;color:#fff;padding:12px 18px;border-radius:8px;text-decoration:none">Reset password</a></p>
      <p>This link expires in {RESET_TOKEN_EXPIRE_MINUTES} minutes and can be used only once.</p>
      <p>If you did not request this, you can ignore this email.</p>
    </div>
    """
    return send_email(to_email, "Reset your Data Mantri password", text, html)


def send_signup_otp_email(to_email: str, otp: str):
    text = (
        "Verify your Data Mantri email\n\n"
        f"Your signup OTP is: {otp}\n\n"
        "This OTP expires in 10 minutes. If you did not request this, ignore this email."
    )
    html_body = f"""
    <div style="font-family:Arial,sans-serif;line-height:1.55;color:#0f172a">
      <h2>Verify your Data Mantri email</h2>
      <p>Your signup OTP is:</p>
      <p style="font-size:24px;font-weight:700;letter-spacing:4px">{html.escape(otp)}</p>
      <p>This OTP expires in 10 minutes.</p>
    </div>
    """
    return send_email(to_email, "Verify your Data Mantri email", text, html_body)


def send_support_email(ticket: SupportTicket, user: User):
    if not SUPPORT_EMAIL:
        raise RuntimeError("SUPPORT_EMAIL is not configured.")
    user_name = user.username or user.email.split("@")[0]
    created_at = ticket.created_at.isoformat() if ticket.created_at else utc_now().isoformat()
    safe_user_name = html.escape(user_name)
    safe_user_email = html.escape(user.email)
    safe_subject = html.escape(ticket.subject)
    safe_message = html.escape(ticket.message).replace("\n", "<br>")
    body = (
        "New Data Mantri support request\n\n"
        f"Ticket ID: {ticket.id}\n"
        f"Created Date & Time: {created_at}\n"
        f"User Name: {user_name}\n"
        f"User Email: {user.email}\n"
        f"Subject: {ticket.subject}\n\n"
        f"Message:\n{ticket.message}\n"
    )
    html_body = f"""
    <div style="font-family:Arial,sans-serif;line-height:1.55;color:#0f172a">
      <h2>New Data Mantri support request</h2>
      <p><strong>Ticket ID:</strong> {ticket.id}</p>
      <p><strong>Created Date &amp; Time:</strong> {created_at}</p>
      <p><strong>User Name:</strong> {safe_user_name}</p>
      <p><strong>User Email:</strong> {safe_user_email}</p>
      <p><strong>Subject:</strong> {safe_subject}</p>
      <p><strong>Message:</strong></p>
      <p>{safe_message}</p>
    </div>
    """
    return send_email(SUPPORT_EMAIL, f"Data Mantri Support #{ticket.id}: {ticket.subject}", body, html_body)


@router.post("/signup")
def signup(credentials: UserCredentials, db: Session = Depends(get_db)):
    email = normalize_email(credentials.email)
    username = normalize_username(credentials.username)
    if validate_email:
        try:
            validate_email(email, check_deliverability=True)
        except EmailNotValidError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid email address: {str(e)}"
            )
    check_rate_limit("signup", email, limit=5, window_seconds=300)
    validate_password_strength(credentials.password)

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="This email is already registered.")
    if username and db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=409, detail="This username is already taken.")

    otp = f"{secrets.randbelow(1_000_000):06d}"
    pending = db.query(SignupOtp).filter(SignupOtp.email == email).first()
    if not pending:
        pending = SignupOtp(email=email)
    pending.username = username
    pending.password_hash = hash_password(credentials.password)
    pending.otp_hash = hash_password(otp)
    pending.otp_expiry = utc_now() + timedelta(minutes=10)
    pending.attempts = 0
    db.add(pending)
    db.commit()

    sent = True
    try:
        send_signup_otp_email(email, otp)
    except Exception:
        sent = False
        logger.exception("Signup OTP email failed email=%s", email)

    response = {"message": "Verification OTP sent to your email.", "requires_otp": True}
    if not sent and os.getenv("APP_ENV", "development").lower() != "production":
        response["dev_otp"] = otp
        response["message"] = "Verification OTP generated. Email is not configured, so dev_otp is included."
    return response


@router.post("/verify-signup-otp")
def verify_signup_otp(request: VerifySignupOtpRequest, db: Session = Depends(get_db)):
    email = normalize_email(request.email)
    check_rate_limit("verify-signup-otp", email, limit=6, window_seconds=300)
    pending = db.query(SignupOtp).filter(SignupOtp.email == email).first()
    if not pending:
        raise HTTPException(status_code=400, detail="No pending signup found. Please sign up again.")
    if pending.attempts >= 5:
        raise HTTPException(status_code=429, detail="Too many OTP attempts. Please sign up again.")
    if utc_now() > pending.otp_expiry.replace(tzinfo=utc_now().tzinfo):
        db.delete(pending)
        db.commit()
        raise HTTPException(status_code=400, detail="OTP expired. Please sign up again.")
    if not verify_password(request.otp, pending.otp_hash):
        pending.attempts = (pending.attempts or 0) + 1
        db.add(pending)
        db.commit()
        raise HTTPException(status_code=400, detail=f"Invalid OTP. {max(0, 5 - pending.attempts)} attempts left.")
    if db.query(User).filter(User.email == email).first():
        db.delete(pending)
        db.commit()
        raise HTTPException(status_code=409, detail="This email is already registered.")
    if pending.username and db.query(User).filter(User.username == pending.username).first():
        raise HTTPException(status_code=409, detail="This username is already taken.")

    user = User(email=email, username=pending.username, password=pending.password_hash)
    start_trial(user)
    user.is_admin = email in ADMIN_EMAILS
    user.email_verified = True
    db.add(user)
    db.delete(pending)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email or username already exists.")
    get_or_create_subscription(user, db)
    return {"message": "Email verified. Account created successfully."}

@router.post("/login")
def login(credentials: LoginCredentials, db: Session = Depends(get_db)):
    identifier = (credentials.identifier or credentials.email or credentials.username or "").strip().lower()
    if not identifier:
        raise HTTPException(status_code=400, detail="Email or username is required.")
    check_rate_limit("login", identifier, limit=8, window_seconds=60)

    if "@" in identifier:
        email = normalize_email(identifier)
        user = db.query(User).filter(User.email == email).first()
    else:
        username = normalize_username(identifier)
        user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="Account not found.")
    if not verify_password(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect password.")

    if user.email.lower() in ADMIN_EMAILS and not user.is_admin:
        user.is_admin = True
        db.add(user)
        db.commit()
        db.refresh(user)
    refresh_user_plan(user, db)
    token = create_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


class PasswordResetRequest(BaseModel):
    email: str
    new_password: str | None = None
    otp: str | None = None
    token: str | None = None


class ForgotPasswordRequest(BaseModel):
    email: str


class VerifyOtpRequest(BaseModel):
    email: str
    otp: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class SupportTicketRequest(BaseModel):
    subject: str
    message: str


class SupportTicketStatusRequest(BaseModel):
    status: str


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class CreateOrderRequest(BaseModel):
    interval: str = "monthly"


class WebhookPayload(BaseModel):
    pass


@router.post("/reset-password")
def reset_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    email = normalize_email(request.email)
    check_rate_limit("reset-password", email, limit=6, window_seconds=300)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Account not found.")
    if not request.new_password:
        raise HTTPException(status_code=400, detail="New password is required")
    validate_password_strength(request.new_password)
    if not user.reset_token or not user.reset_token_expires_at:
        raise HTTPException(status_code=400, detail="This reset link has expired.")
    if utc_now() > user.reset_token_expires_at.replace(tzinfo=utc_now().tzinfo):
        user.reset_token = None
        user.reset_token_expires_at = None
        user.reset_otp_attempts = 0
        user.reset_otp_verified = False
        db.add(user)
        db.commit()
        raise HTTPException(status_code=400, detail="This reset link has expired.")

    if request.token:
        if not verify_password(request.token, user.reset_token):
            raise HTTPException(status_code=400, detail="Invalid reset link.")
    elif request.otp:
        if not user.reset_otp_verified:
            raise HTTPException(status_code=400, detail="OTP must be verified before resetting password")
        if not verify_password(request.otp, user.reset_token):
            raise HTTPException(status_code=400, detail="Invalid OTP")
    else:
        raise HTTPException(status_code=400, detail="Reset token is required.")
    if verify_password(request.new_password, user.password):
        raise HTTPException(status_code=400, detail="New password cannot be the same as the old password")

    user.password = hash_password(request.new_password)
    user.reset_token = None
    user.reset_token_expires_at = None
    user.reset_otp_attempts = 0
    user.reset_otp_verified = False
    db.add(user)
    db.commit()
    return {"message": "Password reset successfully."}


@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    email = normalize_email(request.email)
    check_rate_limit("forgot-password", email, limit=5, window_seconds=300)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"message": "If this email exists, a password reset link has been sent."}

    reset_token = secrets.token_urlsafe(32)
    user.reset_token = hash_password(reset_token)
    user.reset_token_expires_at = utc_now() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    user.reset_otp_attempts = 0
    user.reset_otp_verified = False
    db.add(user)
    db.commit()

    reset_url = build_reset_url(user.email, reset_token)
    try:
        sent = send_password_reset_email(user.email, reset_url)
    except Exception as exc:
        sent = False
        print(f"Password reset email failed: {exc}")

    response = {"message": "If this email exists, a password reset link has been sent."}
    if not sent and os.getenv("APP_ENV", "development").lower() != "production":
        response["dev_reset_url"] = reset_url
    return response


@router.post("/verify-reset-otp")
def verify_reset_otp(request: VerifyOtpRequest, db: Session = Depends(get_db)):
    email = normalize_email(request.email)
    check_rate_limit("verify-reset-otp", email, limit=6, window_seconds=300)
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.reset_token:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    if user.reset_otp_attempts >= 3:
        raise HTTPException(status_code=429, detail="Too many OTP attempts. Request a new OTP.")
    if not user.reset_token_expires_at or utc_now() > user.reset_token_expires_at.replace(tzinfo=utc_now().tzinfo):
        raise HTTPException(status_code=400, detail="OTP expired")

    if not verify_password(request.otp, user.reset_token):
        user.reset_otp_attempts = (user.reset_otp_attempts or 0) + 1
        db.add(user)
        db.commit()
        raise HTTPException(status_code=400, detail=f"Invalid OTP. {max(0, 3 - user.reset_otp_attempts)} attempts left.")

    user.reset_otp_verified = True
    db.add(user)
    db.commit()
    return {"message": "OTP verified. You can now set a new password."}


@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    email: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(request.current_password, user.password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    validate_password_strength(request.new_password)
    if verify_password(request.new_password, user.password):
        raise HTTPException(status_code=400, detail="New password cannot be the same as the old password")

    user.password = hash_password(request.new_password)
    user.reset_token = None
    user.reset_token_expires_at = None
    user.reset_otp_attempts = 0
    user.reset_otp_verified = False
    db.add(user)
    db.commit()
    return {"message": "Password changed successfully."}


@router.get("/profile")
def profile(email: str = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    refresh_user_plan(user, db)

    history_records = (
        db.query(UploadHistory)
        .filter(UploadHistory.user_id == user.id)
        .order_by(UploadHistory.created_at.desc())
        .all()
    )

    history = [
        {
            "id": record.id,
            "filename": record.filename,
            "original_filename": record.original_filename or record.filename,
            "summary": record.summary,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "dataset_lifecycle": (record.result_json or {}).get("dataset_lifecycle"),
        }
        for record in history_records
    ]

    plan = normalize_plan(user.plan)
    subscription = get_or_create_subscription(user, db)
    subscription_days_remaining = days_until(user.subscription_end_date) if plan == "premium" else None
    usage_snapshot = get_usage_snapshot(user, db)
    billing_history = get_billing_history(user, db)

    return {
        "email": user.email,
        "username": user.username,
        "is_admin": bool(user.is_admin),
        "preferred_language": user.preferred_language or "en",
        "latest_upload_id": user.latest_upload_id,
        "plan": plan,
        "has_full_access": has_full_access(user),
        "trial_start_date": user.trial_start_date.isoformat() if user.trial_start_date else None,
        "trial_end_date": user.trial_end_date.isoformat() if user.trial_end_date else None,
        "trial_days_remaining": None,
        "subscription_end_date": user.subscription_end_date.isoformat() if user.subscription_end_date else None,
        "subscription_days_remaining": subscription_days_remaining,
        "subscription_status": subscription.status,
        "cancel_at_period_end": bool(subscription.cancel_at_period_end),
        "history": history,
        "total_uploads": len(history),
        "total_queries": user.qa_queries_used or 0,
        "total_insights": sum(len((record.result_json or {}).get("insights", [])) for record in history_records),
        "limits": usage_snapshot,
        "usage": usage_snapshot,
        "subscription": {
            "price": PREMIUM_PRICE_INR,
            "yearly_price": PREMIUM_YEARLY_PRICE_INR,
            "currency": "INR",
            "renewal": "Monthly" if plan == "premium" else "Upgrade anytime",
            "interval": subscription.interval,
            "status": subscription.status,
        },
        "billing_history": billing_history,
        "pricing": {
            "free": {"price": 0, "currency": "INR", "limits": usage_snapshot},
            "premium": {
                "monthly_price": PREMIUM_PRICE_INR,
                "yearly_price": PREMIUM_YEARLY_PRICE_INR,
                "currency": "INR",
                "unlimited": True,
            },
        },
    }


@router.post("/support")
def create_support_ticket(
    request: SupportTicketRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticket = SupportTicket(
        user_id=user.id,
        subject=request.subject.strip(),
        message=request.message.strip(),
        status="open",
    )
    if not ticket.subject or not ticket.message:
        raise HTTPException(status_code=400, detail="Subject and message are required")

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    try:
        logger.info(
            "Support email attempt ticket_id=%s user_email=%s support_email=%s",
            ticket.id,
            user.email,
            SUPPORT_EMAIL,
        )
        send_support_email(ticket, user)
        ticket.email_sent = True
        ticket.email_sent_at = utc_now()
        ticket.email_error = None
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        logger.info("Support email success ticket_id=%s support_email=%s", ticket.id, SUPPORT_EMAIL)
    except Exception as exc:
        ticket.email_sent = False
        ticket.email_error = str(exc)[:2000]
        db.add(ticket)
        db.commit()
        logger.exception("Support email failure ticket_id=%s support_email=%s", ticket.id, SUPPORT_EMAIL)
        raise HTTPException(
            status_code=502,
            detail=f"Support ticket #{ticket.id} was saved, but the notification email could not be sent. Please contact support directly.",
        )

    return {
        "message": "Support request submitted and email delivered successfully.",
        "email_sent": True,
        "support_email": SUPPORT_EMAIL,
        "ticket": {
            "id": ticket.id,
            "subject": ticket.subject,
            "message": ticket.message,
            "status": ticket.status,
            "email_sent": ticket.email_sent,
            "email_sent_at": ticket.email_sent_at.isoformat() if ticket.email_sent_at else None,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        },
    }


@router.get("/support/my")
def get_my_support_tickets(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tickets = (
        db.query(SupportTicket)
        .filter(SupportTicket.user_id == user.id)
        .order_by(SupportTicket.created_at.desc())
        .all()
    )
    return {"tickets": [
        {
            "id": ticket.id,
            "subject": ticket.subject,
            "message": ticket.message,
            "status": ticket.status,
            "email_sent": ticket.email_sent,
            "email_sent_at": ticket.email_sent_at.isoformat() if ticket.email_sent_at else None,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        }
        for ticket in tickets
    ]}


@router.get("/admin/users")
def admin_users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.id.desc()).all()
    return {"users": [
        {
            "id": user.id,
            "email": user.email,
            "plan": user.plan or "basic",
            "is_admin": bool(user.is_admin),
            "trial_end_date": user.trial_end_date.isoformat() if user.trial_end_date else None,
            "subscription_end_date": user.subscription_end_date.isoformat() if user.subscription_end_date else None,
            "total_uploads": db.query(UploadHistory).filter(UploadHistory.user_id == user.id).count(),
            "total_queries": user.qa_queries_used or 0,
        }
        for user in users
    ]}


@router.get("/admin/support")
def admin_support_tickets(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    tickets = (
        db.query(SupportTicket, User.email)
        .join(User, SupportTicket.user_id == User.id)
        .order_by(SupportTicket.created_at.desc())
        .all()
    )
    return {"tickets": [
        {
            "id": ticket.id,
            "user_email": email,
            "subject": ticket.subject,
            "message": ticket.message,
            "status": ticket.status,
            "email_sent": ticket.email_sent,
            "email_sent_at": ticket.email_sent_at.isoformat() if ticket.email_sent_at else None,
            "email_error": ticket.email_error,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        }
        for ticket, email in tickets
    ]}


@router.patch("/admin/support/{ticket_id}")
def update_support_ticket(
    ticket_id: int,
    request: SupportTicketStatusRequest,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Support ticket not found")
    if request.status not in {"open", "in_progress", "resolved"}:
        raise HTTPException(status_code=400, detail="Invalid status")
    ticket.status = request.status
    db.add(ticket)
    db.commit()
    return {"message": "Support ticket updated.", "status": ticket.status}


@router.post("/create-order")
def create_order(request: CreateOrderRequest | None = None, email: str = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    refresh_user_plan(user, db)
    print("CREATE ORDER CALLED")
    print("RAZORPAY_KEY_ID =", repr(RAZORPAY_KEY_ID))
    print("RAZORPAY_KEY_SECRET =", repr(RAZORPAY_KEY_SECRET))


    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
      raise HTTPException(
        status_code=503,
        detail=f"KEY_ID={repr(RAZORPAY_KEY_ID)} SECRET={repr(RAZORPAY_KEY_SECRET)}"
    )
    interval = "yearly" if request and request.interval == "yearly" else "monthly"
    amount = PREMIUM_YEARLY_PRICE_PAISE if interval == "yearly" else PREMIUM_PRICE_PAISE
    price = PREMIUM_YEARLY_PRICE_INR if interval == "yearly" else PREMIUM_PRICE_INR

    payload = {
        "amount": amount,
        "currency": "INR",
        "receipt": f"dm_{user.id}_{interval}_{int(utc_now().timestamp())}",
        "notes": {"email": user.email, "plan": "premium", "interval": interval},
    }
    
    try:

        response = requests.post(

            "https://api.razorpay.com/v1/orders",

            auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET),

            json=payload,

            timeout=20,

        )

        print("RAZORPAY STATUS =", response.status_code)

        print("RAZORPAY RESPONSE =", response.text)

        response.raise_for_status()

        order = response.json()

    except Exception as exc:

        print("RAZORPAY ERROR =", repr(exc))

        raise HTTPException(

        status_code=502,

        detail=f"Razorpay order creation failed: {str(exc)}"

        )

    billing = create_billing_record(user, db, interval, order)
    user.razorpay_order_id = order["id"]
    db.add(user)
    db.commit()

    return {
        "key_id": RAZORPAY_KEY_ID,
        "order_id": order["id"],
        "billing_id": billing.id,
        "amount": order["amount"],
        "currency": order["currency"],
        "plan": "premium",
        "interval": interval,
        "price": price,
    }


@router.post("/verify-payment")
def verify_payment(request: VerifyPaymentRequest, email: str = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=503, detail="Razorpay is not configured on this server.")
    if request.razorpay_order_id != user.razorpay_order_id:
        raise HTTPException(status_code=400, detail="Payment order does not match the active subscription order.")

    signed_payload = f"{request.razorpay_order_id}|{request.razorpay_payment_id}"
    expected_signature = hmac.new(
        RAZORPAY_KEY_SECRET.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, request.razorpay_signature):
        raise HTTPException(status_code=400, detail="Payment verification failed.")

    billing = db.query(BillingRecord).filter(
        BillingRecord.user_id == user.id,
        BillingRecord.provider_order_id == request.razorpay_order_id,
    ).order_by(BillingRecord.id.desc()).first()
    interval = billing.interval if billing else "monthly"

    activate_premium(user, interval)
    user.razorpay_order_id = None
    subscription = get_or_create_subscription(user, db, interval)
    subscription.plan_code = PLAN_PREMIUM
    subscription.interval = interval
    subscription.status = "active"
    subscription.current_period_start = utc_now()
    subscription.current_period_end = user.subscription_end_date
    subscription.cancel_at_period_end = False
    if billing:
        billing.status = "paid"
        billing.provider_payment_id = request.razorpay_payment_id
        billing.provider_signature = request.razorpay_signature
        db.add(billing)
    payment = PaymentRecord(
        user_id=user.id,
        billing_record_id=billing.id if billing else None,
        event_type="payment_verified",
        provider_payment_id=request.razorpay_payment_id,
        provider_order_id=request.razorpay_order_id,
        amount_paise=billing.amount_paise if billing else None,
        status="captured",
        payload_json=request.model_dump(),
    )
    db.add(payment)
    db.add(subscription)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {
        "message": "Payment successful. Plan upgraded.",
        "plan": user.plan,
        "subscription_end_date": user.subscription_end_date.isoformat() if user.subscription_end_date else None,
    }


@router.post("/cancel-subscription")
def cancel_subscription(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subscription = get_or_create_subscription(user, db)
    if normalize_plan(user.plan) != PLAN_PREMIUM:
        raise HTTPException(status_code=400, detail="You are already on the Free plan.")
    subscription.cancel_at_period_end = True
    subscription.status = "cancel_scheduled"
    db.add(subscription)
    db.commit()
    return {
        "message": "Premium will remain active until the current billing period ends.",
        "cancel_at_period_end": True,
        "subscription_end_date": user.subscription_end_date.isoformat() if user.subscription_end_date else None,
    }


@router.post("/renew-subscription")
def renew_subscription(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subscription = get_or_create_subscription(user, db)
    if normalize_plan(user.plan) != PLAN_PREMIUM:
        raise HTTPException(status_code=400, detail="Upgrade to Premium before renewing.")
    subscription.cancel_at_period_end = False
    subscription.status = "active"
    db.add(subscription)
    db.commit()
    return {"message": "Subscription renewal is active.", "cancel_at_period_end": False}


@router.get("/billing-history")
def billing_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"billing_history": get_billing_history(user, db)}


@router.post("/razorpay/webhook")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", RAZORPAY_KEY_SECRET)
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    if not webhook_secret or not signature:
        raise HTTPException(status_code=400, detail="Webhook signature is required.")
    expected = hmac.new(webhook_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature.")

    payload = json.loads(body.decode("utf-8"))
    event = payload.get("event", "unknown")
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    order_id = payment_entity.get("order_id")
    payment_id = payment_entity.get("id")
    billing = db.query(BillingRecord).filter(BillingRecord.provider_order_id == order_id).first() if order_id else None
    user_id = billing.user_id if billing else None
    if user_id:
        db.add(PaymentRecord(
            user_id=user_id,
            billing_record_id=billing.id,
            event_type=event,
            provider_payment_id=payment_id,
            provider_order_id=order_id,
            amount_paise=payment_entity.get("amount"),
            status=payment_entity.get("status", "received"),
            payload_json=payload,
        ))
        if event in {"payment.captured", "order.paid"}:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                activate_premium(user, billing.interval)
                billing.status = "paid"
                billing.provider_payment_id = payment_id
                subscription = get_or_create_subscription(user, db, billing.interval)
                subscription.plan_code = PLAN_PREMIUM
                subscription.status = "active"
                subscription.current_period_start = utc_now()
                subscription.current_period_end = user.subscription_end_date
                db.add(user)
                db.add(subscription)
                db.add(billing)
        db.commit()
    return {"status": "received", "event": event}
