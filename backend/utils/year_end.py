"""
Year-end consolidated 80G certificate dispatch.

LEGAL document — sent on 1 April for the prior FY (1 Apr → 31 Mar IST).
Idempotent: each (email, fy_label) pair is sent only once, tracked in
db.consolidated_certificates. Donors who receive nothing for a given FY
(zero confirmed donations) are skipped.

Triggered by:
  - Background daemon (server.py startup) — checks daily, fires on April 1 IST.
  - Admin endpoint /api/admin/annual-80g/send — manual trigger / dry-run.
"""
import asyncio
import logging
import uuid
from datetime import datetime, date, timedelta, timezone

from config import db
from routes.certificates import generate_consolidated_80g_pdf, fy_for_date, IST
from utils.email import send_consolidated_80g_email

logger = logging.getLogger(__name__)


async def _aggregate_donor_donations(fy_start: date, fy_end: date):
    """Group confirmed donations by donor email for the given FY range."""
    start_iso = fy_start.isoformat()
    end_iso = (fy_end + timedelta(days=1)).isoformat()  # exclusive upper bound
    pipeline = [
        {"$match": {
            "status": "confirmed",
            "created_at": {"$gte": start_iso, "$lt": end_iso},
            "email": {"$exists": True, "$ne": ""},
        }},
        {"$sort": {"created_at": 1}},
        {"$group": {
            "_id": "$email",
            "donations": {"$push": {
                "id": "$id", "created_at": "$created_at", "amount": "$amount",
                "razorpay_payment_id": "$razorpay_payment_id",
                "subscription_id": "$subscription_id",
                "name": "$name", "pan_number": "$pan_number", "address": "$address",
            }},
            "total_amount": {"$sum": "$amount"},
            "count": {"$sum": 1},
            "name": {"$last": "$name"},
            "pan_number": {"$last": "$pan_number"},
            "address": {"$last": "$address"},
            "phone": {"$last": "$phone"},
        }},
    ]
    return await db.donations.aggregate(pipeline).to_list(10000)


async def send_consolidated_for_fy(fy_start: date, fy_end: date,
                                   fy_label: str, dry_run: bool = False) -> dict:
    """For the given FY, send each donor a consolidated 80G certificate.
    Idempotent — skips donors already sent for this FY."""
    groups = await _aggregate_donor_donations(fy_start, fy_end)
    sent = 0
    skipped_already_sent = 0
    failed = 0
    skipped_no_pan = 0
    details = []

    for g in groups:
        email = (g["_id"] or "").strip().lower()
        if not email:
            continue
        donor = {
            "email": email,
            "name": g.get("name", ""),
            "pan_number": (g.get("pan_number", "") or "").strip(),
            "address": g.get("address", ""),
            "phone": g.get("phone", ""),
        }

        # Idempotency check
        already = await db.consolidated_certificates.find_one({"email": email, "fy_label": fy_label})
        if already and not dry_run:
            skipped_already_sent += 1
            continue

        if not donor["pan_number"]:
            skipped_no_pan += 1
            details.append({"email": email, "status": "skipped_no_pan", "total": g["total_amount"]})
            continue

        if dry_run:
            details.append({
                "email": email, "status": "dry_run",
                "total": g["total_amount"], "donations": g["count"],
            })
            continue

        try:
            pdf = generate_consolidated_80g_pdf(
                donor, g["donations"], fy_label, fy_start, fy_end,
            )
            ok = await send_consolidated_80g_email(
                donor, pdf, fy_label, fy_start, fy_end,
                g["total_amount"], g["count"],
            )
            if ok:
                await db.consolidated_certificates.insert_one({
                    "id": str(uuid.uuid4()),
                    "email": email,
                    "fy_label": fy_label,
                    "fy_start": fy_start.isoformat(),
                    "fy_end": fy_end.isoformat(),
                    "total_amount": g["total_amount"],
                    "donation_count": g["count"],
                    "donor_name": donor["name"],
                    "donor_pan": donor["pan_number"],
                    "sent_at": datetime.now(IST).isoformat(),
                })
                sent += 1
                details.append({"email": email, "status": "sent",
                                "total": g["total_amount"], "donations": g["count"]})
            else:
                failed += 1
                details.append({"email": email, "status": "email_failed",
                                "total": g["total_amount"]})
        except Exception as e:
            logger.exception(f"Consolidated 80G generation failed for {email}: {e}")
            failed += 1
            details.append({"email": email, "status": f"error: {e}"})

    return {
        "fy_label": fy_label,
        "donors_total": len(groups),
        "sent": sent,
        "skipped_already_sent": skipped_already_sent,
        "skipped_no_pan": skipped_no_pan,
        "failed": failed,
        "dry_run": dry_run,
        "details": details,
    }


def previous_fy(today: date) -> tuple[date, date, str]:
    """Return (fy_start, fy_end, label) for the FY that just ended.
    If today is in FY YYYY-(YY+1), 'previous FY' is the one whose 31 Mar already passed."""
    if today.month >= 4:
        # We're in current FY (YYYY-04 to YYYY+1-03). Previous FY ended on 31 Mar of `today.year`.
        prev_end = date(today.year, 3, 31)
    else:
        prev_end = date(today.year - 1, 3, 31)
    return fy_for_date(prev_end)


async def annual_dispatch_daemon():
    """Background task: every 12 hours, check if today (IST) is in the 1-7 April
    window and the previous FY hasn't been drafted yet. Creates a DRAFT (not a direct
    dispatch) — a human admin must approve from the dashboard before any emails go out."""
    import uuid as _uuid
    while True:
        try:
            now = datetime.now(IST)
            today = now.date()
            if today.month == 4 and today.day <= 7 and now.hour >= 1:
                fy_start, fy_end, fy_label = previous_fy(today)
                existing_draft = await db.annual_80g_drafts.find_one(
                    {"fy_label": fy_label, "status": {"$in": ["pending", "approved", "dispatched"]}}
                )
                if not existing_draft:
                    logger.info(f"[ANNUAL_80G] Daemon creating draft for FY {fy_label}")
                    preview = await send_consolidated_for_fy(fy_start, fy_end, fy_label, dry_run=True)
                    draft_id = str(_uuid.uuid4())
                    draft_doc = {
                        "id": draft_id,
                        "fy_label": fy_label,
                        "fy_start": fy_start.isoformat(),
                        "fy_end": fy_end.isoformat(),
                        "drafted_by": "system_daemon",
                        "drafted_at": now.isoformat(),
                        "status": "pending",
                        "approved_by": None, "approved_at": None,
                        "rejected_by": None, "rejected_at": None, "rejection_reason": None,
                        "summary": {
                            "donors_total": preview["donors_total"],
                            "would_send": len([d for d in preview["details"] if d["status"] == "dry_run"]),
                            "skipped_already_sent": preview["skipped_already_sent"],
                            "skipped_no_pan": preview["skipped_no_pan"],
                            "total_amount": sum(d.get("total", 0) for d in preview["details"] if d["status"] == "dry_run"),
                        },
                        "preview_details": preview["details"][:50],
                        "dispatch_result": None,
                    }
                    await db.annual_80g_drafts.insert_one(draft_doc)
                    # Notify ALL admins (including the user who set this up)
                    admins = await db.users.find({"role": "admin"}, {"_id": 0, "email": 1}).to_list(50)
                    for a in admins:
                        await db.notifications.insert_one({
                            "id": str(_uuid.uuid4()), "email": a["email"],
                            "message": f"📋 [System] Annual 80G dispatch draft for FY {fy_label} requires admin approval ({draft_doc['summary']['would_send']} donors, ₹{draft_doc['summary']['total_amount']:,}).",
                            "category": "annual_80g_review", "is_read": False,
                            "created_at": now.isoformat(),
                        })
                    logger.info(f"[ANNUAL_80G] Draft {draft_id} created. {len(admins)} admins notified.")
        except Exception:
            logger.exception("Annual 80G daemon iteration failed")
        await asyncio.sleep(12 * 3600)
