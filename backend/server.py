from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import bcrypt
import jwt
import uuid
import secrets
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from bson import ObjectId

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI(title="Heroic HIFI Foundation API")
api_router = APIRouter(prefix="/api")

# JWT config
JWT_ALGORITHM = "HS256"

def get_jwt_secret():
    return os.environ["JWT_SECRET"]

# Password helpers
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id, "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "type": "access"
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request) -> dict:
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
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

# ── Models ──
class RegisterInput(BaseModel):
    name: str
    email: str
    password: str

class LoginInput(BaseModel):
    email: str
    password: str

class DonationInput(BaseModel):
    name: str
    email: str
    phone: str
    amount: int
    pan_number: Optional[str] = None
    message: Optional[str] = None

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

# ── Auth Routes ──
@api_router.post("/auth/register")
async def register(data: RegisterInput):
    email = data.email.lower().strip()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = hash_password(data.password)
    doc = {
        "name": data.name,
        "email": email,
        "password_hash": hashed,
        "role": "volunteer",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.users.insert_one(doc)
    user_id = str(result.inserted_id)
    token = create_access_token(user_id, email)
    return {"token": token, "user": {"id": user_id, "name": data.name, "email": email, "role": "volunteer"}}

@api_router.post("/auth/login")
async def login(data: LoginInput):
    email = data.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    user_id = str(user["_id"])
    token = create_access_token(user_id, email)
    return {
        "token": token,
        "user": {"id": user_id, "name": user.get("name", ""), "email": email, "role": user.get("role", "volunteer")}
    }

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {"user": user}

@api_router.post("/auth/logout")
async def logout():
    return {"message": "Logged out successfully"}

# ── Missions Routes ──
MISSIONS_DATA = [
    {
        "slug": "mission-shakti",
        "name": "Mission Shakti",
        "name_hi": "मिशन शक्ति",
        "tagline": "Empowering Women, Transforming Communities",
        "tagline_hi": "नारी सशक्तिकरण, समुदाय का कायाकल्प",
        "description": "Mission Shakti is dedicated to empowering women across rural and urban India through skill development, financial literacy, and leadership training. We believe that when women rise, entire communities are uplifted.",
        "description_hi": "मिशन शक्ति ग्रामीण एवं शहरी भारत में कौशल विकास, वित्तीय साक्षरता और नेतृत्व प्रशिक्षण के माध्यम से महिलाओं के सशक्तिकरण हेतु समर्पित है। हमारा विश्वास है कि जब नारी उत्थान होता है, तो पूरा समुदाय ऊपर उठता है।",
        "icon": "Sparkles",
        "color": "#EA580C",
        "image_key": "mission_shakti_women"
    },
    {
        "slug": "mission-swabhiman",
        "name": "Mission Swabhiman",
        "name_hi": "मिशन स्वाभिमान",
        "tagline": "Dignity Through Menstrual Hygiene Awareness",
        "tagline_hi": "मासिक धर्म स्वच्छता जागरूकता द्वारा सम्मान",
        "description": "Mission Swabhiman raises awareness about female menstrual hygiene, breaking taboos and ensuring every woman has access to safe, hygienic products. We conduct workshops in schools, colleges and rural communities.",
        "description_hi": "मिशन स्वाभिमान महिला मासिक धर्म स्वच्छता के बारे में जागरूकता बढ़ाता है, वर्जनाओं को तोड़ता है और सुनिश्चित करता है कि प्रत्येक महिला को सुरक्षित, स्वच्छ उत्पादों तक पहुँच मिले। हम विद्यालयों, महाविद्यालयों और ग्रामीण समुदायों में कार्यशालाएँ आयोजित करते हैं।",
        "icon": "Heart",
        "color": "#DB2777",
        "image_key": "mission_swabhiman_health"
    },
    {
        "slug": "mission-roshni",
        "name": "Mission Roshni",
        "name_hi": "मिशन रोशनी",
        "tagline": "Illuminating Futures Through Education",
        "tagline_hi": "शिक्षा द्वारा भविष्य को रोशन करना",
        "description": "Mission Roshni brings the light of education to children and students from slum areas and underprivileged communities. We provide free tutoring, school supplies, and mentorship to help children dream bigger.",
        "description_hi": "मिशन रोशनी झुग्गी-बस्तियों और वंचित समुदायों के बच्चों एवं विद्यार्थियों तक शिक्षा की ज्योति पहुँचाता है। हम बच्चों को बड़े सपने देखने में सहायता करने हेतु निःशुल्क शिक्षण, विद्यालय सामग्री और मार्गदर्शन प्रदान करते हैं।",
        "icon": "BookOpen",
        "color": "#2563EB",
        "image_key": "mission_roshni_education"
    },
    {
        "slug": "mission-koi-bhookha-na-soye",
        "name": "Mission Koi Bhookha Na Soye",
        "name_hi": "मिशन कोई भूखा न सोए",
        "tagline": "No One Sleeps Hungry",
        "tagline_hi": "कोई भूखा न सोए",
        "description": "This mission collects excess food from hotels, restaurants, weddings, and events, and distributes it among the destitute, homeless, and hungry. We work to ensure that no edible food goes to waste while people go hungry.",
        "description_hi": "यह मिशन होटलों, रेस्तराँओं, विवाहों और आयोजनों से अतिरिक्त भोजन एकत्र करता है और इसे बेसहारा, बेघर और भूखे लोगों में वितरित करता है। हम यह सुनिश्चित करने का प्रयास करते हैं कि कोई भी खाने योग्य भोजन बर्बाद न हो जबकि लोग भूखे रहें।",
        "icon": "UtensilsCrossed",
        "color": "#D97706",
        "image_key": "mission_koibhookhanasoye_food"
    },
    {
        "slug": "mission-paryavaran",
        "name": "Mission Paryavaran",
        "name_hi": "मिशन पर्यावरण",
        "tagline": "Nurturing Nature, Securing Tomorrow",
        "tagline_hi": "प्रकृति का पोषण, कल की सुरक्षा",
        "description": "Mission Paryavaran is committed to raising awareness about the environment and cleanliness. Through tree plantation drives, clean-up campaigns, and educational programs, we strive to create a greener, cleaner world.",
        "description_hi": "मिशन पर्यावरण पर्यावरण एवं स्वच्छता के बारे में जागरूकता बढ़ाने हेतु प्रतिबद्ध है। वृक्षारोपण अभियानों, स्वच्छता अभियानों और शैक्षिक कार्यक्रमों के माध्यम से हम एक हरित, स्वच्छ संसार बनाने का प्रयास करते हैं।",
        "icon": "TreePine",
        "color": "#16A34A",
        "image_key": "mission_paryavaran_environment"
    },
    {
        "slug": "mission-karuna",
        "name": "Mission Karuna",
        "name_hi": "मिशन करुणा",
        "tagline": "Compassion for Every Living Being",
        "tagline_hi": "प्रत्येक प्राणी के प्रति करुणा",
        "description": "Mission Karuna empathizes with voiceless animals. We raise awareness and fight against animal cruelty, conduct rescue operations, and advocate for humane treatment of all animals, strays and domesticated alike.",
        "description_hi": "मिशन करुणा मूक प्राणियों के प्रति सहानुभूति रखता है। हम पशु क्रूरता के विरुद्ध जागरूकता बढ़ाते हैं और लड़ते हैं, बचाव अभियान चलाते हैं, तथा सभी पशुओं—आवारा एवं पालतू दोनों—के मानवीय व्यवहार की पैरवी करते हैं।",
        "icon": "PawPrint",
        "color": "#7C3AED",
        "image_key": "mission_karuna_animals"
    },
    {
        "slug": "mission-paridhan",
        "name": "Mission Paridhan",
        "name_hi": "मिशन परिधान",
        "tagline": "Clothing the Needy, Wrapping with Dignity",
        "tagline_hi": "वस्त्रदान, सम्मान का आवरण",
        "description": "Mission Paridhan collects donated clothes and distributes them among beggars and the needy. Clothing is a basic necessity and through this mission, we aim to restore dignity and provide warmth to the underprivileged.",
        "description_hi": "मिशन परिधान दान में प्राप्त वस्त्रों को एकत्र करता है और उन्हें भिक्षुकों एवं जरूरतमंदों में वितरित करता है। वस्त्र एक मूलभूत आवश्यकता है और इस मिशन के माध्यम से हम वंचितों को सम्मान और ऊष्मा प्रदान करने का लक्ष्य रखते हैं।",
        "icon": "Shirt",
        "color": "#0891B2",
        "image_key": "mission_paridhan_clothes"
    }
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

# ── Donations Routes ──
@api_router.post("/donations")
async def create_donation(data: DonationInput):
    doc = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "email": data.email.lower().strip(),
        "phone": data.phone,
        "amount": data.amount,
        "pan_number": data.pan_number,
        "message": data.message,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.donations.insert_one(doc)
    doc.pop("_id", None)
    return {"message": "Donation recorded successfully. Razorpay payment integration will be activated soon.", "donation": doc}

@api_router.get("/donations")
async def list_donations(user: dict = Depends(get_current_user)):
    donations = await db.donations.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return donations

# ── Volunteers Routes ──
@api_router.post("/volunteers")
async def register_volunteer(data: VolunteerInput):
    doc = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "email": data.email.lower().strip(),
        "phone": data.phone,
        "city": data.city,
        "interests": data.interests,
        "message": data.message,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.volunteers.insert_one(doc)
    doc.pop("_id", None)
    return {"message": "Thank you for registering as a volunteer! We will get back to you shortly.", "volunteer": doc}

# ── Queries Routes ──
@api_router.post("/queries")
async def submit_query(data: QueryInput):
    doc = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "email": data.email.lower().strip(),
        "mission": data.mission,
        "subject": data.subject,
        "message": data.message,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.queries.insert_one(doc)
    doc.pop("_id", None)
    return {"message": "Your query has been submitted successfully. We will respond shortly.", "query": doc}

# ── Health ──
@api_router.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Include router
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    # Seed admin
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@heroichifi.org")
    admin_password = os.environ.get("ADMIN_PASSWORD", "HHF@admin2024")
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        hashed = hash_password(admin_password)
        await db.users.insert_one({
            "email": admin_email,
            "password_hash": hashed,
            "name": "Admin",
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Admin user seeded: {admin_email}")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})
        logger.info("Admin password updated")
    # Write test credentials
    creds_path = Path("/app/memory/test_credentials.md")
    creds_path.parent.mkdir(parents=True, exist_ok=True)
    creds_path.write_text(f"# Test Credentials\n\n## Admin\n- Email: {admin_email}\n- Password: {admin_password}\n- Role: admin\n\n## Auth Endpoints\n- POST /api/auth/login\n- POST /api/auth/register\n- GET /api/auth/me\n- POST /api/auth/logout\n")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
