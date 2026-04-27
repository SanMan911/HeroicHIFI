from fastapi import APIRouter, HTTPException, Request, Depends
import uuid
from datetime import datetime, timezone

from config import db
from models.schemas import StatusUpdate, AdminUserUpdate, BadgeAction, TicketResponse, DriveInput
from utils.auth import require_admin
from utils.activity import log_activity

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
        "image_url": data.image_url or "", "created_by": admin["email"],
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
