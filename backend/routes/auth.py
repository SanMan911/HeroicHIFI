from fastapi import APIRouter, HTTPException, Request, Depends
import random
import secrets
import uuid
from datetime import datetime, timezone, timedelta

from config import db
from models.schemas import OTPRequest, OTPVerify, RegisterInput, LoginInput, PasswordResetRequest, PasswordResetConfirm
from utils.auth import hash_password, verify_password, create_access_token, get_current_user
from utils.email import send_otp_email, send_reset_email, send_registration_notification
from utils.activity import log_activity

router = APIRouter(prefix="/api")


@router.post("/auth/send-otp")
async def send_otp(data: OTPRequest, request: Request):
    email = data.email.lower().strip()
    otp = str(random.randint(100000, 999999))
    token = secrets.token_hex(32)
    await db.otp_tokens.delete_many({"email": email, "purpose": data.purpose})
    await db.otp_tokens.insert_one({
        "email": email, "otp": otp, "purpose": data.purpose, "token": token, "verified": False,
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10)
    })
    sent = await send_otp_email(email, otp)
    await log_activity("otp_sent", "auth", "", email, f"OTP sent for {data.purpose}, email_delivered={sent}", request.client.host if request.client else "")
    msg = "OTP sent to your email." if sent else "OTP generated. Check server logs (Resend API key not configured)."
    return {"message": msg, "email_sent": sent, "otp_debug": otp if not sent else None}


@router.post("/auth/verify-otp")
async def verify_otp(data: OTPVerify, request: Request):
    email = data.email.lower().strip()
    record = await db.otp_tokens.find_one({"email": email, "purpose": data.purpose, "verified": False})
    if not record:
        raise HTTPException(status_code=400, detail="No pending OTP found. Please request a new one.")
    expires_at = record["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
    elif expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="OTP expired. Please request a new one.")
    if record["otp"] != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP. Please try again.")
    await db.otp_tokens.update_one({"_id": record["_id"]}, {"$set": {"verified": True}})
    await log_activity("otp_verified", "auth", "", email, f"OTP verified for {data.purpose}", request.client.host if request.client else "")
    return {"message": "Email verified successfully.", "otp_token": record["token"]}


@router.post("/auth/register")
async def register(data: RegisterInput, request: Request):
    email = data.email.lower().strip()
    otp_record = await db.otp_tokens.find_one({"email": email, "token": data.otp_token, "purpose": "registration", "verified": True})
    if not otp_record:
        raise HTTPException(status_code=400, detail="Email not verified. Please complete OTP verification first.")
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    chosen_role = data.role if data.role in ("volunteer", "member") else "member"
    doc = {
        "name": data.name, "email": email,
        "password_hash": hash_password(data.password),
        "phone": data.phone, "age": data.age, "dob": data.dob,
        "address": data.address, "pan_number": data.pan_number,
        "aadhaar_number": data.aadhaar_number,
        "role": chosen_role, "email_verified": True,
        "volunteer_hours": 0, "badges": ["Helping Hero"] if chosen_role == "volunteer" else [],
        "specializations": data.specializations if chosen_role == "volunteer" else [],
        "profile_pic_path": "", "status": "active",
        "merchandise_issued": False, "admin_comments": "",
        "suspended_until": None, "suspension_reason": "",
        "pan_verified": False, "aadhaar_verified": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.users.insert_one(doc)
    user_id = str(result.inserted_id)
    token = create_access_token(user_id, email)
    await db.otp_tokens.delete_many({"email": email, "purpose": "registration"})
    await log_activity("user_registered", "user", user_id, email, f"New user: {data.name}, role: {chosen_role}", request.client.host if request.client else "")
    # Send notification to admin email
    try:
        await send_registration_notification(data.name, email, chosen_role)
    except Exception:
        pass
    return {"token": token, "user": {"id": user_id, "name": data.name, "email": email, "role": chosen_role, "phone": data.phone, "pan_number": data.pan_number, "aadhaar_number": data.aadhaar_number, "address": data.address, "age": data.age, "dob": data.dob, "volunteer_hours": 0, "badges": ["Helping Hero"] if chosen_role == "volunteer" else [], "profile_pic_path": "", "status": "active"}}


@router.post("/auth/login")
async def login(data: LoginInput, request: Request):
    email = data.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if user.get("status") == "suspended":
        sus_until = user.get("suspended_until", "")
        reason = user.get("suspension_reason", "")
        msg = "Your account is suspended."
        if sus_until:
            msg += f" Until: {sus_until}."
        if reason:
            msg += f" Reason: {reason}"
        raise HTTPException(status_code=403, detail=msg)
    user_id = str(user["_id"])
    token = create_access_token(user_id, email)
    await log_activity("user_login", "user", user_id, email, "Login successful", request.client.host if request.client else "")
    return {"token": token, "user": {
        "id": user_id, "name": user.get("name", ""), "email": email, "role": user.get("role", "volunteer"),
        "phone": user.get("phone", ""), "pan_number": user.get("pan_number", ""), "aadhaar_number": user.get("aadhaar_number", ""),
        "address": user.get("address", ""), "age": user.get("age"), "dob": user.get("dob", ""),
        "volunteer_hours": user.get("volunteer_hours", 0), "badges": user.get("badges", ["Helping Hero"]),
        "profile_pic_path": user.get("profile_pic_path", ""), "status": user.get("status", "active"),
    }}


@router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {"user": user}


@router.post("/auth/logout")
async def logout():
    return {"message": "Logged out successfully"}


@router.post("/auth/forgot-password")
async def forgot_password(data: PasswordResetRequest, request: Request):
    email = data.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user:
        return {"message": "If an account with that email exists, a reset link has been sent."}
    token = secrets.token_hex(32)
    await db.password_reset_tokens.delete_many({"email": email})
    await db.password_reset_tokens.insert_one({
        "email": email, "token": token, "used": False,
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=30)
    })
    sent, link = await send_reset_email(email, token)
    await log_activity("password_reset_requested", "auth", "", email, f"Reset email sent={sent}", request.client.host if request.client else "")
    result = {"message": "If an account with that email exists, a reset link has been sent.", "email_sent": sent}
    if not sent:
        result["debug_link"] = link
    return result


@router.post("/auth/reset-password")
async def reset_password(data: PasswordResetConfirm, request: Request):
    email = data.email.lower().strip()
    record = await db.password_reset_tokens.find_one({"email": email, "token": data.token, "used": False})
    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link.")
    expires_at = record["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
    elif expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Reset link has expired. Please request a new one.")
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    await db.users.update_one({"email": email}, {"$set": {"password_hash": hash_password(data.new_password)}})
    await db.password_reset_tokens.update_one({"_id": record["_id"]}, {"$set": {"used": True}})
    await log_activity("password_reset_completed", "auth", "", email, "Password reset successful", request.client.host if request.client else "")
    return {"message": "Password reset successfully. You can now log in with your new password."}
