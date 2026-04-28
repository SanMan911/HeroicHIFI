from fastapi import APIRouter, HTTPException, Request, Depends
import uuid
from datetime import datetime, timezone

from config import db
from models.schemas import (
    StatusUpdate, AdminUserUpdate, BadgeAction, VolunteerInput,
    QueryInput, TicketInput, TicketResponse, RoleChangeRequest, DriveInput
)
from utils.auth import get_current_user, require_admin
from utils.activity import log_activity
from data.office_posts import OFFICE_POSTS

router = APIRouter(prefix="/api")


# ── Volunteers (legacy form) ──
@router.post("/volunteers")
async def register_volunteer(data: VolunteerInput, request: Request):
    email = data.email.lower().strip()
    existing_user = await db.users.find_one({"email": email})
    if existing_user:
        if existing_user.get("role") != "volunteer":
            await db.users.update_one({"email": email}, {"$set": {"role": "volunteer"}})
            await log_activity("role_upgraded", "user", "", email, "Upgraded to volunteer via form", request.client.host if request.client else "")
        return {"message": "Your account has been updated to volunteer status.", "volunteer": {"email": email, "status": "approved"}}
    doc = {
        "id": str(uuid.uuid4()), "name": data.name, "email": email,
        "phone": data.phone, "city": data.city, "interests": data.interests,
        "message": data.message, "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.volunteers.insert_one(doc)
    doc.pop("_id", None)
    await log_activity("volunteer_registered", "volunteer", doc["id"], email, f"City: {data.city}", request.client.host if request.client else "")
    return {"message": "Thank you for registering as a volunteer! We will get back to you shortly.", "volunteer": doc}


# ── Queries ──
@router.post("/queries")
async def submit_query(data: QueryInput, request: Request):
    doc = {
        "id": str(uuid.uuid4()), "name": data.name, "email": data.email.lower().strip(),
        "mission": data.mission, "subject": data.subject, "message": data.message,
        "status": "open", "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.queries.insert_one(doc)
    doc.pop("_id", None)
    await log_activity("query_submitted", "query", doc["id"], data.email, f"Mission: {data.mission}", request.client.host if request.client else "")
    return {"message": "Your query has been submitted successfully.", "query": doc}


# ── Tickets ──
@router.post("/tickets")
async def create_ticket(data: TicketInput, request: Request, user: dict = Depends(get_current_user)):
    doc = {
        "id": str(uuid.uuid4()), "user_email": user["email"], "user_name": user.get("name", ""),
        "subject": data.subject, "description": data.description,
        "priority": data.priority, "status": "open", "admin_response": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.tickets.insert_one(doc)
    doc.pop("_id", None)
    await log_activity("ticket_created", "ticket", doc["id"], user["email"], f"Subject: {data.subject}", request.client.host if request.client else "")
    return {"message": "Ticket submitted successfully. We will review it shortly.", "ticket": doc}


@router.get("/tickets")
async def list_my_tickets(user: dict = Depends(get_current_user)):
    return await db.tickets.find({"user_email": user["email"]}, {"_id": 0}).sort("created_at", -1).to_list(100)


# ── Missions ──
from data.missions import MISSIONS_DATA

@router.get("/missions")
async def get_missions():
    return MISSIONS_DATA

@router.get("/missions/{slug}")
async def get_mission(slug: str):
    for m in MISSIONS_DATA:
        if m["slug"] == slug:
            return m
    raise HTTPException(status_code=404, detail="Mission not found")


# ── Directory ──
@router.get("/directory")
async def get_directory(user: dict = Depends(get_current_user)):
    return await db.users.find(
        {"role": {"$ne": "admin"}, "status": {"$ne": "suspended"}},
        {"_id": 0, "password_hash": 0, "pan_number": 0, "aadhaar_number": 0, "address": 0, "dob": 0, "age": 0, "admin_comments": 0, "merchandise_issued": 0, "suspended_until": 0, "suspension_reason": 0}
    ).sort("created_at", -1).to_list(500)


# ── Role Change Requests ──
@router.post("/role-requests")
async def request_role_change(data: RoleChangeRequest, request: Request, user: dict = Depends(get_current_user)):
    if data.requested_role not in ("volunteer", "member"):
        raise HTTPException(status_code=400, detail="Invalid role. Choose 'volunteer' or 'member'.")
    if user.get("role") == data.requested_role:
        raise HTTPException(status_code=400, detail=f"You are already a {data.requested_role}.")
    existing = await db.role_requests.find_one({"email": user["email"], "status": "pending"})
    if existing:
        raise HTTPException(status_code=400, detail="You already have a pending role change request.")
    doc = {
        "id": str(uuid.uuid4()), "email": user["email"], "name": user.get("name", ""),
        "current_role": user.get("role", "member"), "requested_role": data.requested_role,
        "reason": data.reason, "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.role_requests.insert_one(doc)
    doc.pop("_id", None)
    await log_activity("role_change_requested", "user", user["email"], user["email"], f"{user.get('role')} -> {data.requested_role}", request.client.host if request.client else "")
    return {"message": "Role change request submitted. An admin will review it.", "request": doc}


@router.get("/role-requests/mine")
async def my_role_requests(user: dict = Depends(get_current_user)):
    return await db.role_requests.find({"email": user["email"]}, {"_id": 0}).sort("created_at", -1).to_list(10)


# ── Drives (public) ──
@router.get("/drives")
async def list_drives():
    return await db.drives.find({}, {"_id": 0}).sort("date", -1).to_list(200)


# ── Wall of Fame (public) ──
@router.get("/wall-of-fame")
async def get_wall_of_fame():
    return await db.wall_of_fame.find({}, {"_id": 0}).sort("added_at", -1).to_list(100)


# ── Recognitions ticker (public) ──
@router.get("/recognitions")
async def get_recognitions():
    """Live homepage ticker payload — Top Donor of the Year + freshest badge
    awards across volunteers & members. No auth required."""
    from utils.top_donor import current_fy
    _s, _e, fy_label = current_fy()
    top = await db.top_donor_ledger.find_one(
        {"fy_label": fy_label, "ended_at": None},
        {"_id": 0},
    )
    # Recent badge awards (Star Volunteer / Rising Star / etc.) taken from
    # users — we surface the newest 8 to keep the marquee snappy.
    featured_badges = [
        "Star Volunteer of the Month",
        "Star Volunteer of the Quarter",
        "Star Volunteer of the Year",
        "Rising Star",
        "Community Builder",
        "Century Hero",
        "Heroic Patron",
    ]
    recent = []
    cursor = db.users.find(
        {"badges": {"$in": featured_badges}},
        {"_id": 0, "email": 1, "name": 1, "badges": 1, "profile_pic_path": 1},
    ).limit(20)
    async for u in cursor:
        for b in u.get("badges", []):
            if b in featured_badges:
                recent.append({
                    "name": u.get("name", ""),
                    "email": u.get("email", ""),
                    "badge": b,
                    "profile_pic_path": u.get("profile_pic_path", ""),
                })
    recent = recent[:12]
    # Active office bearers (Chairman/Secretary/Treasurer)
    bearers = []
    async for u in db.users.find(
        {"designation": {"$in": ["Chairman", "Secretary", "Treasurer"]}},
        {"_id": 0, "name": 1, "designation": 1},
    ):
        bearers.append(u)
    return {
        "fy_label": fy_label,
        "top_donor": {
            "name": top.get("donor_name", "") if top else "",
            "amount": int(top.get("peak_amount", 0)) if top else 0,
            "since": top.get("awarded_at", "") if top else "",
        } if top else None,
        "recent_badges": recent,
        "office_bearers": bearers,
    }


# ── Top Donor ledger (public history) ──
@router.get("/top-donor-ledger")
async def get_top_donor_ledger():
    """Immutable tenure log of every Top Donor of the Year — who held the
    badge, for what period, and the donation amount that took them there."""
    return await db.top_donor_ledger.find({}, {"_id": 0}).sort("awarded_at", -1).to_list(500)



# ── Leadership / Office Bearers (public) ──
@router.get("/office-posts")
async def get_office_posts():
    """Catalog of valid office-bearer post titles (used by the admin UI)."""
    return OFFICE_POSTS


@router.get("/leadership")
async def get_leadership():
    """Public list of office bearers — ANY user (admin, volunteer, member) who
    has an ``office-bearer post`` assigned to them by the Master Admin. Order:
    by position in the canonical ``OFFICE_POSTS`` list (Founder first), then by
    creation date."""
    cursor = db.users.find(
        {"designation": {"$exists": True, "$ne": ""}},
        {
            "_id": 0, "password_hash": 0, "pan_number": 0,
            "aadhaar_number": 0, "address": 0, "phone": 0,
            "admin_comments": 0, "suspension_reason": 0,
        },
    )
    rows = await cursor.to_list(100)
    rank = {p: i for i, p in enumerate(OFFICE_POSTS)}
    def _sort_key(u):
        return (rank.get(u.get("designation", ""), 999), u.get("created_at") or "")
    rows.sort(key=_sort_key)
    return [
        {
            "name": u.get("name", ""),
            "designation": u.get("designation", ""),
            "bio": u.get("leadership_bio", ""),
            "email": u.get("email", ""),
            "profile_pic_path": u.get("profile_pic_path", ""),
            "role": u.get("role", ""),
        }
        for u in rows
    ]

