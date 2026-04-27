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
from utils.razorpay_subs import create_subscription, cancel_subscription, verify_webhook_signature, PLAN_AMOUNTS
from utils.patron import promote_if_qualified, list_patrons, recompute_all, get_patron_summary

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


@router.post("/subscriptions/create")
async def subscription_create(data: SubscriptionInput, request: Request, user: dict = Depends(get_current_user)):
    if data.plan not in PLAN_AMOUNTS:
        raise HTTPException(status_code=400, detail=f"Plan must be one of: {', '.join(PLAN_AMOUNTS.keys())}")
    amount = PLAN_AMOUNTS[data.plan]  # fixed by plan, set in Razorpay dashboard

    rz = await create_subscription(data.plan, amount, {
        "name": data.name, "email": data.email, "pan_number": data.pan_number,
    })

    sub_doc = {
        "id": str(uuid.uuid4()),
        "razorpay_subscription_id": rz["subscription_id"],
        "plan": data.plan,
        "plan_id": rz.get("plan_id", ""),
        "amount": amount,
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
                       f"{data.plan} ₹{amount} ({rz['mode']})", request.client.host if request.client else "")
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
            # Auto-promote to Heroic Patron if threshold reached
            promo = await promote_if_qualified(sub_doc["email"])
            if promo.get("promoted"):
                await log_activity("heroic_patron_promoted", "user", sub_doc["email"], "system",
                                   f"charges={promo['charge_count']} total=₹{promo['total_amount']}", "")
    return {"status": "ok", "verified": True, "event": event}


# ── Heroic Patron — public + admin endpoints ──
@router.get("/heroic-patrons")
async def public_list_patrons(limit: int = 50):
    """Public Wall of Fame patron list — surfaced on /wall-of-fame."""
    return await list_patrons(limit)


@router.get("/admin/patrons/summary/{email}")
async def admin_patron_summary(email: str, admin: dict = Depends(require_admin)):
    return await get_patron_summary(email)


@router.post("/admin/patrons/recompute")
async def admin_recompute_patrons(admin: dict = Depends(require_admin)):
    result = await recompute_all()
    await log_activity("patron_recompute", "system", "", admin["email"],
                       f"checked={result['checked']} promoted={result['promoted']}", "")
    return {"message": f"Recomputed patrons. Checked {result['checked']} subscribers, promoted {result['promoted']}.", **result}


@router.post("/admin/subscriptions/{sub_id}/simulate-charge")
async def admin_simulate_charge(sub_id: str, admin: dict = Depends(require_admin)):
    """Manually record a successful subscription charge — useful while Razorpay
    plans are still placeholders. Mirrors the webhook side-effects."""
    sub = await db.subscriptions.find_one({"id": sub_id})
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    await db.donations.insert_one({
        "id": str(uuid.uuid4()),
        "name": sub.get("name", ""), "email": sub.get("email", ""),
        "phone": sub.get("phone", ""), "amount": sub.get("amount", 0),
        "pan_number": sub.get("pan_number", ""), "aadhaar_number": "",
        "address": sub.get("address", ""),
        "message": f"Simulated recurring {sub.get('plan', '')} charge (admin-triggered)",
        "status": "confirmed",
        "razorpay_payment_id": f"pay_SIM_{uuid.uuid4().hex[:12]}",
        "subscription_id": sub.get("razorpay_subscription_id", sub_id),
        "simulated": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    promo = await promote_if_qualified(sub["email"])
    await log_activity("subscription_charge_simulated", "subscription", sub_id, admin["email"],
                       f"email={sub['email']} amount={sub.get('amount', 0)} promoted={promo.get('promoted', False)}", "")
    return {"message": "Charge simulated.", "patron": promo}
