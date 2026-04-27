from fastapi import APIRouter, HTTPException, Request, Depends
import uuid
from datetime import datetime, timezone

from config import db
from models.schemas import MessageInput
from utils.auth import get_current_user, require_admin
from utils.privacy import strip_numbers
from utils.activity import log_activity

router = APIRouter(prefix="/api")


@router.post("/messages")
async def send_message(data: MessageInput, request: Request, user: dict = Depends(get_current_user)):
    recipient = await db.users.find_one({"email": data.recipient_email.lower().strip()})
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    if data.recipient_email.lower().strip() == user["email"]:
        raise HTTPException(status_code=400, detail="Cannot send message to yourself")
    doc = {
        "id": str(uuid.uuid4()),
        "sender_email": user["email"], "sender_name": user.get("name", ""),
        "recipient_email": data.recipient_email.lower().strip(),
        "recipient_name": recipient.get("name", ""),
        "message": data.message,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.messages.insert_one(doc)
    doc.pop("_id", None)
    await log_activity("message_sent", "message", doc["id"], user["email"], f"To: {data.recipient_email}", request.client.host if request.client else "")
    return {"message": "Message sent successfully", "data": doc}


@router.get("/messages/conversations")
async def get_conversations(user: dict = Depends(get_current_user)):
    email = user["email"]
    pipeline = [
        {"$match": {"$or": [{"sender_email": email}, {"recipient_email": email}]}},
        {"$sort": {"created_at": -1}},
        {"$group": {
            "_id": {"$cond": [{"$eq": ["$sender_email", email]}, "$recipient_email", "$sender_email"]},
            "last_message": {"$first": "$message"}, "last_time": {"$first": "$created_at"},
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


@router.get("/messages/thread/{other_email}")
async def get_thread(other_email: str, user: dict = Depends(get_current_user)):
    email = user["email"]
    other = other_email.lower().strip()
    msgs = await db.messages.find(
        {"$or": [{"sender_email": email, "recipient_email": other}, {"sender_email": other, "recipient_email": email}]},
        {"_id": 0}
    ).sort("created_at", 1).to_list(500)
    for m in msgs:
        if m["recipient_email"] == email:
            m["message"] = strip_numbers(m["message"])
    return msgs


@router.get("/admin/messages")
async def admin_list_conversations(user: dict = Depends(require_admin)):
    pipeline = [
        {"$sort": {"created_at": -1}},
        {"$group": {
            "_id": {"pair": {"$cond": [{"$lt": ["$sender_email", "$recipient_email"]}, {"$concat": ["$sender_email", "||", "$recipient_email"]}, {"$concat": ["$recipient_email", "||", "$sender_email"]}]}},
            "last_message": {"$first": "$message"}, "last_time": {"$first": "$created_at"},
            "sender": {"$first": "$sender_name"}, "recipient": {"$first": "$recipient_name"},
            "sender_email": {"$first": "$sender_email"}, "recipient_email": {"$first": "$recipient_email"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"last_time": -1}},
        {"$project": {"_id": 0, "pair": "$_id.pair", "last_message": 1, "last_time": 1, "sender": 1, "recipient": 1, "sender_email": 1, "recipient_email": 1, "count": 1}}
    ]
    return await db.messages.aggregate(pipeline).to_list(200)


@router.get("/admin/messages/thread/{email1}/{email2}")
async def admin_get_thread(email1: str, email2: str, user: dict = Depends(require_admin)):
    e1, e2 = email1.lower().strip(), email2.lower().strip()
    return await db.messages.find(
        {"$or": [{"sender_email": e1, "recipient_email": e2}, {"sender_email": e2, "recipient_email": e1}]},
        {"_id": 0}
    ).sort("created_at", 1).to_list(500)
