from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import bcrypt
import jwt
import uuid
import secrets
import asyncio
import random
import io
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

# ── PDF imports ──
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

# ── Resend import ──
try:
    import resend
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
except ImportError:
    resend = None

import re

# ── Number Stripping Utility ──
NUMBER_WORDS = [
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen",
    "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety",
    "hundred", "thousand", "million", "billion", "trillion",
    "lakh", "lakhs", "crore", "crores",
    "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth",
    "\u0936\u0942\u0928\u094d\u092f", "\u090f\u0915", "\u0926\u094b", "\u0924\u0940\u0928", "\u091a\u093e\u0930", "\u092a\u093e\u0901\u091a", "\u091b\u0939", "\u0938\u093e\u0924", "\u0906\u0920", "\u0928\u094c", "\u0926\u0938",
    "\u0917\u094d\u092f\u093e\u0930\u0939", "\u092c\u093e\u0930\u0939", "\u0924\u0947\u0930\u0939", "\u091a\u094c\u0926\u0939", "\u092a\u0902\u0926\u094d\u0930\u0939", "\u0938\u094b\u0932\u0939", "\u0938\u0924\u094d\u0930\u0939", "\u0905\u0920\u093e\u0930\u0939", "\u0909\u0928\u094d\u0928\u0940\u0938",
    "\u092c\u0940\u0938", "\u0924\u0940\u0938", "\u091a\u093e\u0932\u0940\u0938", "\u092a\u091a\u093e\u0938", "\u0938\u093e\u0920", "\u0938\u0924\u094d\u0924\u0930", "\u0905\u0920\u094d\u0920\u093e\u0930\u0939", "\u0928\u092c\u094d\u092c\u0947",
    "\u0938\u094c", "\u0939\u091c\u093c\u093e\u0930", "\u0932\u093e\u0916", "\u0915\u0930\u094b\u0921\u093c",
]

def strip_numbers(text: str) -> str:
    if not text:
        return text
    result = re.sub(r'\d+', '[*]', text)
    for word in NUMBER_WORDS:
        escaped = re.escape(word)
        if word.isascii():
            pattern = re.compile(r'\b' + escaped + r'\b', re.IGNORECASE)
        else:
            pattern = re.compile(escaped, re.IGNORECASE)
        result = pattern.sub('[*]', result)
    return result

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI(title="Heroic HIFI Foundation API")
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

JWT_ALGORITHM = "HS256"
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")

def get_jwt_secret():
    return os.environ["JWT_SECRET"]

# ── Activity Logging ──
async def log_activity(action: str, entity_type: str, entity_id: str = "", user_email: str = "", details: str = "", ip: str = ""):
    await db.activity_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "user_email": user_email,
        "details": details,
        "ip": ip,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

# ── Password helpers ──
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

def create_access_token(user_id: str, email: str) -> str:
    payload = {"sub": user_id, "email": email, "exp": datetime.now(timezone.utc) + timedelta(hours=24), "type": "access"}
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request) -> dict:
    auth_header = request.headers.get("Authorization", "")
    token = auth_header[7:] if auth_header.startswith("Bearer ") else None
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        user["_id"] = str(user["_id"])
        user.pop("password_hash", None)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user_optional(request: Request):
    try:
        return await get_current_user(request)
    except HTTPException:
        return None

async def require_admin(request: Request) -> dict:
    user = await get_current_user(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# ── Models ──
class OTPRequest(BaseModel):
    email: str
    purpose: str = "registration"

class OTPVerify(BaseModel):
    email: str
    otp: str
    purpose: str = "registration"

class RegisterInput(BaseModel):
    name: str
    email: str
    password: str
    phone: str
    age: Optional[int] = None
    dob: Optional[str] = None
    address: Optional[str] = None
    pan_number: str
    aadhaar_number: str
    otp_token: str

class LoginInput(BaseModel):
    email: str
    password: str

class DonationInput(BaseModel):
    name: str
    email: str
    phone: str
    amount: int
    pan_number: str
    aadhaar_number: Optional[str] = None
    address: Optional[str] = None
    message: Optional[str] = None
    otp_token: Optional[str] = None

class VolunteerInput(BaseModel):
    name: str
    email: str
    phone: str
    city: str
    interests: List[str] = []
    message: Optional[str] = None

class QueryInput(BaseModel):
    name: str
    email: str
    mission: str
    subject: str
    message: str

class StatusUpdate(BaseModel):
    status: str

# ── OTP Endpoints ──
async def send_otp_email(email: str, otp: str):
    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key or not resend:
        logger.info(f"[OTP MOCK] Email: {email}, OTP: {otp}")
        return False
    try:
        resend.api_key = api_key
        params = {
            "from": SENDER_EMAIL,
            "to": [email],
            "subject": "Heroic HIFI Foundation - Email Verification OTP",
            "html": f"""
            <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:20px;">
                <h2 style="color:#1E56A0;">Heroic HIFI Foundation</h2>
                <p>Your email verification code is:</p>
                <div style="background:#F0F7FA;padding:20px;text-align:center;border-radius:12px;margin:20px 0;">
                    <span style="font-size:32px;font-weight:bold;letter-spacing:8px;color:#1E56A0;">{otp}</span>
                </div>
                <p style="color:#666;font-size:13px;">This code expires in 10 minutes. If you did not request this, please ignore this email.</p>
            </div>
            """
        }
        await asyncio.to_thread(resend.Emails.send, params)
        return True
    except Exception as e:
        logger.error(f"Resend email error: {e}")
        return False

@api_router.post("/auth/send-otp")
async def send_otp(data: OTPRequest, request: Request):
    email = data.email.lower().strip()
    otp = str(random.randint(100000, 999999))
    token = secrets.token_hex(32)
    await db.otp_tokens.delete_many({"email": email, "purpose": data.purpose})
    await db.otp_tokens.insert_one({
        "email": email,
        "otp": otp,
        "purpose": data.purpose,
        "token": token,
        "verified": False,
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10)
    })
    sent = await send_otp_email(email, otp)
    await log_activity("otp_sent", "auth", "", email, f"OTP sent for {data.purpose}, email_delivered={sent}", request.client.host if request.client else "")
    msg = "OTP sent to your email." if sent else "OTP generated. Check server logs (Resend API key not configured)."
    return {"message": msg, "email_sent": sent, "otp_debug": otp if not sent else None}

@api_router.post("/auth/verify-otp")
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

# ── Auth Routes ──
@api_router.post("/auth/register")
async def register(data: RegisterInput, request: Request):
    email = data.email.lower().strip()
    otp_record = await db.otp_tokens.find_one({"email": email, "token": data.otp_token, "purpose": "registration", "verified": True})
    if not otp_record:
        raise HTTPException(status_code=400, detail="Email not verified. Please complete OTP verification first.")
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    doc = {
        "name": data.name, "email": email,
        "password_hash": hash_password(data.password),
        "phone": data.phone, "age": data.age, "dob": data.dob,
        "address": data.address, "pan_number": data.pan_number,
        "aadhaar_number": data.aadhaar_number,
        "role": "volunteer", "email_verified": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.users.insert_one(doc)
    user_id = str(result.inserted_id)
    token = create_access_token(user_id, email)
    await db.otp_tokens.delete_many({"email": email, "purpose": "registration"})
    await log_activity("user_registered", "user", user_id, email, f"New user: {data.name}", request.client.host if request.client else "")
    return {"token": token, "user": {"id": user_id, "name": data.name, "email": email, "role": "volunteer", "phone": data.phone, "pan_number": data.pan_number, "aadhaar_number": data.aadhaar_number, "address": data.address, "age": data.age, "dob": data.dob}}

@api_router.post("/auth/login")
async def login(data: LoginInput, request: Request):
    email = data.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    user_id = str(user["_id"])
    token = create_access_token(user_id, email)
    await log_activity("user_login", "user", user_id, email, "Login successful", request.client.host if request.client else "")
    return {"token": token, "user": {
        "id": user_id, "name": user.get("name", ""), "email": email, "role": user.get("role", "volunteer"),
        "phone": user.get("phone", ""), "pan_number": user.get("pan_number", ""), "aadhaar_number": user.get("aadhaar_number", ""),
        "address": user.get("address", ""), "age": user.get("age"), "dob": user.get("dob", ""),
    }}

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {"user": user}

@api_router.post("/auth/logout")
async def logout():
    return {"message": "Logged out successfully"}

# ── Missions Data ──
MISSIONS_DATA = [
    {"slug": "mission-shakti", "name": "Mission Shakti", "name_hi": "\u092e\u093f\u0936\u0928 \u0936\u0915\u094d\u0924\u093f", "tagline": "Empowering Women, Transforming Communities", "tagline_hi": "\u0928\u093e\u0930\u0940 \u0938\u0936\u0915\u094d\u0924\u093f\u0915\u0930\u0923, \u0938\u092e\u0941\u0926\u093e\u092f \u0915\u093e \u0915\u093e\u092f\u093e\u0915\u0932\u094d\u092a", "description": "Mission Shakti is dedicated to empowering women across rural and urban India through skill development, financial literacy, and leadership training. We believe that when women rise, entire communities are uplifted.", "description_hi": "\u092e\u093f\u0936\u0928 \u0936\u0915\u094d\u0924\u093f \u0917\u094d\u0930\u093e\u092e\u0940\u0923 \u090f\u0935\u0902 \u0936\u0939\u0930\u0940 \u092d\u093e\u0930\u0924 \u092e\u0947\u0902 \u0915\u094c\u0936\u0932 \u0935\u093f\u0915\u093e\u0938, \u0935\u093f\u0924\u094d\u0924\u0940\u092f \u0938\u093e\u0915\u094d\u0937\u0930\u0924\u093e \u0914\u0930 \u0928\u0947\u0924\u0943\u0924\u094d\u0935 \u092a\u094d\u0930\u0936\u093f\u0915\u094d\u0937\u0923 \u0915\u0947 \u092e\u093e\u0927\u094d\u092f\u092e \u0938\u0947 \u092e\u0939\u093f\u0932\u093e\u0913\u0902 \u0915\u0947 \u0938\u0936\u0915\u094d\u0924\u093f\u0915\u0930\u0923 \u0939\u0947\u0924\u0941 \u0938\u092e\u0930\u094d\u092a\u093f\u0924 \u0939\u0948\u0964", "icon": "Sparkles", "color": "#EA580C", "image_key": "mission_shakti_women"},
    {"slug": "mission-swabhiman", "name": "Mission Swabhiman", "name_hi": "\u092e\u093f\u0936\u0928 \u0938\u094d\u0935\u093e\u092d\u093f\u092e\u093e\u0928", "tagline": "Dignity Through Menstrual Hygiene Awareness", "tagline_hi": "\u092e\u093e\u0938\u093f\u0915 \u0927\u0930\u094d\u092e \u0938\u094d\u0935\u091a\u094d\u091b\u0924\u093e \u091c\u093e\u0917\u0930\u0942\u0915\u0924\u093e \u0926\u094d\u0935\u093e\u0930\u093e \u0938\u092e\u094d\u092e\u093e\u0928", "description": "Mission Swabhiman raises awareness about female menstrual hygiene, breaking taboos and ensuring every woman has access to safe, hygienic products.", "description_hi": "\u092e\u093f\u0936\u0928 \u0938\u094d\u0935\u093e\u092d\u093f\u092e\u093e\u0928 \u092e\u0939\u093f\u0932\u093e \u092e\u093e\u0938\u093f\u0915 \u0927\u0930\u094d\u092e \u0938\u094d\u0935\u091a\u094d\u091b\u0924\u093e \u0915\u0947 \u092c\u093e\u0930\u0947 \u092e\u0947\u0902 \u091c\u093e\u0917\u0930\u0942\u0915\u0924\u093e \u092c\u0922\u093c\u093e\u0924\u093e \u0939\u0948\u0964", "icon": "Heart", "color": "#DB2777", "image_key": "mission_swabhiman_health"},
    {"slug": "mission-roshni", "name": "Mission Roshni", "name_hi": "\u092e\u093f\u0936\u0928 \u0930\u094b\u0936\u0928\u0940", "tagline": "Illuminating Futures Through Education", "tagline_hi": "\u0936\u093f\u0915\u094d\u0937\u093e \u0926\u094d\u0935\u093e\u0930\u093e \u092d\u0935\u093f\u0937\u094d\u092f \u0915\u094b \u0930\u094b\u0936\u0928 \u0915\u0930\u0928\u093e", "description": "Mission Roshni brings the light of education to children and students from slum areas and underprivileged communities.", "description_hi": "\u092e\u093f\u0936\u0928 \u0930\u094b\u0936\u0928\u0940 \u091d\u0941\u0917\u094d\u0917\u0940-\u092c\u0938\u094d\u0924\u093f\u092f\u094b\u0902 \u0914\u0930 \u0935\u0902\u091a\u093f\u0924 \u0938\u092e\u0941\u0926\u093e\u092f\u094b\u0902 \u0915\u0947 \u092c\u091a\u094d\u091a\u094b\u0902 \u0924\u0915 \u0936\u093f\u0915\u094d\u0937\u093e \u0915\u0940 \u091c\u094d\u092f\u094b\u0924\u093f \u092a\u0939\u0941\u0901\u091a\u093e\u0924\u093e \u0939\u0948\u0964", "icon": "BookOpen", "color": "#2563EB", "image_key": "mission_roshni_education"},
    {"slug": "mission-koi-bhookha-na-soye", "name": "Mission Koi Bhookha Na Soye", "name_hi": "\u092e\u093f\u0936\u0928 \u0915\u094b\u0908 \u092d\u0942\u0916\u093e \u0928 \u0938\u094b\u090f", "tagline": "No One Sleeps Hungry", "tagline_hi": "\u0915\u094b\u0908 \u092d\u0942\u0916\u093e \u0928 \u0938\u094b\u090f", "description": "This mission collects excess food from hotels, restaurants, weddings, and events, and distributes it among the destitute, homeless, and hungry.", "description_hi": "\u092f\u0939 \u092e\u093f\u0936\u0928 \u0939\u094b\u091f\u0932\u094b\u0902, \u0930\u0947\u0938\u094d\u0924\u0930\u093e\u0901\u0913\u0902, \u0935\u093f\u0935\u093e\u0939\u094b\u0902 \u0938\u0947 \u0905\u0924\u093f\u0930\u093f\u0915\u094d\u0924 \u092d\u094b\u091c\u0928 \u090f\u0915\u0924\u094d\u0930 \u0915\u0930\u0924\u093e \u0939\u0948\u0964", "icon": "UtensilsCrossed", "color": "#D97706", "image_key": "mission_koibhookhanasoye_food"},
    {"slug": "mission-paryavaran", "name": "Mission Paryavaran", "name_hi": "\u092e\u093f\u0936\u0928 \u092a\u0930\u094d\u092f\u093e\u0935\u0930\u0923", "tagline": "Nurturing Nature, Securing Tomorrow", "tagline_hi": "\u092a\u094d\u0930\u0915\u0943\u0924\u093f \u0915\u093e \u092a\u094b\u0937\u0923, \u0915\u0932 \u0915\u0940 \u0938\u0941\u0930\u0915\u094d\u0937\u093e", "description": "Mission Paryavaran is committed to raising awareness about the environment and cleanliness.", "description_hi": "\u092e\u093f\u0936\u0928 \u092a\u0930\u094d\u092f\u093e\u0935\u0930\u0923 \u092a\u0930\u094d\u092f\u093e\u0935\u0930\u0923 \u090f\u0935\u0902 \u0938\u094d\u0935\u091a\u094d\u091b\u0924\u093e \u0915\u0947 \u092c\u093e\u0930\u0947 \u092e\u0947\u0902 \u091c\u093e\u0917\u0930\u0942\u0915\u0924\u093e \u092c\u0922\u093c\u093e\u0928\u0947 \u0939\u0947\u0924\u0941 \u092a\u094d\u0930\u0924\u093f\u092c\u0926\u094d\u0927 \u0939\u0948\u0964", "icon": "TreePine", "color": "#16A34A", "image_key": "mission_paryavaran_environment"},
    {"slug": "mission-karuna", "name": "Mission Karuna", "name_hi": "\u092e\u093f\u0936\u0928 \u0915\u0930\u0941\u0923\u093e", "tagline": "Compassion for Every Living Being", "tagline_hi": "\u092a\u094d\u0930\u0924\u094d\u092f\u0947\u0915 \u092a\u094d\u0930\u093e\u0923\u0940 \u0915\u0947 \u092a\u094d\u0930\u0924\u093f \u0915\u0930\u0941\u0923\u093e", "description": "Mission Karuna empathizes with voiceless animals. We raise awareness and fight against animal cruelty.", "description_hi": "\u092e\u093f\u0936\u0928 \u0915\u0930\u0941\u0923\u093e \u092e\u0942\u0915 \u092a\u094d\u0930\u093e\u0923\u093f\u092f\u094b\u0902 \u0915\u0947 \u092a\u094d\u0930\u0924\u093f \u0938\u0939\u093e\u0928\u0941\u092d\u0942\u0924\u093f \u0930\u0916\u0924\u093e \u0939\u0948\u0964", "icon": "PawPrint", "color": "#7C3AED", "image_key": "mission_karuna_animals"},
    {"slug": "mission-paridhan", "name": "Mission Paridhan", "name_hi": "\u092e\u093f\u0936\u0928 \u092a\u0930\u093f\u0927\u093e\u0928", "tagline": "Clothing the Needy, Wrapping with Dignity", "tagline_hi": "\u0935\u0938\u094d\u0924\u094d\u0930\u0926\u093e\u0928, \u0938\u092e\u094d\u092e\u093e\u0928 \u0915\u093e \u0906\u0935\u0930\u0923", "description": "Mission Paridhan collects donated clothes and distributes them among beggars and the needy.", "description_hi": "\u092e\u093f\u0936\u0928 \u092a\u0930\u093f\u0927\u093e\u0928 \u0926\u093e\u0928 \u092e\u0947\u0902 \u092a\u094d\u0930\u093e\u092a\u094d\u0924 \u0935\u0938\u094d\u0924\u094d\u0930\u094b\u0902 \u0915\u094b \u090f\u0915\u0924\u094d\u0930 \u0915\u0930\u0924\u093e \u0939\u0948\u0964", "icon": "Shirt", "color": "#0891B2", "image_key": "mission_paridhan_clothes"},
]

@api_router.get("/missions")
async def get_missions():
    return MISSIONS_DATA

@api_router.get("/missions/{slug}")
async def get_mission(slug: str):
    for m in MISSIONS_DATA:
        if m["slug"] == slug:
            return m
    raise HTTPException(status_code=404, detail="Mission not found")

# ── Razorpay Donation Flow ──
@api_router.post("/donations/create-order")
async def create_razorpay_order(data: DonationInput, request: Request):
    user = await get_current_user_optional(request)
    if not user and not data.otp_token:
        raise HTTPException(status_code=400, detail="Email verification required. Please verify your email with OTP first.")
    if not user and data.otp_token:
        otp_rec = await db.otp_tokens.find_one({"email": data.email.lower().strip(), "token": data.otp_token, "purpose": "donation", "verified": True})
        if not otp_rec:
            raise HTTPException(status_code=400, detail="Invalid or expired email verification. Please verify again.")
    donation_id = str(uuid.uuid4())
    doc = {
        "id": donation_id, "name": data.name, "email": data.email.lower().strip(),
        "phone": data.phone, "amount": data.amount, "pan_number": data.pan_number,
        "aadhaar_number": data.aadhaar_number or (user.get("aadhaar_number", "") if user else ""),
        "address": data.address or (user.get("address", "") if user else ""),
        "message": data.message, "status": "pending",
        "user_id": user.get("_id", "") if user else "",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    rz_key = os.environ.get("RAZORPAY_KEY_ID")
    rz_secret = os.environ.get("RAZORPAY_KEY_SECRET")
    if rz_key and rz_secret:
        import razorpay
        rz_client = razorpay.Client(auth=(rz_key, rz_secret))
        order = rz_client.order.create(data={"amount": data.amount * 100, "currency": "INR", "receipt": donation_id})
        doc["razorpay_order_id"] = order["id"]
        await db.donations.insert_one(doc)
        doc.pop("_id", None)
        await log_activity("donation_order_created", "donation", donation_id, data.email, f"Amount: {data.amount} INR, Razorpay order", request.client.host if request.client else "")
        return {"donation": doc, "razorpay_order_id": order["id"], "razorpay_key": rz_key, "amount": data.amount * 100, "currency": "INR"}
    else:
        await db.donations.insert_one(doc)
        doc.pop("_id", None)
        await log_activity("donation_recorded", "donation", donation_id, data.email, f"Amount: {data.amount} INR, manual", request.client.host if request.client else "")
        return {"donation": doc, "razorpay_order_id": None, "message": "Donation recorded. Our team will contact you for payment."}

@api_router.post("/donations/verify-payment")
async def verify_razorpay_payment(request: Request):
    body = await request.json()
    rz_key = os.environ.get("RAZORPAY_KEY_ID")
    rz_secret = os.environ.get("RAZORPAY_KEY_SECRET")
    if not rz_key or not rz_secret:
        raise HTTPException(status_code=500, detail="Razorpay not configured")
    import razorpay
    rz_client = razorpay.Client(auth=(rz_key, rz_secret))
    try:
        rz_client.utility.verify_payment_signature({
            "razorpay_order_id": body["razorpay_order_id"],
            "razorpay_payment_id": body["razorpay_payment_id"],
            "razorpay_signature": body["razorpay_signature"],
        })
        await db.donations.update_one({"id": body["donation_id"]}, {"$set": {"status": "confirmed", "razorpay_payment_id": body["razorpay_payment_id"]}})
        await log_activity("payment_verified", "donation", body["donation_id"], "", "Razorpay payment confirmed", request.client.host if request.client else "")
        return {"message": "Payment verified successfully", "status": "confirmed"}
    except Exception:
        await db.donations.update_one({"id": body["donation_id"]}, {"$set": {"status": "failed"}})
        raise HTTPException(status_code=400, detail="Payment verification failed")

@api_router.post("/donations")
async def create_donation(data: DonationInput, request: Request):
    doc = {
        "id": str(uuid.uuid4()), "name": data.name, "email": data.email.lower().strip(),
        "phone": data.phone, "amount": data.amount, "pan_number": data.pan_number,
        "aadhaar_number": data.aadhaar_number or "", "address": data.address or "",
        "message": data.message, "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.donations.insert_one(doc)
    doc.pop("_id", None)
    await log_activity("donation_recorded", "donation", doc["id"], data.email, f"Amount: {data.amount}", request.client.host if request.client else "")
    return {"message": "Donation recorded successfully.", "donation": doc}

@api_router.get("/donations")
async def list_donations(user: dict = Depends(get_current_user)):
    return await db.donations.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)

# ── 80G Certificate PDF ──
def generate_80g_pdf(donation: dict) -> bytes:
    buf = io.BytesIO()
    c = pdf_canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    navy = HexColor("#1E56A0")
    sky = HexColor("#28A9E2")
    orange = HexColor("#FF7F00")
    dark = HexColor("#0D2847")
    gray = HexColor("#666666")

    # Border
    c.setStrokeColor(navy)
    c.setLineWidth(3)
    c.rect(20*mm, 20*mm, w - 40*mm, h - 40*mm)
    c.setStrokeColor(sky)
    c.setLineWidth(1)
    c.rect(22*mm, 22*mm, w - 44*mm, h - 44*mm)

    y = h - 45*mm
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(navy)
    c.drawCentredString(w/2, y, "HEROIC HIFI FOUNDATION")
    y -= 7*mm
    c.setFont("Helvetica", 9)
    c.setFillColor(gray)
    c.drawCentredString(w/2, y, "Section 8 Company under The Companies Act, 2013")
    y -= 5*mm
    c.drawCentredString(w/2, y, "CIN: U88900BR2024NPL072593")
    y -= 5*mm
    c.setFont("Helvetica", 7.5)
    c.drawCentredString(w/2, y, "C/o Nirbhay Kr. Agnihotry, Village: Korha, Tola: Korha, Mirjanhat, Bhagalpur, Jagdishpur, Bihar 812005")

    y -= 12*mm
    c.setStrokeColor(orange)
    c.setLineWidth(2)
    c.line(35*mm, y, w - 35*mm, y)

    y -= 10*mm
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(dark)
    c.drawCentredString(w/2, y, "PROVISIONAL DONATION RECEIPT")
    y -= 7*mm
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(orange)
    c.drawCentredString(w/2, y, "Under Section 80G of the Income Tax Act, 1961")
    y -= 5*mm
    c.setFont("Helvetica", 8.5)
    c.setFillColor(gray)
    c.drawCentredString(w/2, y, "(Provisional Certificate \u2014 Eligible for 50% Tax Rebate)")

    cert_no = f"HHF/{datetime.now().strftime('%Y%m')}/{donation['id'][:8].upper()}"
    y -= 12*mm
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(dark)
    c.drawString(35*mm, y, f"Certificate No: {cert_no}")
    c.drawRightString(w - 35*mm, y, f"Date: {datetime.now().strftime('%d %B %Y')}")

    y -= 15*mm
    fields = [
        ("Donor Name", donation.get("name", "")),
        ("PAN Number", donation.get("pan_number", "")),
        ("Aadhaar Number", donation.get("aadhaar_number", "") or "N/A"),
        ("Address", donation.get("address", "") or "N/A"),
        ("Phone", donation.get("phone", "")),
        ("Email", donation.get("email", "")),
        ("Donation Amount", f"\u20B9 {donation.get('amount', 0):,}"),
        ("Donation Date", donation.get("created_at", "")[:10]),
        ("Payment Status", donation.get("status", "pending").capitalize()),
    ]
    for label, value in fields:
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(navy)
        c.drawString(35*mm, y, f"{label}:")
        c.setFont("Helvetica", 9)
        c.setFillColor(dark)
        val_str = str(value)
        if len(val_str) > 70:
            val_str = val_str[:70] + "..."
        c.drawString(80*mm, y, val_str)
        y -= 7*mm

    y -= 8*mm
    c.setStrokeColor(sky)
    c.setLineWidth(0.5)
    c.line(35*mm, y, w - 35*mm, y)
    y -= 8*mm

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(dark)
    c.drawCentredString(w/2, y, "IMPORTANT NOTICE")
    y -= 6*mm
    style = ParagraphStyle("notice", fontName="Helvetica", fontSize=8, leading=11, textColor=gray, alignment=TA_LEFT)
    notice_text = (
        "This is a <b>Provisional Donation Receipt</b> issued by Heroic HIFI Foundation. "
        "As per the applicable provisions, this provisional certificate entitles the donor to claim a <b>50% tax rebate/deduction</b> "
        "on the donated amount under Section 80G of the Income Tax Act, 1961. "
        "This certificate is subject to the final approval and issuance of the regular 80G certificate by the Income Tax Department. "
        "The donor is advised to retain this receipt for their tax records."
    )
    p = Paragraph(notice_text, style)
    pw, ph = p.wrap(w - 70*mm, 100*mm)
    p.drawOn(c, 35*mm, y - ph)
    y -= ph + 15*mm

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(navy)
    c.drawString(35*mm, y, "For Heroic HIFI Foundation")
    y -= 12*mm
    c.setFont("Helvetica", 8)
    c.setFillColor(dark)
    c.drawString(35*mm, y, "Authorised Signatory")
    c.drawRightString(w - 35*mm, y, "Email: hhf.hifi@proton.me | Phone: (+91) 7970976881")

    c.save()
    buf.seek(0)
    return buf.read()

@api_router.get("/donations/{donation_id}/certificate")
async def download_80g_certificate(donation_id: str):
    donation = await db.donations.find_one({"id": donation_id}, {"_id": 0})
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    if not donation.get("pan_number"):
        raise HTTPException(status_code=400, detail="PAN number is required for 80G certificate")
    pdf_bytes = generate_80g_pdf(donation)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=HHF_80G_{donation_id[:8]}.pdf"}
    )

# ── Volunteers Routes ──
@api_router.post("/volunteers")
async def register_volunteer(data: VolunteerInput, request: Request):
    doc = {
        "id": str(uuid.uuid4()), "name": data.name, "email": data.email.lower().strip(),
        "phone": data.phone, "city": data.city, "interests": data.interests,
        "message": data.message, "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.volunteers.insert_one(doc)
    doc.pop("_id", None)
    await log_activity("volunteer_registered", "volunteer", doc["id"], data.email, f"City: {data.city}", request.client.host if request.client else "")
    return {"message": "Thank you for registering as a volunteer! We will get back to you shortly.", "volunteer": doc}

# ── Queries Routes ──
@api_router.post("/queries")
async def submit_query(data: QueryInput, request: Request):
    doc = {
        "id": str(uuid.uuid4()), "name": data.name, "email": data.email.lower().strip(),
        "mission": data.mission, "subject": data.subject, "message": data.message,
        "status": "open", "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.queries.insert_one(doc)
    doc.pop("_id", None)
    await log_activity("query_submitted", "query", doc["id"], data.email, f"Mission: {data.mission}", request.client.host if request.client else "")
    return {"message": "Your query has been submitted successfully.", "query": doc}

# ── Admin Routes ──
@api_router.get("/admin/stats")
async def admin_stats(user: dict = Depends(require_admin)):
    total_donations = await db.donations.count_documents({})
    agg = await db.donations.aggregate([{"$group": {"_id": None, "total": {"$sum": "$amount"}}}]).to_list(1)
    total_amount = agg[0]["total"] if agg else 0
    confirmed = await db.donations.count_documents({"status": "confirmed"})
    total_vol = await db.volunteers.count_documents({})
    approved_vol = await db.volunteers.count_documents({"status": "approved"})
    total_q = await db.queries.count_documents({})
    open_q = await db.queries.count_documents({"status": "open"})
    total_users = await db.users.count_documents({})
    return {
        "donations": {"total": total_donations, "confirmed": confirmed, "total_amount": total_amount},
        "volunteers": {"total": total_vol, "approved": approved_vol},
        "queries": {"total": total_q, "open": open_q},
        "users": {"total": total_users},
    }

@api_router.get("/admin/donations")
async def admin_list_donations(user: dict = Depends(require_admin)):
    return await db.donations.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)

@api_router.put("/admin/donations/{item_id}/status")
async def admin_update_donation_status(item_id: str, data: StatusUpdate, user: dict = Depends(require_admin), request: Request = None):
    result = await db.donations.update_one({"id": item_id}, {"$set": {"status": data.status}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Donation not found")
    await log_activity("donation_status_updated", "donation", item_id, user["email"], f"Status -> {data.status}", "")
    return {"message": "Status updated", "status": data.status}

@api_router.get("/admin/volunteers")
async def admin_list_volunteers(user: dict = Depends(require_admin)):
    return await db.volunteers.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)

@api_router.put("/admin/volunteers/{item_id}/status")
async def admin_update_volunteer_status(item_id: str, data: StatusUpdate, user: dict = Depends(require_admin)):
    result = await db.volunteers.update_one({"id": item_id}, {"$set": {"status": data.status}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    await log_activity("volunteer_status_updated", "volunteer", item_id, user["email"], f"Status -> {data.status}", "")
    return {"message": "Status updated", "status": data.status}

@api_router.get("/admin/queries")
async def admin_list_queries(user: dict = Depends(require_admin)):
    return await db.queries.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)

@api_router.put("/admin/queries/{item_id}/status")
async def admin_update_query_status(item_id: str, data: StatusUpdate, user: dict = Depends(require_admin)):
    result = await db.queries.update_one({"id": item_id}, {"$set": {"status": data.status}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Query not found")
    await log_activity("query_status_updated", "query", item_id, user["email"], f"Status -> {data.status}", "")
    return {"message": "Status updated", "status": data.status}

@api_router.get("/admin/users")
async def admin_list_users(user: dict = Depends(require_admin)):
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).sort("created_at", -1).to_list(500)
    # Add string id from email for identification
    return users

@api_router.delete("/admin/users/{user_email}")
async def admin_delete_user(user_email: str, user: dict = Depends(require_admin)):
    email = user_email.lower().strip()
    if email == user["email"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    result = await db.users.delete_one({"email": email})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    await log_activity("user_deleted", "user", email, user["email"], f"Deleted user: {email}", "")
    return {"message": f"User {email} deleted successfully"}

# ── Directory (public members list) ──
@api_router.get("/directory")
async def get_directory(user: dict = Depends(get_current_user)):
    members = await db.users.find(
        {"role": {"$ne": "admin"}},
        {"_id": 0, "password_hash": 0, "pan_number": 0, "aadhaar_number": 0, "address": 0, "dob": 0, "age": 0}
    ).sort("created_at", -1).to_list(500)
    return members

# ── Messaging ──
class MessageInput(BaseModel):
    recipient_email: str
    message: str

@api_router.post("/messages")
async def send_message(data: MessageInput, request: Request, user: dict = Depends(get_current_user)):
    recipient = await db.users.find_one({"email": data.recipient_email.lower().strip()})
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    if data.recipient_email.lower().strip() == user["email"]:
        raise HTTPException(status_code=400, detail="Cannot send message to yourself")
    doc = {
        "id": str(uuid.uuid4()),
        "sender_email": user["email"],
        "sender_name": user.get("name", ""),
        "recipient_email": data.recipient_email.lower().strip(),
        "recipient_name": recipient.get("name", ""),
        "message": data.message,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.messages.insert_one(doc)
    doc.pop("_id", None)
    await log_activity("message_sent", "message", doc["id"], user["email"], f"To: {data.recipient_email}", request.client.host if request.client else "")
    return {"message": "Message sent successfully", "data": doc}

@api_router.get("/messages/conversations")
async def get_conversations(user: dict = Depends(get_current_user)):
    email = user["email"]
    pipeline = [
        {"$match": {"$or": [{"sender_email": email}, {"recipient_email": email}]}},
        {"$sort": {"created_at": -1}},
        {"$group": {
            "_id": {"$cond": [{"$eq": ["$sender_email", email]}, "$recipient_email", "$sender_email"]},
            "last_message": {"$first": "$message"},
            "last_time": {"$first": "$created_at"},
            "other_name": {"$first": {"$cond": [{"$eq": ["$sender_email", email]}, "$recipient_name", "$sender_name"]}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"last_time": -1}},
        {"$project": {"_id": 0, "email": "$_id", "name": "$other_name", "last_message": 1, "last_time": 1, "count": 1}}
    ]
    convos = await db.messages.aggregate(pipeline).to_list(100)
    for c in convos:
        c["last_message_preview"] = strip_numbers(c["last_message"])[:80] if c.get("last_message") else ""
    return convos

@api_router.get("/messages/thread/{other_email}")
async def get_thread(other_email: str, user: dict = Depends(get_current_user)):
    email = user["email"]
    other = other_email.lower().strip()
    msgs = await db.messages.find(
        {"$or": [
            {"sender_email": email, "recipient_email": other},
            {"sender_email": other, "recipient_email": email}
        ]},
        {"_id": 0}
    ).sort("created_at", 1).to_list(500)
    for m in msgs:
        if m["recipient_email"] == email:
            m["message"] = strip_numbers(m["message"])
    return msgs

# ── Admin Messages ──
@api_router.get("/admin/messages")
async def admin_list_conversations(user: dict = Depends(require_admin)):
    pipeline = [
        {"$sort": {"created_at": -1}},
        {"$group": {
            "_id": {
                "pair": {"$cond": [
                    {"$lt": ["$sender_email", "$recipient_email"]},
                    {"$concat": ["$sender_email", "||", "$recipient_email"]},
                    {"$concat": ["$recipient_email", "||", "$sender_email"]}
                ]}
            },
            "last_message": {"$first": "$message"},
            "last_time": {"$first": "$created_at"},
            "sender": {"$first": "$sender_name"},
            "recipient": {"$first": "$recipient_name"},
            "sender_email": {"$first": "$sender_email"},
            "recipient_email": {"$first": "$recipient_email"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"last_time": -1}},
        {"$project": {"_id": 0, "pair": "$_id.pair", "last_message": 1, "last_time": 1, "sender": 1, "recipient": 1, "sender_email": 1, "recipient_email": 1, "count": 1}}
    ]
    return await db.messages.aggregate(pipeline).to_list(200)

@api_router.get("/admin/messages/thread/{email1}/{email2}")
async def admin_get_thread(email1: str, email2: str, user: dict = Depends(require_admin)):
    e1, e2 = email1.lower().strip(), email2.lower().strip()
    msgs = await db.messages.find(
        {"$or": [
            {"sender_email": e1, "recipient_email": e2},
            {"sender_email": e2, "recipient_email": e1}
        ]},
        {"_id": 0}
    ).sort("created_at", 1).to_list(500)
    return msgs

# ── Health ──
@api_router.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.otp_tokens.create_index("expires_at", expireAfterSeconds=0)
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@heroichifi.org")
    admin_password = os.environ.get("ADMIN_PASSWORD", "HHF@admin2024")
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        await db.users.insert_one({
            "email": admin_email, "password_hash": hash_password(admin_password),
            "name": "Admin", "role": "admin", "email_verified": True,
            "phone": "(+91) 7970976881", "pan_number": "", "aadhaar_number": "",
            "address": "", "age": None, "dob": "",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Admin seeded: {admin_email}")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})
    creds_path = Path("/app/memory/test_credentials.md")
    creds_path.parent.mkdir(parents=True, exist_ok=True)
    creds_path.write_text(f"# Test Credentials\n\n## Admin\n- Email: {admin_email}\n- Password: {admin_password}\n- Role: admin\n")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
