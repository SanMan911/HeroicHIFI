from fastapi import APIRouter, HTTPException, Request, Depends
import uuid
from datetime import datetime, timezone

from config import db
from models.schemas import (
    StatusUpdate, AdminUserUpdate, BadgeAction, TicketResponse, DriveInput,
    EmailBlastInput, EventReportInput, AdminPromotionRequest
)
from utils.auth import require_admin, get_current_user
from utils.activity import log_activity
from utils.email import send_email_blast, send_notification_email
from utils.llm import generate_event_article

router = APIRouter(prefix="/api")


# ── Admin Donations ──
@router.get("/admin/donations")
async def admin_list_donations(user: dict = Depends(require_admin)):
    return await db.donations.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)


@router.put("/admin/donations/{item_id}/status")
async def admin_update_donation_status(item_id: str, data: StatusUpdate, user: dict = Depends(require_admin)):
    result = await db.donations.update_one({"id": item_id}, {"$set": {"status": data.status}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Donation not found")
    await log_activity("donation_status_updated", "donation", item_id, user["email"], f"Status -> {data.status}", "")
    return {"message": "Status updated", "status": data.status}


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


# ── Admin Users ──
@router.get("/admin/users")
async def admin_list_users(user: dict = Depends(require_admin)):
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).sort("created_at", -1).to_list(500)
    donation_totals = {}
    agg = await db.donations.aggregate([
        {"$match": {"status": {"$in": ["confirmed", "pending"]}}},
        {"$group": {"_id": "$email", "total": {"$sum": "$amount"}}}
    ]).to_list(1000)
    for entry in agg:
        donation_totals[entry["_id"]] = entry["total"]
    for u in users:
        u["total_donated"] = donation_totals.get(u["email"], 0)
    return users


@router.put("/admin/users/{user_email}/update")
async def admin_update_user(user_email: str, data: AdminUserUpdate, admin: dict = Depends(require_admin)):
    email = user_email.lower().strip()
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
    if data.status is not None:
        updates["status"] = data.status
        if data.status == "suspended":
            updates["suspended_until"] = data.suspended_until or ""
            updates["suspension_reason"] = data.suspension_reason or ""
        elif data.status == "active":
            updates["suspended_until"] = None
            updates["suspension_reason"] = ""
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    await db.users.update_one({"email": email}, {"$set": updates})
    changes = ", ".join(f"{k}={v}" for k, v in updates.items())
    await log_activity("admin_user_updated", "user", email, admin["email"], changes, "")
    return {"message": f"User {email} updated successfully"}


@router.delete("/admin/users/{user_email}")
async def admin_delete_user(user_email: str, user: dict = Depends(require_admin)):
    email = user_email.lower().strip()
    if email == user["email"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    result = await db.users.delete_one({"email": email})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    await log_activity("user_deleted", "user", email, user["email"], f"Deleted user: {email}", "")
    return {"message": f"User {email} deleted successfully"}


# ── Admin Badges ──
@router.post("/admin/users/{user_email}/badge")
async def admin_add_badge(user_email: str, data: BadgeAction, admin: dict = Depends(require_admin)):
    email = user_email.lower().strip()
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
    total_donations = await db.donations.count_documents({})
    agg = await db.donations.aggregate([{"$group": {"_id": None, "total": {"$sum": "$amount"}}}]).to_list(1)
    total_amount = agg[0]["total"] if agg else 0
    confirmed = await db.donations.count_documents({"status": "confirmed"})
    total_vol = await db.users.count_documents({"role": "volunteer"})
    total_members = await db.users.count_documents({"role": "member"})
    total_q = await db.queries.count_documents({})
    open_q = await db.queries.count_documents({"status": "open"})
    total_users = await db.users.count_documents({})
    total_tickets = await db.tickets.count_documents({})
    open_tickets = await db.tickets.count_documents({"status": "open"})
    pending_role_requests = await db.role_requests.count_documents({"status": "pending"})
    total_drives = await db.drives.count_documents({})
    verified_pan = await db.users.count_documents({"pan_verified": True})
    unverified_pan = await db.users.count_documents({"pan_verified": {"$ne": True}})
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
@router.get("/admin/activity-logs")
async def admin_activity_logs(limit: int = 100, admin: dict = Depends(require_admin)):
    return await db.activity_logs.find({}, {"_id": 0}).sort("timestamp", -1).to_list(limit)


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
    # Calculate star hero: combination of attendance + hours + admin_rating
    star_hero_email = ""
    star_hero_name = "the entire team"
    if data.attendance:
        scores = []
        for email in data.attendance:
            u = await db.users.find_one({"email": email})
            if u:
                attendance_count = await db.event_reports.count_documents({"attendance": email})
                hours = u.get("volunteer_hours", 0)
                score = (attendance_count + 1) * 2 + hours + data.admin_rating
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


# ── Admin Promotion (multi-admin approval) ──
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
    admin_count = await db.users.count_documents({"role": "admin"})
    required_approvals = max(1, admin_count - 1)
    doc = {
        "id": str(uuid.uuid4()), "target_email": target_email,
        "target_name": target.get("name", ""),
        "requested_by": admin["email"], "reason": data.reason,
        "required_approvals": required_approvals,
        "approvals": [admin["email"]],
        "rejections": [],
        "status": "approved" if required_approvals <= 1 else "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    if doc["status"] == "approved":
        await db.users.update_one({"email": target_email}, {"$set": {"role": "admin"}})
        await log_activity("admin_promoted", "user", target_email, admin["email"], "Promoted to admin (sole admin approval)", "")
    else:
        await log_activity("admin_promotion_requested", "user", target_email, admin["email"], f"Needs {required_approvals} approvals", "")
    await db.admin_promotions.insert_one(doc)
    doc.pop("_id", None)
    return {"message": f"{'User promoted to admin.' if doc['status'] == 'approved' else f'Promotion request created. Needs {required_approvals} admin approvals.'}", "promotion": doc}


@router.get("/admin/promote-requests")
async def list_promotion_requests(admin: dict = Depends(require_admin)):
    return await db.admin_promotions.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)


@router.put("/admin/promote-requests/{request_id}/approve")
async def approve_promotion(request_id: str, admin: dict = Depends(require_admin)):
    req = await db.admin_promotions.find_one({"id": request_id, "status": "pending"})
    if not req:
        raise HTTPException(status_code=404, detail="Request not found or already processed")
    if admin["email"] in req.get("approvals", []):
        raise HTTPException(status_code=400, detail="You have already approved this request")
    approvals = req.get("approvals", []) + [admin["email"]]
    required = req.get("required_approvals", 1)
    if len(approvals) >= required:
        await db.admin_promotions.update_one({"id": request_id}, {"$set": {"approvals": approvals, "status": "approved"}})
        await db.users.update_one({"email": req["target_email"]}, {"$set": {"role": "admin"}})
        await log_activity("admin_promoted", "user", req["target_email"], admin["email"], f"Promoted to admin ({len(approvals)}/{required} approvals)", "")
        return {"message": f"{req['target_name']} has been promoted to admin!"}
    else:
        await db.admin_promotions.update_one({"id": request_id}, {"$set": {"approvals": approvals}})
        await log_activity("admin_promotion_approved", "user", req["target_email"], admin["email"], f"Approval {len(approvals)}/{required}", "")
        return {"message": f"Approved. {len(approvals)}/{required} approvals received."}


@router.put("/admin/promote-requests/{request_id}/reject")
async def reject_promotion(request_id: str, admin: dict = Depends(require_admin)):
    req = await db.admin_promotions.find_one({"id": request_id, "status": "pending"})
    if not req:
        raise HTTPException(status_code=404, detail="Request not found or already processed")
    rejections = req.get("rejections", []) + [admin["email"]]
    await db.admin_promotions.update_one({"id": request_id}, {"$set": {"rejections": rejections, "status": "rejected"}})
    await log_activity("admin_promotion_rejected", "user", req["target_email"], admin["email"], "Promotion rejected", "")
    return {"message": "Promotion request rejected."}


# ── Event Articles (public) ──
@router.get("/events/articles")
async def list_event_articles():
    reports = await db.event_reports.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return [{"id": r["id"], "title": r.get("drive_title", ""), "article": r.get("article", ""), "star_hero": r.get("star_hero_name", ""), "volunteer_names": r.get("volunteer_names", []), "date": r.get("created_at", "")} for r in reports]
