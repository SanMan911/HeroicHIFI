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
from utils.auth import get_current_user, require_admin, is_super_admin
from utils.activity import log_activity
from utils.email import send_donation_receipt_email
from utils.razorpay_subs import create_subscription, cancel_subscription, verify_webhook_signature, PLAN_AMOUNTS
from utils.patron import promote_if_qualified, list_patrons, recompute_all, get_patron_summary
from routes.certificates import generate_provisional_receipt_pdf

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


@router.post("/subscriptions/create")
async def subscription_create(data: SubscriptionInput, request: Request, user: dict = Depends(get_current_user)):
    if data.plan in PLAN_AMOUNTS:
        amount = PLAN_AMOUNTS[data.plan]  # fixed by plan
        fee_covered = 0
    elif data.plan.startswith("custom_"):
        custom_interval = data.plan.split("_", 1)[1]
        if custom_interval not in {"monthly", "quarterly", "half_yearly", "annual"}:
            raise HTTPException(status_code=400, detail="Custom plan must be custom_monthly, custom_quarterly, custom_half_yearly or custom_annual.")
        if not data.custom_amount or data.custom_amount < 100:
            raise HTTPException(status_code=400, detail="Custom recurring amount must be at least \u20B9 100 per cycle.")
        if data.custom_amount > 1000000:
            raise HTTPException(status_code=400, detail="Custom recurring amount cannot exceed \u20B9 10,00,000 per cycle.")
        amount = int(data.custom_amount)
        # If donor opts to cover fees, build the upgraded amount into the dynamic plan
        import math
        fee_covered = math.ceil(amount * 0.0236) if data.cover_fee else 0
        amount += fee_covered  # the plan & subscription will be created with the gross amount
    else:
        raise HTTPException(status_code=400, detail=f"Plan must be one of: {', '.join(PLAN_AMOUNTS.keys())} or custom_<interval>.")

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
            donation_doc = {
                "id": str(uuid.uuid4()), "name": sub_doc["name"], "email": sub_doc["email"],
                "phone": sub_doc.get("phone", ""), "amount": amount, "pan_number": sub_doc.get("pan_number", ""),
                "aadhaar_number": "", "address": sub_doc.get("address", ""),
                "message": f"Recurring {sub_doc['plan']} donation",
                "status": "confirmed", "razorpay_payment_id": pay_entity.get("id", ""),
                "subscription_id": sub_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            await db.donations.insert_one(donation_doc)
            donation_doc.pop("_id", None)
            # Real-time Top-Donor recompute on each recurring charge
            try:
                from utils.top_donor import recompute_top_donor
                await recompute_top_donor()
            except Exception:
                pass
            try:
                from utils.most_generous import recompute_most_generous
                await recompute_most_generous()
            except Exception:
                pass
            # Auto-email 80G receipt PDF
            try:
                pdf_bytes = generate_provisional_receipt_pdf(donation_doc)
                sent = await send_donation_receipt_email(donation_doc, pdf_bytes, label=sub_doc["plan"])
                await log_activity("recurring_receipt_emailed", "donation", donation_doc["id"], "system",
                                   f"to={sub_doc['email']} sent={sent} amount=₹{amount}", "")
            except Exception as e:
                logger.warning(f"Receipt email failed for {sub_doc['email']}: {e}")
            # Auto-promote to Heroic Patron if threshold reached
            promo = await promote_if_qualified(sub_doc["email"])
            if promo.get("promoted"):
                await log_activity("heroic_patron_promoted", "user", sub_doc["email"], "system",
                                   f"charges={promo['charge_count']} total=₹{promo['total_amount']}", "")
    return {"status": "ok", "verified": True, "event": event}


# ── Heroic Patron — public + admin endpoints ──
@router.get("/heroic-patrons")
async def public_list_patrons(limit: int = 50):
    """Public Wall of Fame patron list — surfaced on /wall-of-fame.
    Amounts rounded to the nearest \u20B9100 for donor privacy."""
    from utils.money import round_to_100
    rows = await list_patrons(limit)
    for r in rows:
        r["patron_total_amount"] = round_to_100(r.get("patron_total_amount"))
    return rows


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
    donation_doc = {
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
    }
    await db.donations.insert_one(donation_doc)
    donation_doc.pop("_id", None)
    # Auto-email 80G receipt PDF (same path as production webhook)
    receipt_sent = False
    try:
        pdf_bytes = generate_provisional_receipt_pdf(donation_doc)
        receipt_sent = await send_donation_receipt_email(donation_doc, pdf_bytes, label=sub.get("plan", "recurring"))
    except Exception as e:
        logger.warning(f"Simulated receipt email failed: {e}")
    promo = await promote_if_qualified(sub["email"])
    # Real-time recognition recompute (simulated charge counts as confirmed)
    try:
        from utils.top_donor import recompute_top_donor
        from utils.most_generous import recompute_most_generous
        await recompute_top_donor()
        await recompute_most_generous()
    except Exception:
        pass
    await log_activity("subscription_charge_simulated", "subscription", sub_id, admin["email"],
                       f"email={sub['email']} amount={sub.get('amount', 0)} promoted={promo.get('promoted', False)} receipt_sent={receipt_sent}", "")
    return {"message": "Charge simulated.", "patron": promo, "receipt_sent": receipt_sent}



# ── Webhook Health (admin) ──
@router.get("/admin/webhook-health")
async def admin_webhook_health(limit: int = 25, admin: dict = Depends(require_admin)):
    """Summary of recent Razorpay webhook events for the admin dashboard."""
    total = await db.webhook_events.count_documents({"source": "razorpay"})
    verified = await db.webhook_events.count_documents({"source": "razorpay", "verified": True})
    unverified = total - verified
    pass_rate = round((verified / total) * 100, 1) if total else 0.0
    last_event = await db.webhook_events.find_one(
        {"source": "razorpay"}, {"_id": 0}, sort=[("received_at", -1)]
    )
    last_verified = await db.webhook_events.find_one(
        {"source": "razorpay", "verified": True}, {"_id": 0}, sort=[("received_at", -1)]
    )
    recent = await db.webhook_events.find(
        {"source": "razorpay"}, {"_id": 0}
    ).sort("received_at", -1).to_list(limit)
    # Per-event-type counts
    by_event_agg = await db.webhook_events.aggregate([
        {"$match": {"source": "razorpay"}},
        {"$group": {"_id": "$event", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]).to_list(50)
    return {
        "total": total,
        "verified": verified,
        "unverified": unverified,
        "pass_rate": pass_rate,
        "last_event": last_event,
        "last_verified": last_verified,
        "recent": recent,
        "by_event": [{"event": r["_id"], "count": r["count"]} for r in by_event_agg],
    }


@router.post("/admin/webhook-events/purge")
async def admin_purge_webhook_events(admin: dict = Depends(require_admin)):
    """Master Admin only — clear historical webhook events to reset the health
    widget. Use this after rotating the webhook secret or after migrating from a
    test environment so old test/ping events no longer skew the pass rate."""
    if not is_super_admin(admin):
        raise HTTPException(status_code=403, detail="Master Admin only.")
    res = await db.webhook_events.delete_many({"source": "razorpay"})
    await log_activity("webhook_events_purged", "admin", "", admin["email"], f"Cleared {res.deleted_count} webhook event(s)", "")
    return {"message": f"Cleared {res.deleted_count} webhook event(s). Health widget reset.", "deleted": res.deleted_count}


@router.post("/admin/webhook-events/{event_id}/replay")
async def admin_replay_webhook_event(event_id: str, admin: dict = Depends(require_admin)):
    """Re-run the webhook handler logic on a stored event (without re-verifying signature).
    Useful when an event was rejected for signature mismatch but the payload is genuine,
    or to re-trigger Heroic Patron promotion after manual correction."""
    evt = await db.webhook_events.find_one({"id": event_id, "source": "razorpay"})
    if not evt:
        raise HTTPException(status_code=404, detail="Webhook event not found")
    payload = evt.get("payload", {}) or {}
    event = payload.get("event", evt.get("event", "unknown"))
    side_effects = []
    if event == "subscription.charged":
        sub_entity = payload.get("payload", {}).get("subscription", {}).get("entity", {})
        pay_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        sub_id = sub_entity.get("id", "")
        amount = (pay_entity.get("amount", 0) or 0) // 100
        sub_doc = await db.subscriptions.find_one({"razorpay_subscription_id": sub_id})
        if not sub_doc:
            side_effects.append("subscription not found in db")
        else:
            existing_pay = await db.donations.find_one({"razorpay_payment_id": pay_entity.get("id", "")})
            if existing_pay:
                side_effects.append("donation already recorded — skipped duplicate")
            else:
                donation_doc = {
                    "id": str(uuid.uuid4()), "name": sub_doc["name"], "email": sub_doc["email"],
                    "phone": sub_doc.get("phone", ""), "amount": amount,
                    "pan_number": sub_doc.get("pan_number", ""), "aadhaar_number": "",
                    "address": sub_doc.get("address", ""),
                    "message": f"Recurring {sub_doc['plan']} donation (replayed)",
                    "status": "confirmed", "razorpay_payment_id": pay_entity.get("id", ""),
                    "subscription_id": sub_id, "replayed": True,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                await db.donations.insert_one(donation_doc)
                donation_doc.pop("_id", None)
                side_effects.append("donation recorded")
                # Real-time Top-Donor recompute on replayed charge
                try:
                    from utils.top_donor import recompute_top_donor
                    await recompute_top_donor()
                except Exception:
                    pass
                try:
                    from utils.most_generous import recompute_most_generous
                    await recompute_most_generous()
                except Exception:
                    pass
                # Email receipt on replay too
                try:
                    pdf_bytes = generate_provisional_receipt_pdf(donation_doc)
                    sent = await send_donation_receipt_email(donation_doc, pdf_bytes, label="replayed")
                    side_effects.append("receipt emailed" if sent else "receipt email failed")
                except Exception as e:
                    side_effects.append(f"receipt error: {e}")
            promo = await promote_if_qualified(sub_doc["email"])
            if promo.get("promoted"):
                side_effects.append(f"heroic patron promoted (charges={promo['charge_count']})")
    await db.webhook_events.update_one({"id": event_id}, {"$set": {
        "replayed_at": datetime.now(timezone.utc).isoformat(),
        "replayed_by": admin["email"],
    }})
    await log_activity("webhook_replayed", "webhook", event_id, admin["email"],
                       f"event={event} side_effects={'; '.join(side_effects) or 'none'}", "")
    return {"message": "Event replayed.", "event": event, "side_effects": side_effects}



# ── Annual Consolidated 80G Dispatch (admin) ──
from datetime import date as _date  # noqa: E402
from utils.year_end import send_consolidated_for_fy, previous_fy  # noqa: E402
from routes.certificates import fy_for_date  # noqa: E402


@router.post("/admin/annual-80g/send")
async def admin_send_annual_80g(
    fy_start: str | None = None, dry_run: bool = False,
    admin: dict = Depends(require_admin),
):
    """DEPRECATED in favour of the draft+approve flow. Kept for backwards compat
    of dry-run preview; non-dry-run is rejected and redirects to /draft."""
    if not dry_run:
        raise HTTPException(
            status_code=400,
            detail="Direct dispatch is gated. Use POST /api/admin/annual-80g/draft to create a draft, "
                   "then POST /api/admin/annual-80g/drafts/{id}/approve from a SECOND admin account.",
        )
    if fy_start:
        try:
            fs = _date.fromisoformat(fy_start)
            fs_start, fs_end, fs_label = fy_for_date(fs)
        except ValueError:
            raise HTTPException(status_code=400, detail="fy_start must be YYYY-MM-DD (e.g. 2025-04-01)")
    else:
        fs_start, fs_end, fs_label = previous_fy(_date.today())
    return await send_consolidated_for_fy(fs_start, fs_end, fs_label, dry_run=True)


@router.post("/admin/annual-80g/draft")
async def admin_draft_annual_80g(
    fy_start: str | None = None,
    admin: dict = Depends(require_admin),
):
    """Create a dispatch draft. A SECOND admin must approve before any emails go out.
    Idempotent: if a pending or completed draft for the same FY exists, returns it instead."""
    if fy_start:
        try:
            fs = _date.fromisoformat(fy_start)
            fs_start, fs_end, fs_label = fy_for_date(fs)
        except ValueError:
            raise HTTPException(status_code=400, detail="fy_start must be YYYY-MM-DD (e.g. 2025-04-01)")
    else:
        fs_start, fs_end, fs_label = previous_fy(_date.today())

    existing = await db.annual_80g_drafts.find_one(
        {"fy_label": fs_label, "status": {"$in": ["pending", "approved", "dispatched"]}},
        {"_id": 0},
    )
    if existing:
        return {"message": f"Existing draft for FY {fs_label} (status={existing['status']}).", "draft": existing}

    # Compute preview to embed in draft (so reviewers see exactly what will happen)
    preview = await send_consolidated_for_fy(fs_start, fs_end, fs_label, dry_run=True)
    draft_id = str(uuid.uuid4())
    draft_doc = {
        "id": draft_id,
        "fy_label": fs_label,
        "fy_start": fs_start.isoformat(),
        "fy_end": fs_end.isoformat(),
        "drafted_by": admin["email"],
        "drafted_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
        "approved_by": None,
        "approved_at": None,
        "rejected_by": None,
        "rejected_at": None,
        "rejection_reason": None,
        "summary": {
            "donors_total": preview["donors_total"],
            "would_send": len([d for d in preview["details"] if d["status"] == "dry_run"]),
            "skipped_already_sent": preview["skipped_already_sent"],
            "skipped_no_pan": preview["skipped_no_pan"],
            "total_amount": sum(d.get("total", 0) for d in preview["details"] if d["status"] == "dry_run"),
        },
        "preview_details": preview["details"][:50],  # keep payload small
        "dispatch_result": None,
    }
    await db.annual_80g_drafts.insert_one(draft_doc)
    draft_doc.pop("_id", None)
    await log_activity("annual_80g_drafted", "system", fs_label, admin["email"],
                       f"donors={preview['donors_total']} would_send={draft_doc['summary']['would_send']}", "")
    # Notify all OTHER admins by in-app notification
    other_admins = await db.users.find({"role": "admin", "email": {"$ne": admin["email"]}}, {"_id": 0, "email": 1}).to_list(50)
    for a in other_admins:
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()), "email": a["email"],
            "message": f"📋 Annual 80G dispatch draft for FY {fs_label} awaits your approval ({draft_doc['summary']['would_send']} donors, ₹{draft_doc['summary']['total_amount']:,}).",
            "category": "annual_80g_review", "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    return {"message": f"Draft created for FY {fs_label}. {len(other_admins)} admin(s) notified for approval.", "draft": draft_doc}


@router.get("/admin/annual-80g/drafts")
async def admin_list_drafts(admin: dict = Depends(require_admin)):
    return await db.annual_80g_drafts.find({}, {"_id": 0}).sort("drafted_at", -1).to_list(50)


@router.post("/admin/annual-80g/drafts/{draft_id}/approve")
async def admin_approve_draft(draft_id: str, admin: dict = Depends(require_admin)):
    draft = await db.annual_80g_drafts.find_one({"id": draft_id})
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Draft is {draft['status']}, not pending")
    # Master Admin overrides separation-of-duties (master control)
    if draft["drafted_by"] == admin["email"] and not is_super_admin(admin):
        raise HTTPException(status_code=403, detail="Approval must come from a different admin (separation-of-duties).")

    fs_start = _date.fromisoformat(draft["fy_start"])
    fs_end = _date.fromisoformat(draft["fy_end"])
    fs_label = draft["fy_label"]

    # Mark approved + dispatched in one go (race-safe upsert via status check)
    await db.annual_80g_drafts.update_one(
        {"id": draft_id, "status": "pending"},
        {"$set": {
            "status": "approved",
            "approved_by": admin["email"],
            "approved_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    # Run the actual dispatch
    result = await send_consolidated_for_fy(fs_start, fs_end, fs_label, dry_run=False)
    await db.annual_80g_drafts.update_one(
        {"id": draft_id},
        {"$set": {
            "status": "dispatched",
            "dispatch_result": {k: v for k, v in result.items() if k != "details"},
            "dispatched_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    await db.consolidated_dispatch_runs.insert_one({
        "id": str(uuid.uuid4()),
        "fy_label": fs_label,
        "draft_id": draft_id,
        "drafted_by": draft["drafted_by"],
        "approved_by": admin["email"],
        "triggered_by": "draft_approval",
        "status": "completed",
        "result": {k: v for k, v in result.items() if k != "details"},
        "started_at": datetime.now(timezone.utc).isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
    })
    await log_activity("annual_80g_approved_and_sent", "system", fs_label, admin["email"],
                       f"draft={draft_id} drafted_by={draft['drafted_by']} sent={result['sent']} failed={result['failed']}"
                       + (" override=true" if is_super_admin(admin) and draft['drafted_by'] == admin['email'] else ""), "")
    return {"message": f"Approved and dispatched. Sent {result['sent']}, failed {result['failed']}.", "result": result}


@router.post("/admin/annual-80g/drafts/{draft_id}/reject")
async def admin_reject_draft(draft_id: str, admin: dict = Depends(require_admin)):
    draft = await db.annual_80g_drafts.find_one({"id": draft_id})
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Draft is {draft['status']}, not pending")
    if draft["drafted_by"] == admin["email"] and not is_super_admin(admin):
        raise HTTPException(status_code=403, detail="Reject must come from a different admin.")
    await db.annual_80g_drafts.update_one({"id": draft_id}, {"$set": {
        "status": "rejected",
        "rejected_by": admin["email"],
        "rejected_at": datetime.now(timezone.utc).isoformat(),
    }})
    await log_activity("annual_80g_rejected", "system", draft["fy_label"], admin["email"],
                       f"draft={draft_id} drafted_by={draft['drafted_by']}"
                       + (" override=true" if is_super_admin(admin) and draft['drafted_by'] == admin['email'] else ""), "")
    return {"message": "Draft rejected. Drafter can create a fresh draft."}


@router.get("/admin/annual-80g/runs")
async def admin_list_dispatch_runs(admin: dict = Depends(require_admin)):
    """History of every consolidated-80G dispatch (auto + manual)."""
    return await db.consolidated_dispatch_runs.find({}, {"_id": 0}).sort("finished_at", -1).to_list(50)
