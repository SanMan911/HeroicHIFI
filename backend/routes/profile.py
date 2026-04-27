from fastapi import APIRouter, HTTPException, Request, Depends, File, UploadFile, Query, Response
import uuid
import jwt as pyjwt
from config import db, get_jwt_secret, JWT_ALGORITHM
from utils.auth import get_current_user
from utils.storage import put_object, get_object, APP_NAME
from utils.badges import compute_auto_badges
from utils.activity import log_activity
from models.schemas import ProfileUpdate
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


@router.get("/profile")
async def get_profile(user: dict = Depends(get_current_user)):
    email = user["email"]
    auto_badges, total_donated = await compute_auto_badges(user)
    current_badges = list(set(user.get("badges", []) + auto_badges))
    if set(current_badges) != set(user.get("badges", [])):
        await db.users.update_one({"email": email}, {"$set": {"badges": current_badges}})
    return {
        "name": user.get("name", ""), "email": email, "phone": user.get("phone", ""),
        "address": user.get("address", ""), "role": user.get("role", "volunteer"),
        "volunteer_hours": user.get("volunteer_hours", 0),
        "badges": current_badges, "total_donated": total_donated,
        "profile_pic_path": user.get("profile_pic_path", ""),
        "pan_number": user.get("pan_number", ""), "aadhaar_number": user.get("aadhaar_number", ""),
        "age": user.get("age"), "dob": user.get("dob", ""),
        "status": user.get("status", "active"),
        "pan_verified": user.get("pan_verified", False),
        "aadhaar_verified": user.get("aadhaar_verified", False),
        "created_at": user.get("created_at", ""),
    }


@router.put("/profile")
async def update_profile(data: ProfileUpdate, user: dict = Depends(get_current_user)):
    updates = {}
    if data.name is not None:
        updates["name"] = data.name
    if data.phone is not None:
        updates["phone"] = data.phone
    if data.address is not None:
        updates["address"] = data.address
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    await db.users.update_one({"email": user["email"]}, {"$set": updates})
    return {"message": "Profile updated successfully"}


@router.post("/profile/upload-pic")
async def upload_profile_pic(user: dict = Depends(get_current_user), file: UploadFile = File(...)):
    allowed = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP, and GIF images are allowed.")
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum 5MB.")
    ext = file.filename.split(".")[-1] if "." in file.filename else "png"
    path = f"{APP_NAME}/profiles/{user['_id']}/{uuid.uuid4()}.{ext}"
    try:
        result = put_object(path, data, file.content_type)
        stored_path = result.get("path", path)
        await db.users.update_one({"email": user["email"]}, {"$set": {"profile_pic_path": stored_path}})
        return {"message": "Profile picture uploaded", "path": stored_path}
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload image")


@router.get("/files/{path:path}")
async def serve_file(path: str, auth: str = Query(None), request: Request = None):
    auth_header = ""
    if request:
        auth_header = request.headers.get("Authorization", "")
    token = auth_header[7:] if auth_header.startswith("Bearer ") else auth
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        pyjwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        file_data, content_type = get_object(path)
        return Response(content=file_data, media_type=content_type)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
