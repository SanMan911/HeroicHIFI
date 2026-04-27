"""
Razorpay Subscriptions API routes — recurring donations.

Architecture is fully wired up. Until real plan IDs are set in .env
(RAZORPAY_PLAN_MONTHLY / RAZORPAY_PLAN_QUARTERLY), the endpoints return
placeholder responses so the frontend can be developed and tested.

Endpoints:
  POST /api/subscriptions/create        - donor creates a subscription
  GET  /api/subscriptions/mine          - donor lists their own subscriptions
  POST /api/subscriptions/{id}/cancel   - donor cancels their subscription
  GET  /api/admin/subscriptions         - admin lists ALL subscriptions
  POST /api/subscriptions/webhook       - Razorpay webhook (subscription.charged etc.)
"""
import uuid
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, Depends

from config import db
from models.schemas import SubscriptionInput
from utils.auth import get_current_user, require_admin
from utils.activity import log_activity
from utils.razorpay_subs import create_subscription, cancel_subscription, verify_webhook_signature

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


@router.post("/subscriptions/create")
async def subscription_create(data: SubscriptionInput, request: Request, user: dict = Depends(get_current_user)):
    if data.plan not in ("monthly", "quarterly"):
        raise HTTPException(status_code=400, detail="Plan must be 'monthly' or 'quarterly'")
    if data.amount < 100:
        raise HTTPException(status_code=400, detail="Minimum recurring amount is ₹100")

    rz = await create_subscription(data.plan, data.amount, {
        "name": data.name, "email": data.email, "pan_number": data.pan_number,
    })

    sub_doc = {
        "id": str(uuid.uuid4()),
        "razorpay_subscription_id": rz["subscription_id"],
        "plan": data.plan,
        "plan_id": rz.get("plan_id", ""),
        "amount": data.amount,
        "name": data.name,
        "email": data.email.lower().strip(),
        "phone": data.phone,
        "pan_number": data.pan_number,
        "address": data.address or "",
        "status": rz["status"],
        "mode": rz["mode"],
        "short_url": rz.get("short_url", ""),
        "user_email": user["email"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "cancelled_at": None,
    }
    await db.subscriptions.insert_one(sub_doc)
    sub_doc.pop("_id", None)
    await log_activity("subscription_created", "subscription", sub_doc["id"], user["email"],
                       f"{data.plan} ₹{data.amount} ({rz['mode']})", request.client.host if request.client else "")
    return {
        "subscription": sub_doc,
        "razorpay_subscription_id": rz["subscription_id"],
        "razorpay_key": rz.get("key_id", ""),
        "short_url": rz.get("short_url", ""),
        "mode": rz["mode"],
        "note": rz.get("note", ""),
    }


@router.get("/subscriptions/mine")
async def subscription_mine(user: dict = Depends(get_current_user)):
    return await db.subscriptions.find({"user_email": user["email"]}, {"_id": 0}).sort("created_at", -1).to_list(50)


@router.post("/subscriptions/{sub_id}/cancel")
async def subscription_cancel(sub_id: str, user: dict = Depends(get_current_user)):
    sub = await db.subscriptions.find_one({"id": sub_id, "user_email": user["email"]})
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    rz_id = sub.get("razorpay_subscription_id", "")
    result = await cancel_subscription(rz_id) if rz_id and not rz_id.startswith("sub_PENDING") else {"cancelled": True, "status": "cancelled_local"}
    await db.subscriptions.update_one({"id": sub_id}, {"$set": {
        "status": "cancelled", "cancelled_at": datetime.now(timezone.utc).isoformat()
    }})
    await log_activity("subscription_cancelled", "subscription", sub_id, user["email"], result["status"], "")
    return {"message": "Subscription cancelled", "result": result}


@router.get("/admin/subscriptions")
async def admin_list_subscriptions(admin: dict = Depends(require_admin)):
    return await db.subscriptions.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)


@router.post("/subscriptions/webhook")
async def subscription_webhook(request: Request):
    """Razorpay webhook — signature verified, event recorded."""
    body = await request.body()
    sig = request.headers.get("x-razorpay-signature", "")
    valid = verify_webhook_signature(body, sig)
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    event = payload.get("event", "unknown")
    await db.webhook_events.insert_one({
        "id": str(uuid.uuid4()), "source": "razorpay", "event": event,
        "verified": valid, "payload": payload,
        "received_at": datetime.now(timezone.utc).isoformat(),
    })
    if not valid:
        # Don't 401 — Razorpay retries; just log and ack
        logger.warning(f"Razorpay webhook signature failed for event {event}")
        return {"status": "received", "verified": False}
    # On subscription.charged, record a donation entry
    if event == "subscription.charged":
        sub_entity = payload.get("payload", {}).get("subscription", {}).get("entity", {})
        pay_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        sub_id = sub_entity.get("id", "")
        amount = (pay_entity.get("amount", 0) or 0) // 100
        sub_doc = await db.subscriptions.find_one({"razorpay_subscription_id": sub_id})
        if sub_doc:
            await db.donations.insert_one({
                "id": str(uuid.uuid4()), "name": sub_doc["name"], "email": sub_doc["email"],
                "phone": sub_doc.get("phone", ""), "amount": amount, "pan_number": sub_doc.get("pan_number", ""),
                "aadhaar_number": "", "address": sub_doc.get("address", ""),
                "message": f"Recurring {sub_doc['plan']} donation",
                "status": "confirmed", "razorpay_payment_id": pay_entity.get("id", ""),
                "subscription_id": sub_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
    return {"status": "ok", "verified": True, "event": event}
