from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
import io
import csv
import uuid
from datetime import datetime, timezone, date, timedelta

from config import db
from models.schemas import (
    StatusUpdate, AdminUserUpdate, BadgeAction, TicketResponse, DriveInput,
    EmailBlastInput, EventReportInput, AdminPromotionRequest, DeleteUserInput,
    PANVerifyInput, AdminRemovalRequest, EventProposalInput, EventEditInput
)
from utils.auth import require_admin, get_current_user, is_super_admin, super_admin_email
from utils.activity import log_activity
from utils.email import send_email_blast, send_notification_email
from utils.llm import generate_event_article
from utils.sandbox import verify_pan, verify_aadhaar_pan_link
from routes.certificates import generate_agm_report_pdf, fy_for_date

router = APIRouter(prefix="/api")


# ── Admin Donations ──
@router.get("/admin/donations")
async def admin_list_donations(user: dict = Depends(require_admin)):
    return await db.donations.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)


# ── CSV Exports (admin) ──
def _csv_response(rows: list[dict], headers: list[str], filename: str) -> StreamingResponse:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({h: ("" if row.get(h) is None else row.get(h)) for h in headers})
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/admin/export/roster.csv")
async def export_roster_csv(user: dict = Depends(require_admin)):
    """Master Admin and Admin export. Master Admin row hidden from non-master admins."""
    query = {}
    if not is_super_admin(user):
        query["email"] = {"$ne": super_admin_email()}
    rows = await db.users.find(query, {"_id": 0, "password_hash": 0}).sort("created_at", -1).to_list(5000)
    for r in rows:
        r["specializations"] = ", ".join(r.get("specializations", []) or [])
        r["badges"] = ", ".join(r.get("badges", []) or [])
    headers = [
        "name", "email", "phone", "role", "designation", "status",
        "pan_number", "aadhaar_number", "address", "age", "dob",
        "volunteer_hours", "specializations", "badges",
        "pan_verified", "aadhaar_verified", "merchandise_issued",
        "specialization_edits_remaining", "created_at",
    ]
    await log_activity("export_roster_csv", "admin", "", user["email"], f"Exported {len(rows)} roster row(s)", "")
    return _csv_response(rows, headers, f"hhf_roster_{date.today().isoformat()}.csv")


@router.get("/admin/export/donations.csv")
async def export_donations_csv(user: dict = Depends(require_admin)):
    rows = await db.donations.find({}, {"_id": 0}).sort("created_at", -1).to_list(20000)
    for r in rows:
        # Defensive defaults so legacy donations export cleanly
        r.setdefault("fee_covered", 0)
        r.setdefault("gross_amount", r.get("amount", 0))
    headers = [
        "id", "name", "email", "phone", "amount", "fee_covered", "gross_amount",
        "status", "pan_number", "aadhaar_number", "address",
        "razorpay_order_id", "razorpay_payment_id", "subscription_id",
        "message", "created_at",
    ]
    await log_activity("export_donations_csv", "admin", "", user["email"], f"Exported {len(rows)} donation row(s)", "")
    return _csv_response(rows, headers, f"hhf_donations_{date.today().isoformat()}.csv")


@router.get("/admin/export/activity.csv")
async def export_activity_csv(days: int = 90, user: dict = Depends(require_admin)):
    """Recent activity logs (default 90 days). Master Admin's own actions are
    hidden from non-master admins to preserve the hidden-master invariant."""
    since = datetime.now(timezone.utc) - timedelta(days=max(1, min(days, 365)))
    query: dict = {"timestamp": {"$gte": since.isoformat()}}
    if not is_super_admin(user):
        query["user_email"] = {"$ne": super_admin_email()}
    rows = await db.activity_logs.find(query, {"_id": 0}).sort("timestamp", -1).to_list(50000)
    headers = ["timestamp", "action", "entity_type", "entity_id", "user_email", "details", "ip"]
    await log_activity("export_activity_csv", "admin", "", user["email"], f"Exported {len(rows)} activity row(s) (last {days}d)", "")
    return _csv_response(rows, headers, f"hhf_activity_{date.today().isoformat()}.csv")


@router.get("/admin/office-bearer-history")
async def admin_office_bearer_history(user: dict = Depends(require_admin)):
    """Every office-bearer tenure row — open + closed. Ordered by start_date
    desc so the most recent assignment surfaces first. Use at AGMs for a clean
    governance trail."""
    return await db.office_bearer_tenures.find({}, {"_id": 0}).sort("start_date", -1).to_list(500)


@router.get("/admin/agm-report")
async def admin_agm_report(fy_start: str = "", admin: dict = Depends(require_admin)):
    """Download the AGM Governance Report PDF for the given Indian FY.

    - ``fy_start`` format: ``YYYY-MM-DD`` (typically ``YYYY-04-01``). When
      omitted we default to the previous completed FY.
    - Lists every office-bearer tenure whose period overlaps the FY window
      (start_date <= fy_end  AND  (end_date is null OR end_date >= fy_start)).
    """
    today = datetime.now(timezone.utc).date()
    if fy_start:
        try:
            fy_anchor = date.fromisoformat(fy_start.strip()[:10])
        except ValueError:
            raise HTTPException(status_code=400, detail="fy_start must be YYYY-MM-DD")
    else:
        # Default: the FY that ENDED most recently (i.e. previous FY).
        if today.month >= 4:
            fy_anchor = date(today.year - 1, 4, 1)
        else:
            fy_anchor = date(today.year - 2, 4, 1)
    fy_s, fy_e, fy_label = fy_for_date(fy_anchor)
    fy_s_iso, fy_e_iso = fy_s.isoformat(), fy_e.isoformat()
    # Tenures overlapping [fy_s, fy_e]
    cursor = db.office_bearer_tenures.find(
        {
            "start_date": {"$lte": fy_e_iso},
            "$or": [{"end_date": None}, {"end_date": {"$gte": fy_s_iso}}],
        },
        {"_id": 0},
    )
    tenures = await cursor.to_list(500)
    # Sort: Chairman > Secretary > Treasurer > Assistant, then start_date asc
    order = {"Chairman": 0, "Secretary": 1, "Treasurer": 2, "Assistant": 3}
    tenures.sort(key=lambda t: (order.get(t.get("post", ""), 99), t.get("start_date") or ""))
    pdf_bytes = generate_agm_report_pdf(fy_label, fy_s, fy_e, tenures, admin.get("name") or admin.get("email", ""))
    await log_activity("agm_report_downloaded", "report", "", admin["email"], f"FY {fy_label}, {len(tenures)} tenures", "")
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=HHF-AGM-Report-FY{fy_label}.pdf"},
    )


@router.put("/admin/donations/{item_id}/status")
async def admin_update_donation_status(item_id: str, data: StatusUpdate, user: dict = Depends(require_admin)):
    result = await db.donations.update_one({"id": item_id}, {"$set": {"status": data.status}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Donation not found")
    await log_activity("donation_status_updated", "donation", item_id, user["email"], f"Status -> {data.status}", "")
    return {"message": "Status updated", "status": data.status}


@router.post("/admin/donations/purge-all")
async def admin_purge_all_donations(body: dict, request: Request, user: dict = Depends(require_admin)):
    """DESTRUCTIVE: Deletes every donation record. Master-Admin only. Requires
    typed confirmation phrase ``PURGE ALL DONATIONS`` in the body to prevent
    accidental clicks. The wiped documents are archived to ``donations_archive``
    so nothing is ever truly lost."""
    if not is_super_admin(user):
        raise HTTPException(status_code=403, detail="Only the Master Admin may purge donations.")
    if (body or {}).get("confirm") != "PURGE ALL DONATIONS":
        raise HTTPException(status_code=400, detail="Confirmation phrase mismatch. Type 'PURGE ALL DONATIONS' to proceed.")
    count = await db.donations.count_documents({})
    if count == 0:
        return {"message": "No donations to purge.", "deleted": 0}
    # Archive first
    archive_batch_id = str(uuid.uuid4())
    async for doc in db.donations.find({}):
        doc.pop("_id", None)
        doc["archive_batch_id"] = archive_batch_id
        doc["archived_at"] = datetime.now(timezone.utc).isoformat()
        doc["archived_by"] = user["email"]
        await db.donations_archive.insert_one(doc)
    result = await db.donations.delete_many({})
    await log_activity(
        "donations_purged", "donation", archive_batch_id, user["email"],
        f"Master Admin purged {result.deleted_count} donation records (archived in donations_archive)",
        request.client.host if request.client else ""
    )
    return {"message": f"Purged {result.deleted_count} donations (archived).", "deleted": result.deleted_count, "archive_batch_id": archive_batch_id}


# ── Admin Volunteers ──
@router.get("/admin/volunteers")
async def admin_list_volunteers(user: dict = Depends(require_admin)):
    return await db.volunteers.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)


@router.put("/admin/volunteers/{item_id}/status")
async def admin_update_volunteer_status(item_id: str, data: StatusUpdate, user: dict = Depends(require_admin)):
    result = await db.volunteers.update_one({"id": item_id}, {"$set": {"status": data.status}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    await log_activity("volunteer_status_updated", "volunteer", item_id, user["email"], f"Status -> {data.status}", "")
    return {"message": "Status updated", "status": data.status}


# ── Admin Queries ──
@router.get("/admin/queries")
async def admin_list_queries(user: dict = Depends(require_admin)):
    return await db.queries.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)


@router.put("/admin/queries/{item_id}/status")
async def admin_update_query_status(item_id: str, data: StatusUpdate, user: dict = Depends(require_admin)):
    result = await db.queries.update_one({"id": item_id}, {"$set": {"status": data.status}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Query not found")
    await log_activity("query_status_updated", "query", item_id, user["email"], f"Status -> {data.status}", "")
    return {"message": "Status updated", "status": data.status}


@router.put("/admin/queries/{item_id}/respond")
async def admin_respond_to_query(item_id: str, body: dict, admin: dict = Depends(require_admin)):
    """Email a reply to the original visitor and mark the query responded.
    This is the bridge for **anonymous public visitors** — they can't use the
    in-app messaging system because they don't have an account."""
    response_text = (body or {}).get("response", "").strip()
    if len(response_text) < 5:
        raise HTTPException(status_code=400, detail="Please type at least a 5-character reply.")
    q = await db.queries.find_one({"id": item_id}, {"_id": 0})
    if not q:
        raise HTTPException(status_code=404, detail="Query not found")
    if not q.get("email"):
        raise HTTPException(status_code=400, detail="The query has no email address — cannot reply.")
    # Send the reply via the same email pipeline as ticket responses
    from utils.email import send_query_response_email
    sent = await send_query_response_email(q, response_text, admin)
    await db.queries.update_one(
        {"id": item_id},
        {"$set": {
            "status": "responded",
            "admin_response": response_text,
            "responded_by": admin["email"],
            "responded_at": datetime.now(timezone.utc).isoformat(),
            "email_sent": sent,
        }},
    )
    await log_activity("query_responded", "query", item_id, admin["email"], f"Replied via email (sent={sent})", "")
    return {"message": "Reply sent." if sent else "Reply saved (email failed — check Resend logs).", "email_sent": sent}


# ── Admin Users ──
@router.get("/admin/users")
async def admin_list_users(user: dict = Depends(require_admin)):
    # Hide the Master Admin from every other admin
    query = {} if is_super_admin(user) else {"email": {"$ne": super_admin_email()}}
    users = await db.users.find(query, {"_id": 0, "password_hash": 0}).sort("created_at", -1).to_list(500)
    existing_emails = {u["email"] for u in users}
    # Aggregate donation totals per email (all statuses — so guest donors surface even if still pending)
    donation_totals = {}
    donor_meta = {}  # email -> {name, phone, pan_number, address, first_seen, last_seen}
    agg = await db.donations.aggregate([
        {"$group": {
            "_id": "$email",
            "total": {"$sum": {"$cond": [{"$in": ["$status", ["confirmed", "pending"]]}, "$amount", 0]}},
            "name": {"$last": "$name"},
            "phone": {"$last": "$phone"},
            "pan_number": {"$last": "$pan_number"},
            "aadhaar_number": {"$last": "$aadhaar_number"},
            "address": {"$last": "$address"},
            "first_seen": {"$min": "$created_at"},
            "last_seen": {"$max": "$created_at"},
        }}
    ]).to_list(2000)
    for entry in agg:
        email = entry["_id"]
        if not email:
            continue
        donation_totals[email] = entry["total"]
        donor_meta[email] = entry
    for u in users:
        u["total_donated"] = donation_totals.get(u["email"], 0)
        u["is_super_admin"] = is_super_admin(u.get("email", ""))
    # Surface guest donors (exist in donations but never signed up) as synthetic roster entries
    for email, meta in donor_meta.items():
        if email in existing_emails:
            continue
        if email == super_admin_email() and not is_super_admin(user):
            continue
        users.append({
            "email": email,
            "name": meta.get("name") or email.split("@")[0],
            "role": "donor",
            "phone": meta.get("phone") or "",
            "pan_number": meta.get("pan_number") or "",
            "aadhaar_number": meta.get("aadhaar_number") or "",
            "address": meta.get("address") or "",
            "badges": [],
            "volunteer_hours": 0,
            "specializations": [],
            "status": "guest",
            "is_guest_donor": True,
            "created_at": meta.get("first_seen") or "",
            "last_donation_at": meta.get("last_seen") or "",
            "total_donated": meta.get("total", 0),
            "email_verified": False,
            "pan_verified": False,
        })
    return users


@router.put("/admin/users/{user_email}/update")
async def admin_update_user(user_email: str, data: AdminUserUpdate, admin: dict = Depends(require_admin)):
    email = user_email.lower().strip()
    # Master Admin is invisible / immutable to regular admins
    if is_super_admin(email) and not is_super_admin(admin):
        raise HTTPException(status_code=404, detail="User not found")
    target = await db.users.find_one({"email": email})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    updates = {}
    if data.role is not None:
        if data.role == "admin" or target.get("role") == "admin":
            if admin.get("role") != "admin":
                raise HTTPException(status_code=403, detail="Only admins can grant or revoke admin role")
        updates["role"] = data.role
    if data.volunteer_hours is not None:
        updates["volunteer_hours"] = data.volunteer_hours
    if data.merchandise_issued is not None:
        updates["merchandise_issued"] = data.merchandise_issued
    if data.admin_comments is not None:
        updates["admin_comments"] = data.admin_comments
    if data.designation is not None or data.leadership_bio is not None:
        if not is_super_admin(admin):
            raise HTTPException(status_code=403, detail="Only the Master Admin can assign or remove an office-bearer post.")
        if data.designation is not None:
            from data.office_posts import OFFICE_POSTS_SET, UNIQUE_POSTS
            cleaned = data.designation.strip()
            if cleaned and cleaned not in OFFICE_POSTS_SET:
                raise HTTPException(status_code=400, detail=f"'{cleaned}' is not a recognised office-bearer post.")
            # Office-bearer posts apply ONLY to admins. Promote the user first.
            if cleaned and target.get("role") != "admin":
                raise HTTPException(
                    status_code=400,
                    detail=f"Office posts are reserved for admins. Promote {target.get('name') or email} to admin first via the Roster card or the Admins tab.",
                )
            # Enforce single-occupant posts (Chairman / Secretary / Treasurer)
            if cleaned in UNIQUE_POSTS:
                holder = await db.users.find_one(
                    {"designation": cleaned, "email": {"$ne": email}},
                    {"_id": 0, "name": 1, "email": 1},
                )
                if holder:
                    raise HTTPException(
                        status_code=400,
                        detail=f"{cleaned} post is currently held by {holder.get('name') or holder.get('email')}. Clear their post first before assigning it to someone else.",
                    )
            updates["designation"] = cleaned
            # tenure_start mirrored onto user doc for easy read on the roster
            if cleaned:
                updates["tenure_start"] = (data.effective_date or datetime.now(timezone.utc).date().isoformat()).strip()[:10]
            else:
                updates["tenure_start"] = ""
        if data.leadership_bio is not None:
            updates["leadership_bio"] = data.leadership_bio.strip()[:280]
    if data.status is not None:
        updates["status"] = data.status
        if data.status == "suspended":
            if not data.suspension_reason or len(data.suspension_reason.strip()) < 5:
                raise HTTPException(status_code=400, detail="A suspension reason (min 5 chars) is required")
            updates["suspended_until"] = data.suspended_until or ""
            updates["suspension_reason"] = data.suspension_reason.strip()
            updates["suspended_at"] = datetime.now(timezone.utc).isoformat()
            updates["suspended_by"] = admin["email"]
        elif data.status == "active":
            updates["suspended_until"] = None
            updates["suspension_reason"] = ""
            updates["unsuspended_at"] = datetime.now(timezone.utc).isoformat()
            updates["unsuspended_by"] = admin["email"]
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    # Capture old designation BEFORE the update, so we can write a tenure row
    old_designation = (target.get("designation") or "").strip() if "designation" in updates else None
    old_tenure_start = (target.get("tenure_start") or "").strip() if "designation" in updates else None
    await db.users.update_one({"email": email}, {"$set": updates})
    # Track office-bearer tenure periods (immutable history for AGM reports)
    if old_designation is not None and old_designation != updates.get("designation", ""):
        new_designation = updates.get("designation", "") or ""
        effective = (data.effective_date or datetime.now(timezone.utc).date().isoformat()).strip()[:10]
        reason = (data.leadership_bio or "").strip()[:280] or None
        # Close the open tenure row for the OUTGOING post
        if old_designation:
            await db.office_bearer_tenures.update_one(
                {"user_email": email, "post": old_designation, "end_date": None},
                {"$set": {
                    "end_date": effective,
                    "end_reason": reason,
                    "ended_by": admin["email"],
                    "ended_at": datetime.now(timezone.utc).isoformat(),
                }},
            )
        # Open a new tenure row for the INCOMING post
        if new_designation:
            await db.office_bearer_tenures.insert_one({
                "id": str(uuid.uuid4()),
                "user_email": email,
                "user_name": target.get("name", ""),
                "post": new_designation,
                "start_date": effective,
                "end_date": None,
                "start_reason": reason,
                "end_reason": None,
                "started_by": admin["email"],
                "ended_by": None,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "ended_at": None,
            })
        # Lightweight audit entry in the activity log
        await log_activity(
            "office_bearer_changed", "user", email, admin["email"],
            f"{old_designation or '—'} ({old_tenure_start or '—'}) → {new_designation or 'cleared'} (eff. {effective})",
            "",
        )
    changes = ", ".join(f"{k}={v}" for k, v in updates.items())
    await log_activity("admin_user_updated", "user", email, admin["email"], changes, "")
    return {"message": f"User {email} updated successfully"}


@router.delete("/admin/users/{user_email}")
async def admin_delete_user(user_email: str, data: DeleteUserInput, user: dict = Depends(require_admin)):
    email = user_email.lower().strip()
    if email == user["email"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    if is_super_admin(email) and not is_super_admin(user):
        raise HTTPException(status_code=404, detail="User not found")
    if not data.reason or len(data.reason.strip()) < 5:
        raise HTTPException(status_code=400, detail="A removal reason (min 5 chars) is required for audit")
    target = await db.users.find_one({"email": email}, {"_id": 0, "password_hash": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    # Archive before deleting
    await db.deleted_users_archive.insert_one({
        "id": str(uuid.uuid4()),
        "user": target,
        "deleted_by": user["email"],
        "reason": data.reason.strip(),
        "deleted_at": datetime.now(timezone.utc).isoformat(),
    })
    await db.users.delete_one({"email": email})
    await log_activity("user_deleted", "user", email, user["email"], f"Reason: {data.reason.strip()}", "")
    return {"message": f"User {email} removed.", "reason": data.reason.strip()}


# ── PAN-Aadhaar Verification (Sandbox API) ──
@router.post("/admin/users/{user_email}/verify-pan")
async def admin_verify_pan(user_email: str, admin: dict = Depends(require_admin)):
    """Verify PAN of a user using Sandbox API (or stub if placeholder keys)."""
    email = user_email.lower().strip()
    if is_super_admin(email) and not is_super_admin(admin):
        raise HTTPException(status_code=404, detail="User not found")
    target = await db.users.find_one({"email": email})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    pan = target.get("pan_number", "")
    name = target.get("name", "")
    if not pan:
        raise HTTPException(status_code=400, detail="User has no PAN on file")
    result = await verify_pan(pan, name)
    aadhaar = target.get("aadhaar_number", "")
    link_result = None
    if aadhaar:
        link_result = await verify_aadhaar_pan_link(pan, aadhaar)
    await db.users.update_one({"email": email}, {"$set": {
        "pan_verified": result["verified"],
        "pan_verification_status": result["status"],
        "pan_verification_mode": result["mode"],
        "pan_verified_at": datetime.now(timezone.utc).isoformat(),
        "aadhaar_pan_linked": (link_result or {}).get("linked", False),
    }})
    await log_activity("pan_verified", "user", email, admin["email"],
                       f"PAN status={result['status']} mode={result['mode']} link={(link_result or {}).get('status', 'n/a')}", "")
    return {"verified": result["verified"], "status": result["status"], "mode": result["mode"],
            "name_match": result.get("name_match", False), "aadhaar_link": link_result, "raw": result.get("raw", {})}


@router.post("/admin/verify-pan-adhoc")
async def admin_verify_pan_adhoc(data: PANVerifyInput, admin: dict = Depends(require_admin)):
    """Verify any arbitrary PAN/Aadhaar/Name combination without persisting."""
    pan_result = await verify_pan(data.pan, data.name)
    link_result = None
    if data.aadhaar:
        link_result = await verify_aadhaar_pan_link(data.pan, data.aadhaar)
    return {"pan": pan_result, "aadhaar_link": link_result}


# ── Admin Badges ──
@router.post("/admin/users/{user_email}/badge")
async def admin_add_badge(user_email: str, data: BadgeAction, admin: dict = Depends(require_admin)):
    email = user_email.lower().strip()
    if is_super_admin(email) and not is_super_admin(admin):
        raise HTTPException(status_code=404, detail="User not found")
    target = await db.users.find_one({"email": email})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    current_badges = target.get("badges", [])
    if data.badge not in current_badges:
        current_badges.append(data.badge)
        await db.users.update_one({"email": email}, {"$set": {"badges": current_badges}})
    await log_activity("badge_added", "user", email, admin["email"], f"Badge: {data.badge}", "")
    return {"message": f"Badge '{data.badge}' added", "badges": current_badges}


@router.delete("/admin/users/{user_email}/badge/{badge_name}")
async def admin_remove_badge(user_email: str, badge_name: str, admin: dict = Depends(require_admin)):
    email = user_email.lower().strip()
    if is_super_admin(email) and not is_super_admin(admin):
        raise HTTPException(status_code=404, detail="User not found")
    target = await db.users.find_one({"email": email})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    current_badges = [b for b in target.get("badges", []) if b != badge_name]
    await db.users.update_one({"email": email}, {"$set": {"badges": current_badges}})
    await log_activity("badge_removed", "user", email, admin["email"], f"Badge: {badge_name}", "")
    return {"message": f"Badge '{badge_name}' removed", "badges": current_badges}


# ── Admin Stats ──
@router.get("/admin/stats")
async def admin_stats(user: dict = Depends(require_admin)):
    # Filter Master Admin out of counts shown to other admins
    user_filter = {} if is_super_admin(user) else {"email": {"$ne": super_admin_email()}}
    total_donations = await db.donations.count_documents({})
    agg = await db.donations.aggregate([{"$group": {"_id": None, "total": {"$sum": "$amount"}}}]).to_list(1)
    total_amount = agg[0]["total"] if agg else 0
    confirmed = await db.donations.count_documents({"status": "confirmed"})
    total_vol = await db.users.count_documents({"role": "volunteer", **user_filter})
    total_members = await db.users.count_documents({"role": "member", **user_filter})
    total_q = await db.queries.count_documents({})
    open_q = await db.queries.count_documents({"status": "open"})
    total_users = await db.users.count_documents(user_filter)
    total_tickets = await db.tickets.count_documents({})
    open_tickets = await db.tickets.count_documents({"status": "open"})
    pending_role_requests = await db.role_requests.count_documents({"status": "pending"})
    total_drives = await db.drives.count_documents({})
    verified_pan = await db.users.count_documents({"pan_verified": True, **user_filter})
    unverified_pan = await db.users.count_documents({"pan_verified": {"$ne": True}, **user_filter})
    return {
        "donations": {"total": total_donations, "confirmed": confirmed, "total_amount": total_amount},
        "volunteers": {"total": total_vol},
        "members": {"total": total_members},
        "queries": {"total": total_q, "open": open_q},
        "users": {"total": total_users},
        "tickets": {"total": total_tickets, "open": open_tickets},
        "role_requests": {"pending": pending_role_requests},
        "drives": {"total": total_drives},
        "verification": {"pan_verified": verified_pan, "pan_unverified": unverified_pan},
    }


# ── Admin Tickets ──
@router.get("/admin/tickets")
async def admin_list_tickets(user: dict = Depends(require_admin)):
    return await db.tickets.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)


@router.put("/admin/tickets/{ticket_id}/status")
async def admin_update_ticket_status(ticket_id: str, data: StatusUpdate, user: dict = Depends(require_admin)):
    result = await db.tickets.update_one({"id": ticket_id}, {"$set": {"status": data.status, "updated_at": datetime.now(timezone.utc).isoformat()}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ticket not found")
    await log_activity("ticket_status_updated", "ticket", ticket_id, user["email"], f"Status -> {data.status}", "")
    return {"message": "Ticket status updated"}


@router.put("/admin/tickets/{ticket_id}/respond")
async def admin_respond_ticket(ticket_id: str, data: TicketResponse, user: dict = Depends(require_admin)):
    result = await db.tickets.update_one({"id": ticket_id}, {"$set": {"admin_response": data.response, "status": "responded", "updated_at": datetime.now(timezone.utc).isoformat()}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ticket not found")
    await log_activity("ticket_responded", "ticket", ticket_id, user["email"], "Admin responded", "")
    return {"message": "Response sent"}


# ── Admin Role Requests ──
@router.get("/admin/role-requests")
async def admin_list_role_requests(admin: dict = Depends(require_admin)):
    return await db.role_requests.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)


@router.put("/admin/role-requests/{request_id}/approve")
async def admin_approve_role_request(request_id: str, admin: dict = Depends(require_admin), request: Request = None):
    req = await db.role_requests.find_one({"id": request_id, "status": "pending"})
    if not req:
        raise HTTPException(status_code=404, detail="Request not found or already processed")
    await db.users.update_one({"email": req["email"]}, {"$set": {"role": req["requested_role"]}})
    await db.role_requests.update_one({"id": request_id}, {"$set": {"status": "approved", "reviewed_by": admin["email"], "reviewed_at": datetime.now(timezone.utc).isoformat()}})
    await log_activity("role_change_approved", "user", req["email"], admin["email"], f"{req['current_role']} -> {req['requested_role']}", "")
    return {"message": f"Role change approved. {req['name']} is now a {req['requested_role']}."}


@router.put("/admin/role-requests/{request_id}/reject")
async def admin_reject_role_request(request_id: str, admin: dict = Depends(require_admin), request: Request = None):
    req = await db.role_requests.find_one({"id": request_id, "status": "pending"})
    if not req:
        raise HTTPException(status_code=404, detail="Request not found or already processed")
    await db.role_requests.update_one({"id": request_id}, {"$set": {"status": "rejected", "reviewed_by": admin["email"], "reviewed_at": datetime.now(timezone.utc).isoformat()}})
    await log_activity("role_change_rejected", "user", req["email"], admin["email"], f"Rejected: {req['current_role']} -> {req['requested_role']}", "")
    return {"message": "Role change request rejected."}


# ── Admin Drives ──
@router.post("/admin/drives")
async def create_drive(data: DriveInput, admin: dict = Depends(require_admin), request: Request = None):
    doc = {
        "id": str(uuid.uuid4()), "title": data.title, "description": data.description,
        "date": data.date, "location": data.location, "drive_type": data.drive_type,
        "mission_slug": data.mission_slug or "", "estimated_days": data.estimated_days,
        "time": data.time or "", "image_url": data.image_url or "",
        "reported": False, "created_by": admin["email"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.drives.insert_one(doc)
    doc.pop("_id", None)
    await log_activity("drive_created", "drive", doc["id"], admin["email"], f"{data.drive_type}: {data.title}", "")
    return {"message": "Drive created successfully.", "drive": doc}


@router.put("/admin/drives/{drive_id}")
async def update_drive(drive_id: str, data: DriveInput, admin: dict = Depends(require_admin)):
    updates = {"title": data.title, "description": data.description, "date": data.date, "location": data.location, "drive_type": data.drive_type}
    if data.image_url is not None:
        updates["image_url"] = data.image_url
    result = await db.drives.update_one({"id": drive_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Drive not found")
    await log_activity("drive_updated", "drive", drive_id, admin["email"], f"Updated: {data.title}", "")
    return {"message": "Drive updated."}


@router.delete("/admin/drives/{drive_id}")
async def delete_drive(drive_id: str, admin: dict = Depends(require_admin)):
    result = await db.drives.delete_one({"id": drive_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Drive not found")
    await log_activity("drive_deleted", "drive", drive_id, admin["email"], "Drive deleted", "")
    return {"message": "Drive deleted."}


# ── Admin Wall of Fame ──
@router.post("/admin/wall-of-fame/{user_email}")
async def add_to_wall_of_fame(user_email: str, admin: dict = Depends(require_admin)):
    email = user_email.lower().strip()
    target = await db.users.find_one({"email": email})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    existing = await db.wall_of_fame.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="User is already on the Wall of Fame")
    total_agg = await db.donations.aggregate([
        {"$match": {"email": email, "status": {"$in": ["confirmed", "pending"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    total_donated = total_agg[0]["total"] if total_agg else 0
    doc = {
        "email": email, "name": target.get("name", ""), "role": target.get("role", "volunteer"),
        "volunteer_hours": target.get("volunteer_hours", 0), "total_donated": total_donated,
        "badges": target.get("badges", []), "profile_pic_path": target.get("profile_pic_path", ""),
        "contribution_summary": "", "added_by": admin["email"],
        "added_at": datetime.now(timezone.utc).isoformat()
    }
    await db.wall_of_fame.insert_one(doc)
    doc.pop("_id", None)
    await log_activity("wall_of_fame_added", "user", email, admin["email"], "Added to Wall of Fame", "")
    return {"message": f"{target.get('name', email)} added to the Wall of Fame!", "entry": doc}


@router.delete("/admin/wall-of-fame/{user_email}")
async def remove_from_wall_of_fame(user_email: str, admin: dict = Depends(require_admin)):
    email = user_email.lower().strip()
    result = await db.wall_of_fame.delete_one({"email": email})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not on the Wall of Fame")
    await log_activity("wall_of_fame_removed", "user", email, admin["email"], "Removed from Wall of Fame", "")
    return {"message": "Removed from the Wall of Fame"}


@router.put("/admin/wall-of-fame/{user_email}")
async def update_wall_entry(user_email: str, data: dict, admin: dict = Depends(require_admin)):
    email = user_email.lower().strip()
    updates = {}
    if "contribution_summary" in data:
        updates["contribution_summary"] = data["contribution_summary"]
    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update")
    result = await db.wall_of_fame.update_one({"email": email}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not on the Wall of Fame")
    return {"message": "Wall of Fame entry updated"}


# ── Admin Activity Logs ──
async def _archive_old_activity_logs(days: int = 7):
    """Move activity-log rows older than ``days`` to the archive collection.
    Called lazily whenever an admin fetches the live log so we don't need a
    separate cron. Idempotent and safe to call repeatedly."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    cursor = db.activity_logs.find({"timestamp": {"$lt": cutoff}})
    moved = 0
    async for doc in cursor:
        doc.pop("_id", None)
        doc["archived_at"] = datetime.now(timezone.utc).isoformat()
        await db.activity_logs_archive.insert_one(doc)
        moved += 1
    if moved:
        await db.activity_logs.delete_many({"timestamp": {"$lt": cutoff}})
    return moved


@router.get("/admin/activity-logs")
async def admin_activity_logs(limit: int = 100, admin: dict = Depends(require_admin)):
    # Lazy archive — keep the live collection lean (≤ 7 days).
    try:
        await _archive_old_activity_logs(7)
    except Exception:
        pass
    if is_super_admin(admin):
        return await db.activity_logs.find({}, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    # Hide all activity by/about the Master Admin from regular admins
    sa = super_admin_email()
    q = {"$and": [{"user_email": {"$ne": sa}}, {"entity_id": {"$ne": sa}}]}
    return await db.activity_logs.find(q, {"_id": 0}).sort("timestamp", -1).to_list(limit)


@router.get("/admin/activity-logs/archive")
async def admin_activity_logs_archive(limit: int = 200, admin: dict = Depends(require_admin)):
    """Read-only access to the archived (>7 days old) activity rows."""
    if is_super_admin(admin):
        return await db.activity_logs_archive.find({}, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    sa = super_admin_email()
    q = {"$and": [{"user_email": {"$ne": sa}}, {"entity_id": {"$ne": sa}}]}
    return await db.activity_logs_archive.find(q, {"_id": 0}).sort("timestamp", -1).to_list(limit)



# ── Email Blasts ──
@router.post("/admin/email-blast")
async def admin_send_email_blast(data: EmailBlastInput, admin: dict = Depends(require_admin)):
    query = {}
    if data.target == "volunteers":
        query = {"role": "volunteer"}
    elif data.target == "members":
        query = {"role": "member"}
    users = await db.users.find(query, {"email": 1, "_id": 0}).to_list(10000)
    emails = [u["email"] for u in users if u.get("email")]
    if not emails:
        raise HTTPException(status_code=400, detail="No recipients found for the selected target.")
    sent = await send_email_blast(data.subject, data.body, emails)
    await log_activity("email_blast_sent", "email", "", admin["email"], f"Target: {data.target}, Recipients: {len(emails)}, Sent: {sent}, Subject: {data.subject}", "")
    # Log blast record
    await db.email_blasts.insert_one({
        "id": str(uuid.uuid4()), "subject": data.subject, "body": data.body,
        "target": data.target, "recipient_count": len(emails), "sent_count": sent,
        "sent_by": admin["email"], "created_at": datetime.now(timezone.utc).isoformat()
    })
    return {"message": f"Email blast sent to {sent}/{len(emails)} recipients.", "sent": sent, "total": len(emails)}


@router.get("/admin/email-blasts")
async def admin_list_email_blasts(admin: dict = Depends(require_admin)):
    return await db.email_blasts.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)


# ── Event Proposals (Proposer + Seconder + Treasurer approval) ──
async def _treasurer_email() -> str | None:
    u = await db.users.find_one({"designation": "Treasurer"}, {"_id": 0, "email": 1})
    return u["email"] if u else None


@router.post("/admin/events/propose")
async def propose_event(data: EventProposalInput, admin: dict = Depends(require_admin)):
    try:
        date.fromisoformat(data.event_date.strip()[:10])
    except ValueError:
        raise HTTPException(status_code=400, detail="event_date must be YYYY-MM-DD.")
    if data.days < 1:
        raise HTTPException(status_code=400, detail="days must be ≥ 1.")
    if data.budget < 0:
        raise HTTPException(status_code=400, detail="budget cannot be negative.")
    doc = {
        "id": str(uuid.uuid4()),
        "mission": data.mission.strip(),
        "drive_name": data.drive_name.strip(),
        "event_date": data.event_date.strip()[:10],
        "place": data.place.strip(),
        "days": int(data.days),
        "event_time": (data.event_time or "").strip() or None,
        "budget": float(data.budget),
        "notes": (data.notes or "").strip() or None,
        "proposer": admin["email"],
        "proposer_name": admin.get("name", ""),
        "seconder": None, "seconded_at": None,
        "treasurer_decision": None, "treasurer_email": None, "treasurer_at": None, "treasurer_note": None,
        "status": "proposed",
        "delete_request": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.event_proposals.insert_one(doc)
    doc.pop("_id", None)
    await log_activity("event_proposed", "event", doc["id"], admin["email"], f"{doc['drive_name']} on {doc['event_date']}", "")
    return {"message": "Event proposed. Awaiting a seconder.", "event": doc}


@router.put("/admin/events/{event_id}/second")
async def second_event(event_id: str, admin: dict = Depends(require_admin)):
    ev = await db.event_proposals.find_one({"id": event_id})
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    if ev.get("status") != "proposed":
        raise HTTPException(status_code=400, detail=f"Cannot second an event with status '{ev.get('status')}'.")
    if ev.get("proposer") == admin["email"]:
        raise HTTPException(status_code=400, detail="The proposer cannot also second the event.")
    await db.event_proposals.update_one(
        {"id": event_id},
        {"$set": {"seconder": admin["email"],
                  "seconded_at": datetime.now(timezone.utc).isoformat(),
                  "status": "seconded",
                  "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    await log_activity("event_seconded", "event", event_id, admin["email"], f"{ev['drive_name']}", "")
    return {"message": "Event seconded. Awaiting Treasurer approval."}


@router.put("/admin/events/{event_id}/treasurer-decision")
async def treasurer_decision(event_id: str, body: dict, admin: dict = Depends(require_admin)):
    decision = (body or {}).get("decision", "").strip().lower()
    note = (body or {}).get("note", "").strip()
    if decision not in ("approved", "declined"):
        raise HTTPException(status_code=400, detail="decision must be 'approved' or 'declined'.")
    if (admin.get("designation") or "") != "Treasurer" and not is_super_admin(admin):
        raise HTTPException(status_code=403, detail="Only the Treasurer (or Master Admin override) can give the final decision.")
    ev = await db.event_proposals.find_one({"id": event_id})
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    if ev.get("status") != "seconded":
        raise HTTPException(status_code=400, detail=f"Event must be seconded before Treasurer decision (current: {ev.get('status')}).")
    if decision == "declined" and len(note) < 5:
        raise HTTPException(status_code=400, detail="Please provide a note (≥ 5 chars) — required for AGM minutes.")
    new_status = "approved" if decision == "approved" else "declined"
    await db.event_proposals.update_one(
        {"id": event_id},
        {"$set": {"treasurer_decision": decision,
                  "treasurer_email": admin["email"],
                  "treasurer_at": datetime.now(timezone.utc).isoformat(),
                  "treasurer_note": note or None,
                  "status": new_status,
                  "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    await log_activity(f"event_{new_status}", "event", event_id, admin["email"], f"{ev['drive_name']} | budget=₹{ev.get('budget', 0):,.0f}", "")
    return {"message": f"Event {new_status} by Treasurer."}


@router.put("/admin/events/{event_id}/edit")
async def edit_event(event_id: str, data: EventEditInput, admin: dict = Depends(require_admin)):
    ev = await db.event_proposals.find_one({"id": event_id})
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    if ev.get("status") == "deleted":
        raise HTTPException(status_code=400, detail="Cannot edit a deleted event.")
    payload = data.model_dump(exclude_unset=True)
    if not payload:
        raise HTTPException(status_code=400, detail="Nothing to update.")
    if "event_date" in payload and payload["event_date"]:
        try:
            date.fromisoformat(payload["event_date"].strip()[:10])
        except ValueError:
            raise HTTPException(status_code=400, detail="event_date must be YYYY-MM-DD.")
        payload["event_date"] = payload["event_date"].strip()[:10]
    if "days" in payload and payload["days"] is not None and payload["days"] < 1:
        raise HTTPException(status_code=400, detail="days must be ≥ 1.")
    substantive_keys = {"mission", "drive_name", "event_date", "place", "days", "event_time", "budget"}
    is_substantive = bool(substantive_keys & set(payload.keys()))
    payload["updated_at"] = datetime.now(timezone.utc).isoformat()
    revote_triggered = False
    if is_substantive and ev.get("status") in ("seconded", "approved"):
        payload.update({
            "status": "proposed", "seconder": None, "seconded_at": None,
            "treasurer_decision": None, "treasurer_email": None,
            "treasurer_at": None, "treasurer_note": None,
        })
        revote_triggered = True
    await db.event_proposals.update_one({"id": event_id}, {"$set": payload})
    await log_activity("event_edited", "event", event_id, admin["email"], f"Fields: {list(payload.keys())}", "")
    return {"message": "Event updated." + (" Re-seconding & treasurer approval needed." if revote_triggered else ""), "needs_revote": revote_triggered}


@router.post("/admin/events/{event_id}/delete-request")
async def request_event_delete(event_id: str, body: dict, admin: dict = Depends(require_admin)):
    reason = (body or {}).get("reason", "").strip()
    if len(reason) < 5:
        raise HTTPException(status_code=400, detail="A reason of at least 5 characters is required.")
    ev = await db.event_proposals.find_one({"id": event_id})
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    if ev.get("status") == "deleted":
        raise HTTPException(status_code=400, detail="Event is already deleted.")
    if is_super_admin(admin):
        await db.event_proposals.update_one(
            {"id": event_id},
            {"$set": {"status": "deleted", "deleted_by": admin["email"], "deleted_reason": reason,
                      "deleted_at": datetime.now(timezone.utc).isoformat(),
                      "updated_at": datetime.now(timezone.utc).isoformat()}},
        )
        await log_activity("event_deleted", "event", event_id, admin["email"], f"Master-Admin override: {reason}", "")
        return {"message": "Event deleted by Master Admin override."}
    voters = await _regular_admin_emails()
    delete_req = {
        "requested_by": admin["email"], "reason": reason,
        "required_voters": voters, "approvals": [admin["email"]],
        "rejections": [], "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if set(delete_req["approvals"]) >= set(voters):
        await db.event_proposals.update_one(
            {"id": event_id},
            {"$set": {"status": "deleted", "deleted_by": admin["email"], "deleted_reason": reason,
                      "deleted_at": datetime.now(timezone.utc).isoformat(), "delete_request": delete_req,
                      "updated_at": datetime.now(timezone.utc).isoformat()}},
        )
        await log_activity("event_deleted", "event", event_id, admin["email"], f"Unanimous (sole voter): {reason}", "")
        return {"message": "Event deleted (sole regular admin)."}
    await db.event_proposals.update_one({"id": event_id}, {"$set": {"delete_request": delete_req}})
    await log_activity("event_delete_requested", "event", event_id, admin["email"], f"Needs unanimous vote: {reason}", "")
    remaining = len(set(voters) - {admin["email"]})
    return {"message": f"Delete proposal raised. Needs unanimous approval from {remaining} more admin(s)."}


@router.put("/admin/events/{event_id}/delete-vote")
async def vote_event_delete(event_id: str, body: dict, admin: dict = Depends(require_admin)):
    action = (body or {}).get("action", "").strip().lower()
    if action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action must be 'approve' or 'reject'.")
    ev = await db.event_proposals.find_one({"id": event_id})
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    req = ev.get("delete_request")
    if not req:
        raise HTTPException(status_code=400, detail="No active delete request.")
    if ev.get("status") == "deleted":
        raise HTTPException(status_code=400, detail="Event already deleted.")
    voters = set(req.get("required_voters", []))
    if not is_super_admin(admin) and admin["email"] not in voters:
        raise HTTPException(status_code=403, detail="You are not on this delete vote's roster.")
    if action == "reject":
        await db.event_proposals.update_one({"id": event_id}, {"$set": {"delete_request": None, "updated_at": datetime.now(timezone.utc).isoformat()}})
        await log_activity("event_delete_rejected", "event", event_id, admin["email"], "Rejected", "")
        return {"message": "Delete request rejected and cleared."}
    approvals = list(set(req.get("approvals", []) + [admin["email"]]))
    req["approvals"] = approvals
    if is_super_admin(admin) or set(approvals) >= voters:
        await db.event_proposals.update_one(
            {"id": event_id},
            {"$set": {"status": "deleted", "deleted_by": admin["email"],
                      "deleted_reason": req.get("reason", ""),
                      "deleted_at": datetime.now(timezone.utc).isoformat(),
                      "delete_request": req,
                      "updated_at": datetime.now(timezone.utc).isoformat()}},
        )
        await log_activity("event_deleted", "event", event_id, admin["email"], f"Unanimous: {req.get('reason', '')}", "")
        return {"message": "Event deleted (unanimous)."}
    await db.event_proposals.update_one({"id": event_id}, {"$set": {"delete_request": req}})
    remaining = len(voters - set(approvals))
    return {"message": f"Approved. {remaining} more admin(s) needed."}


@router.get("/admin/events/proposals")
async def list_event_proposals(admin: dict = Depends(require_admin)):
    cursor = db.event_proposals.find({}, {"_id": 0}).sort("created_at", -1)
    rows = await cursor.to_list(500)
    treasurer = await _treasurer_email()
    return {"events": rows, "treasurer_email": treasurer, "viewer_is_treasurer": (admin.get("designation") == "Treasurer")}


@router.get("/admin/treasury-snapshot")
async def admin_treasury_snapshot(admin: dict = Depends(require_admin)):
    """Live financial snapshot used by the Treasurer to gauge headroom before
    approving an event budget. All numbers are scoped to the current Indian
    Financial Year (1 Apr → 31 Mar)."""
    today = datetime.now(timezone.utc).date()
    fy_s, fy_e, fy_label = fy_for_date(today)
    s_iso = fy_s.isoformat()
    e_iso = fy_e.isoformat() + "T23:59:59"
    # Confirmed donations YTD
    don_pipeline = [
        {"$match": {"status": "confirmed", "created_at": {"$gte": s_iso, "$lte": e_iso}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}},
    ]
    don_agg = await db.donations.aggregate(don_pipeline).to_list(1)
    confirmed_total = int(don_agg[0]["total"]) if don_agg else 0
    confirmed_count = int(don_agg[0]["count"]) if don_agg else 0
    # Approved event budgets YTD (events whose event_date falls in FY)
    ev_approved = db.event_proposals.find(
        {"status": "approved", "event_date": {"$gte": s_iso, "$lte": fy_e.isoformat()}},
        {"_id": 0, "drive_name": 1, "budget": 1, "event_date": 1, "treasurer_email": 1},
    )
    approved_rows = await ev_approved.to_list(500)
    approved_committed = int(sum(float(e.get("budget", 0) or 0) for e in approved_rows))
    # Pending events awaiting treasurer (status='seconded')
    ev_pending = db.event_proposals.find(
        {"status": "seconded"}, {"_id": 0, "drive_name": 1, "budget": 1, "event_date": 1},
    )
    pending_rows = await ev_pending.to_list(500)
    pending_total = int(sum(float(e.get("budget", 0) or 0) for e in pending_rows))
    headroom = confirmed_total - approved_committed
    return {
        "fy_label": fy_label,
        "fy_start": fy_s.isoformat(),
        "fy_end": fy_e.isoformat(),
        "confirmed_donations": confirmed_total,
        "confirmed_donation_count": confirmed_count,
        "approved_event_budgets": approved_committed,
        "approved_event_count": len(approved_rows),
        "pending_event_budgets": pending_total,
        "pending_event_count": len(pending_rows),
        "available_headroom": headroom,
    }


# ── Event Report & Article Generation ──
@router.post("/admin/events/report")
async def submit_event_report(data: EventReportInput, admin: dict = Depends(require_admin)):
    drive = await db.drives.find_one({"id": data.drive_id})
    if not drive:
        raise HTTPException(status_code=404, detail="Drive not found")
    # Get volunteer names from attendance
    volunteer_names = []
    for email in data.attendance:
        u = await db.users.find_one({"email": email}, {"name": 1, "_id": 0})
        if u:
            volunteer_names.append(u["name"])
    # Calculate star hero: combination of attendance + hours + admin_rating (single aggregate)
    star_hero_email = ""
    star_hero_name = "the entire team"
    if data.attendance:
        # Single $unwind aggregation: get count of past attendance per email in O(1) DB calls
        attendance_agg = await db.event_reports.aggregate([
            {"$unwind": "$attendance"},
            {"$match": {"attendance": {"$in": data.attendance}}},
            {"$group": {"_id": "$attendance", "count": {"$sum": 1}}},
        ]).to_list(1000)
        attendance_counts = {a["_id"]: a["count"] for a in attendance_agg}
        users_list = await db.users.find({"email": {"$in": data.attendance}}, {"_id": 0}).to_list(1000)
        scores = []
        for u in users_list:
            email = u["email"]
            ac = attendance_counts.get(email, 0)
            hours = u.get("volunteer_hours", 0)
            score = (ac + 1) * 2 + hours + data.admin_rating
            scores.append({"email": email, "name": u.get("name", ""), "score": score})
        if scores:
            scores.sort(key=lambda x: x["score"], reverse=True)
            star_hero_email = scores[0]["email"]
            star_hero_name = scores[0]["name"]
    # Generate AI article
    article = await generate_event_article({
        "title": drive.get("title", ""),
        "mission": drive.get("mission_slug", "Community Service"),
        "date": drive.get("date", ""),
        "location": drive.get("location", ""),
        "time_spent": data.time_spent,
        "resources_spent": data.resources_spent,
        "summary": data.summary,
        "outcome": data.outcome,
        "issues": data.issues,
        "volunteer_names": volunteer_names,
        "star_hero": star_hero_name,
    })
    # Save event report
    report_doc = {
        "id": str(uuid.uuid4()), "drive_id": data.drive_id,
        "drive_title": drive.get("title", ""),
        "time_spent": data.time_spent, "resources_spent": data.resources_spent,
        "summary": data.summary, "issues": data.issues, "outcome": data.outcome,
        "admin_rating": data.admin_rating,
        "attendance": data.attendance, "volunteer_names": volunteer_names,
        "star_hero_email": star_hero_email, "star_hero_name": star_hero_name,
        "article": article, "reported_by": admin["email"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.event_reports.insert_one(report_doc)
    report_doc.pop("_id", None)
    # Mark drive as reported
    await db.drives.update_one({"id": data.drive_id}, {"$set": {"drive_type": "past", "reported": True}})
    # Update volunteer hours for attendees
    for email in data.attendance:
        await db.users.update_one({"email": email}, {"$inc": {"volunteer_hours": 1}})
    # Create notifications for all tagged volunteers
    for email in data.attendance:
        u = await db.users.find_one({"email": email}, {"name": 1, "_id": 0})
        notif_msg = f'You were tagged in the event report for "{drive.get("title", "")}".'
        if email == star_hero_email:
            notif_msg = f'Congratulations! You are the Star Hero of "{drive.get("title", "")}"!'
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()), "user_email": email,
            "title": f"Event Report: {drive.get('title', '')}",
            "message": notif_msg, "type": "event_report",
            "link": f"/drives/{data.drive_id}",
            "read": False, "created_at": datetime.now(timezone.utc).isoformat()
        })
        # Also send email notification
        try:
            await send_notification_email(email, f"Heroic HIFI: {drive.get('title', '')}", notif_msg)
        except Exception:
            pass
    # Award star hero badge
    if star_hero_email:
        await db.users.update_one({"email": star_hero_email}, {"$addToSet": {"badges": "Star Hero"}})
    await log_activity("event_report_submitted", "drive", data.drive_id, admin["email"], f"Star Hero: {star_hero_name}, Attendees: {len(data.attendance)}", "")
    return {"message": "Event report submitted and article generated!", "report": report_doc}


@router.get("/admin/events/reports")
async def list_event_reports(admin: dict = Depends(require_admin)):
    return await db.event_reports.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)


@router.get("/admin/events/pending")
async def get_pending_event_reports(admin: dict = Depends(require_admin)):
    """Get drives whose date has passed but no report has been filed."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    drives = await db.drives.find({"reported": {"$ne": True}}, {"_id": 0}).to_list(500)
    pending = [d for d in drives if d.get("date", "9999") <= today]
    return pending


# ── Notifications ──
@router.get("/notifications")
async def get_my_notifications(user: dict = Depends(get_current_user)):
    return await db.notifications.find({"user_email": user["email"]}, {"_id": 0}).sort("created_at", -1).to_list(50)


@router.get("/notifications/unread-count")
async def unread_count(user: dict = Depends(get_current_user)):
    count = await db.notifications.count_documents({"user_email": user["email"], "read": False})
    return {"count": count}


@router.put("/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: str, user: dict = Depends(get_current_user)):
    await db.notifications.update_one({"id": notif_id, "user_email": user["email"]}, {"$set": {"read": True}})
    return {"message": "Marked as read"}


@router.put("/notifications/read-all")
async def mark_all_read(user: dict = Depends(get_current_user)):
    await db.notifications.update_many({"user_email": user["email"], "read": False}, {"$set": {"read": True}})
    return {"message": "All notifications marked as read"}


# ── Admin Promotion (unanimous approval of all regular admins) ──
async def _regular_admin_emails() -> list:
    """All admins EXCEPT the Master Admin. Super Admin stays aloof from every
    vote — they can act unilaterally but never count as a regular voter."""
    sa = super_admin_email()
    cursor = db.users.find({"role": "admin", "email": {"$ne": sa}}, {"_id": 0, "email": 1})
    return [u["email"] async for u in cursor]


@router.post("/admin/promote-request")
async def request_admin_promotion(data: AdminPromotionRequest, admin: dict = Depends(require_admin)):
    target_email = data.target_email.lower().strip()
    target = await db.users.find_one({"email": target_email})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.get("role") == "admin":
        raise HTTPException(status_code=400, detail="User is already an admin")
    existing = await db.admin_promotions.find_one({"target_email": target_email, "status": "pending"})
    if existing:
        raise HTTPException(status_code=400, detail="A pending promotion request already exists for this user")
    regular_voters = await _regular_admin_emails()
    # Master Admin acts unilaterally; their "request" is immediately approved.
    if is_super_admin(admin):
        required_voters = []
        initial_approvals = [admin["email"]]
        status = "approved"
    else:
        # Unanimous — every regular admin (including the proposer) must approve.
        required_voters = regular_voters
        initial_approvals = [admin["email"]]
        status = "approved" if set(initial_approvals) >= set(required_voters) else "pending"
    doc = {
        "id": str(uuid.uuid4()), "target_email": target_email,
        "target_name": target.get("name", ""),
        "requested_by": admin["email"], "reason": data.reason,
        "required_voters": required_voters,
        "approvals": initial_approvals,
        "rejections": [],
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if status == "approved":
        await db.users.update_one({"email": target_email}, {"$set": {"role": "admin"}})
        await log_activity("admin_promoted", "user", target_email, admin["email"],
                           "Promoted to admin (Master Admin action)" if is_super_admin(admin) else "Promoted to admin (unanimous sole-voter)", "")
    else:
        remaining = len(set(required_voters) - set(initial_approvals))
        await log_activity("admin_promotion_requested", "user", target_email, admin["email"], f"Needs {remaining} more unanimous approvals", "")
    await db.admin_promotions.insert_one(doc)
    doc.pop("_id", None)
    remaining = len(set(required_voters) - set(initial_approvals))
    msg = "User promoted to admin." if status == "approved" else f"Promotion proposed. Needs unanimous approval from {remaining} more admin(s)."
    return {"message": msg, "promotion": doc}


@router.get("/admin/promote-requests")
async def list_promotion_requests(admin: dict = Depends(require_admin)):
    return await db.admin_promotions.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)


@router.put("/admin/promote-requests/{request_id}/approve")
async def approve_promotion(request_id: str, admin: dict = Depends(require_admin)):
    req = await db.admin_promotions.find_one({"id": request_id, "status": "pending"})
    if not req:
        raise HTTPException(status_code=404, detail="Request not found or already processed")
    if is_super_admin(admin):
        # Master Admin can force-approve at any time.
        approvals = list(set(req.get("approvals", []) + [admin["email"]]))
        await db.admin_promotions.update_one({"id": request_id}, {"$set": {"approvals": approvals, "status": "approved"}})
        await db.users.update_one({"email": req["target_email"]}, {"$set": {"role": "admin"}})
        await log_activity("admin_promoted", "user", req["target_email"], admin["email"], "Promoted by Master Admin override", "")
        return {"message": f"{req['target_name']} has been promoted to admin (Master Admin override)."}
    voters = set(req.get("required_voters", []))
    if admin["email"] not in voters:
        raise HTTPException(status_code=403, detail="You are not on this vote's roster.")
    if admin["email"] in req.get("approvals", []):
        raise HTTPException(status_code=400, detail="You have already approved this request")
    approvals = req.get("approvals", []) + [admin["email"]]
    if set(approvals) >= voters:
        await db.admin_promotions.update_one({"id": request_id}, {"$set": {"approvals": approvals, "status": "approved"}})
        await db.users.update_one({"email": req["target_email"]}, {"$set": {"role": "admin"}})
        await log_activity("admin_promoted", "user", req["target_email"], admin["email"], f"Promoted to admin ({len(approvals)}/{len(voters)} unanimous)", "")
        return {"message": f"{req['target_name']} has been promoted to admin!"}
    await db.admin_promotions.update_one({"id": request_id}, {"$set": {"approvals": approvals}})
    await log_activity("admin_promotion_approved", "user", req["target_email"], admin["email"], f"Approval {len(approvals)}/{len(voters)}", "")
    remaining = len(voters - set(approvals))
    return {"message": f"Approved. {remaining} more admin(s) still need to approve."}


@router.put("/admin/promote-requests/{request_id}/reject")
async def reject_promotion(request_id: str, admin: dict = Depends(require_admin)):
    req = await db.admin_promotions.find_one({"id": request_id, "status": "pending"})
    if not req:
        raise HTTPException(status_code=404, detail="Request not found or already processed")
    rejections = req.get("rejections", []) + [admin["email"]]
    await db.admin_promotions.update_one({"id": request_id}, {"$set": {"rejections": rejections, "status": "rejected"}})
    await log_activity("admin_promotion_rejected", "user", req["target_email"], admin["email"], "Promotion rejected", "")
    return {"message": "Promotion request rejected."}


# ── Admin Removal (unanimous approval, Super Admin can bypass) ──
@router.post("/admin/remove-admin-request")
async def request_admin_removal(data: AdminRemovalRequest, admin: dict = Depends(require_admin)):
    target_email = data.target_email.lower().strip()
    if is_super_admin(target_email):
        raise HTTPException(status_code=403, detail="The Master Admin cannot be removed via this workflow.")
    target = await db.users.find_one({"email": target_email})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.get("role") != "admin":
        raise HTTPException(status_code=400, detail="User is not an admin")
    existing = await db.admin_removals.find_one({"target_email": target_email, "status": "pending"})
    if existing:
        raise HTTPException(status_code=400, detail="A pending removal request already exists for this admin")
    regular_voters = await _regular_admin_emails()
    if is_super_admin(admin):
        required_voters = []
        initial_approvals = [admin["email"]]
        status = "approved"
    else:
        # Unanimous — all regular admins EXCEPT the target must approve.
        required_voters = [e for e in regular_voters if e != target_email]
        initial_approvals = [admin["email"]]
        status = "approved" if set(initial_approvals) >= set(required_voters) else "pending"
    doc = {
        "id": str(uuid.uuid4()), "target_email": target_email,
        "target_name": target.get("name", ""),
        "requested_by": admin["email"], "reason": (data.reason or "").strip(),
        "required_voters": required_voters,
        "approvals": initial_approvals,
        "rejections": [],
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if status == "approved":
        await db.users.update_one({"email": target_email}, {"$set": {"role": "member"}})
        await log_activity("admin_demoted", "user", target_email, admin["email"],
                           "Admin demoted (Master Admin action)" if is_super_admin(admin) else "Admin demoted (unanimous sole-voter)", "")
    else:
        remaining = len(set(required_voters) - set(initial_approvals))
        await log_activity("admin_removal_requested", "user", target_email, admin["email"], f"Needs {remaining} more unanimous approvals", "")
    await db.admin_removals.insert_one(doc)
    doc.pop("_id", None)
    remaining = len(set(required_voters) - set(initial_approvals))
    msg = "Admin removed." if status == "approved" else f"Removal proposed. Needs unanimous approval from {remaining} more admin(s)."
    return {"message": msg, "removal": doc}


@router.get("/admin/remove-admin-requests")
async def list_removal_requests(admin: dict = Depends(require_admin)):
    return await db.admin_removals.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)


@router.put("/admin/remove-admin-requests/{request_id}/approve")
async def approve_removal(request_id: str, admin: dict = Depends(require_admin)):
    req = await db.admin_removals.find_one({"id": request_id, "status": "pending"})
    if not req:
        raise HTTPException(status_code=404, detail="Request not found or already processed")
    if is_super_admin(admin):
        approvals = list(set(req.get("approvals", []) + [admin["email"]]))
        await db.admin_removals.update_one({"id": request_id}, {"$set": {"approvals": approvals, "status": "approved"}})
        await db.users.update_one({"email": req["target_email"]}, {"$set": {"role": "member"}})
        await log_activity("admin_demoted", "user", req["target_email"], admin["email"], "Removed by Master Admin override", "")
        return {"message": f"{req['target_name']} has been removed from admin (Master Admin override)."}
    voters = set(req.get("required_voters", []))
    if admin["email"] not in voters:
        raise HTTPException(status_code=403, detail="You are not on this vote's roster (the target admin cannot vote).")
    if admin["email"] in req.get("approvals", []):
        raise HTTPException(status_code=400, detail="You have already approved this request")
    approvals = req.get("approvals", []) + [admin["email"]]
    if set(approvals) >= voters:
        await db.admin_removals.update_one({"id": request_id}, {"$set": {"approvals": approvals, "status": "approved"}})
        await db.users.update_one({"email": req["target_email"]}, {"$set": {"role": "member"}})
        await log_activity("admin_demoted", "user", req["target_email"], admin["email"], f"Admin removed ({len(approvals)}/{len(voters)} unanimous)", "")
        return {"message": f"{req['target_name']} has been removed from admin."}
    await db.admin_removals.update_one({"id": request_id}, {"$set": {"approvals": approvals}})
    await log_activity("admin_removal_approved", "user", req["target_email"], admin["email"], f"Approval {len(approvals)}/{len(voters)}", "")
    remaining = len(voters - set(approvals))
    return {"message": f"Approved. {remaining} more admin(s) still need to approve."}


@router.put("/admin/remove-admin-requests/{request_id}/reject")
async def reject_removal(request_id: str, admin: dict = Depends(require_admin)):
    req = await db.admin_removals.find_one({"id": request_id, "status": "pending"})
    if not req:
        raise HTTPException(status_code=404, detail="Request not found or already processed")
    rejections = req.get("rejections", []) + [admin["email"]]
    await db.admin_removals.update_one({"id": request_id}, {"$set": {"rejections": rejections, "status": "rejected"}})
    await log_activity("admin_removal_rejected", "user", req["target_email"], admin["email"], "Removal rejected", "")
    return {"message": "Removal request rejected."}


# ── Event Articles (public) ──
@router.get("/events/articles")
async def list_event_articles():
    reports = await db.event_reports.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return [{"id": r["id"], "title": r.get("drive_title", ""), "article": r.get("article", ""), "star_hero": r.get("star_hero_name", ""), "volunteer_names": r.get("volunteer_names", []), "date": r.get("created_at", "")} for r in reports]
