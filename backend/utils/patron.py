"""
Heroic Patron tier — auto-promotes recurring donors with ≥6 successful charges.

A 'Heroic Patron' is someone who has committed long enough that their
recurring donations have been charged at least 6 times. They get:
  - The 'Heroic Patron' badge on their user record
  - A pinned spot on the Wall of Fame with tier='heroic_patron'
  - Their charge_count and plan_type surfaced publicly

This module is called from:
  - routes/subscriptions.py webhook (subscription.charged event)
  - admin endpoint POST /api/admin/patrons/recompute (manual refresh)
"""
from datetime import datetime, timezone

from config import db

PATRON_THRESHOLD = 6  # successful charges to qualify
PATRON_BADGE = "Heroic Patron"


async def count_subscription_charges(email: str) -> int:
    """Count confirmed donations linked to a subscription for this email."""
    return await db.donations.count_documents({
        "email": email.lower().strip(),
        "subscription_id": {"$exists": True, "$ne": ""},
        "status": "confirmed",
    })


async def get_patron_summary(email: str) -> dict:
    """Return charge_count, total_amount, plan, qualified for one user."""
    email = email.lower().strip()
    charges = await db.donations.find({
        "email": email,
        "subscription_id": {"$exists": True, "$ne": ""},
        "status": "confirmed",
    }, {"_id": 0}).to_list(500)
    total = sum(c.get("amount", 0) for c in charges)
    sub = await db.subscriptions.find_one(
        {"email": email}, {"_id": 0, "plan": 1}, sort=[("created_at", -1)]
    )
    plan = (sub or {}).get("plan", "")
    return {
        "email": email,
        "charge_count": len(charges),
        "total_amount": total,
        "plan": plan,
        "qualified": len(charges) >= PATRON_THRESHOLD,
    }


async def promote_if_qualified(email: str) -> dict:
    """Award Heroic Patron badge + Wall of Fame entry if user crossed the threshold."""
    summary = await get_patron_summary(email)
    if not summary["qualified"]:
        return {"promoted": False, **summary}

    user = await db.users.find_one({"email": summary["email"]})
    if not user:
        return {"promoted": False, "reason": "user_not_found", **summary}

    # Add badge (idempotent)
    await db.users.update_one(
        {"email": summary["email"]},
        {"$addToSet": {"badges": PATRON_BADGE}},
    )

    # Add or update Wall of Fame entry with tier=heroic_patron
    wall_entry = await db.wall_of_fame.find_one({"email": summary["email"]})
    payload = {
        "tier": "heroic_patron",
        "patron_charge_count": summary["charge_count"],
        "patron_total_amount": summary["total_amount"],
        "patron_plan": summary["plan"],
        "patron_promoted_at": datetime.now(timezone.utc).isoformat(),
    }
    if wall_entry:
        await db.wall_of_fame.update_one({"email": summary["email"]}, {"$set": payload})
    else:
        await db.wall_of_fame.insert_one({
            "email": summary["email"],
            "name": user.get("name", ""),
            "role": user.get("role", ""),
            "volunteer_hours": user.get("volunteer_hours", 0),
            "total_donated": summary["total_amount"],
            "badges": user.get("badges", []) + [PATRON_BADGE],
            "profile_pic_path": user.get("profile_pic_path", ""),
            "contribution_summary": f"Heroic Patron with {summary['charge_count']} {summary['plan']} contributions.",
            "added_by": "system_auto",
            "added_at": datetime.now(timezone.utc).isoformat(),
            **payload,
        })
    return {"promoted": True, **summary}


async def list_patrons(limit: int = 50) -> list:
    """Public list of Heroic Patrons sorted by charge count + amount."""
    rows = await db.wall_of_fame.find(
        {"tier": "heroic_patron"}, {"_id": 0}
    ).sort([("patron_charge_count", -1), ("patron_total_amount", -1)]).to_list(limit)
    return rows


async def recompute_all() -> dict:
    """Walk every subscriber and promote those who qualify. Used by admin trigger."""
    emails = await db.subscriptions.distinct("email")
    promoted = 0
    for email in emails:
        result = await promote_if_qualified(email)
        if result.get("promoted"):
            promoted += 1
    return {"checked": len(emails), "promoted": promoted, "threshold": PATRON_THRESHOLD}
