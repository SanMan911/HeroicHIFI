from config import db, logger, client
from utils.auth import hash_password, verify_password
from utils.storage import init_storage
from utils.year_end import annual_dispatch_daemon

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from pathlib import Path
import asyncio
import os

from routes.auth import router as auth_router
from routes.donations import router as donations_router
from routes.messages import router as messages_router
from routes.profile import router as profile_router
from routes.admin import router as admin_router
from routes.general import router as general_router
from routes.subscriptions import router as subscriptions_router

app = FastAPI(title="Heroic HIFI Foundation API")

# Include all route modules
app.include_router(auth_router)
app.include_router(donations_router)
app.include_router(messages_router)
app.include_router(profile_router)
app.include_router(admin_router)
app.include_router(general_router)
app.include_router(subscriptions_router)

# Health endpoint
@app.get("/api/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# CORS
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
    await db.password_reset_tokens.create_index("expires_at", expireAfterSeconds=0)
    await db.tickets.create_index("user_email")
    try:
        init_storage()
    except Exception as e:
        logger.warning(f"Storage init on startup: {e}")
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@heroichifi.org")
    admin_password = os.environ.get("ADMIN_PASSWORD", "HHF@admin2024")
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        await db.users.insert_one({
            "email": admin_email, "password_hash": hash_password(admin_password),
            "name": "Admin", "role": "admin", "email_verified": True,
            "phone": "(+91) 7970976881", "pan_number": "", "aadhaar_number": "",
            "address": "", "age": None, "dob": "",
            "pan_verified": False, "aadhaar_verified": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Admin seeded: {admin_email}")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})
    try:
        creds_path = Path("/app/memory/test_credentials.md")
        creds_path.parent.mkdir(parents=True, exist_ok=True)
        creds_path.write_text(f"# Test Credentials\n\n## Admin\n- Email: {admin_email}\n- Password: {admin_password}\n- Role: admin\n")
    except (PermissionError, OSError):
        pass

    # Background daemon: annual 80G consolidated dispatch (idempotent, runs daily)
    asyncio.create_task(annual_dispatch_daemon())
    logger.info("Annual 80G dispatch daemon started")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
