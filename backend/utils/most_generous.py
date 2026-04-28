"""Real-time "Most Generous Donor" engine.

Mirrors `top_donor.py` but ranks donors by lifetime-in-FY total **fee_covered**
(i.e. how much they voluntarily absorbed in Razorpay processing fees so the
foundation receives the full pledge). Awarded as the "Most Generous Donor"
badge — an alternative recognition track from raw donation amount.

Idempotent. Safe to invoke from every donation/subscription confirmation hook.
"""

import uuid
from datetime import datetime, timezone, date

from config import db
from utils.top_donor import current_fy


async def _fee_totals_in_fy(fy_s: date, fy_e: date) -> list[dict]:
    """Aggregate confirmed-donation fee-covered totals grouped by email for the
    given FY window. Donors who never opted-in (fee_covered == 0) are excluded."""
    s_iso, e_iso = fy_s.isoformat(), fy_e.isoformat() + "T23:59:59"
    cursor = db.donations.aggregate([
        {"$match": {
            "status": "confirmed",
            "created_at": {"$gte": s_iso, "$lte": e_iso},
            "email": {"$exists": True, "$ne": ""},
            "fee_covered": {"$gt": 0},
        }},
        {"$group": {
            "_id": "$email",
            "total_fee": {"$sum": "$fee_covered"},
            "total_pledge": {"$sum": "$amount"},
            "name": {"$last": "$name"},
            "last_at": {"$max": "$created_at"},
        }},
        {"$sort": {"total_fee": -1, "last_at": 1}},
    ])
    return await cursor.to_list(500)


async def recompute_most_generous() -> dict | None:
    """Recompute the current FY's Most Generous Donor (highest total fee_covered).
    Successor must STRICTLY exceed the incumbent to claim the title — same rule
    as Top Donor. Idempotent."""
    fy_s, fy_e, fy_label = current_fy()
    totals = await _fee_totals_in_fy(fy_s, fy_e)
    if not totals:
        return None
    leader = totals[0]
    leader_email = leader["_id"]
    leader_fee = int(leader["total_fee"] or 0)
    leader_pledge = int(leader["total_pledge"] or 0)
    now_iso = datetime.now(timezone.utc).isoformat()

    active = await db.most_generous_ledger.find_one(
        {"fy_label": fy_label, "ended_at": None}, {"_id": 0},
    )
    if active and active["donor_email"] == leader_email:
        if active.get("peak_fee", 0) != leader_fee or active.get("peak_pledge", 0) != leader_pledge:
            await db.most_generous_ledger.update_one(
                {"id": active["id"]},
                {"$set": {
                    "peak_fee": leader_fee,
                    "peak_pledge": leader_pledge,
                    "last_observed_at": now_iso,
                }},
            )
        return {**active, "peak_fee": leader_fee, "peak_pledge": leader_pledge}

    if active and leader_fee <= int(active.get("peak_fee", 0)):
        return active
    if active:
        await db.most_generous_ledger.update_one(
            {"id": active["id"]},
            {"$set": {
                "ended_at": now_iso,
                "ended_reason": f"Overtaken by {leader.get('name', '')} (\u20B9{leader_fee:,} absorbed)",
            }},
        )
    new_row = {
        "id": str(uuid.uuid4()),
        "fy_label": fy_label,
        "fy_start": fy_s.isoformat(),
        "fy_end": fy_e.isoformat(),
        "donor_email": leader_email,
        "donor_name": leader.get("name", ""),
        "peak_fee": leader_fee,
        "peak_pledge": leader_pledge,
        "awarded_at": now_iso,
        "last_observed_at": now_iso,
        "ended_at": None,
        "ended_reason": None,
    }
    await db.most_generous_ledger.insert_one(new_row)
    # Materialise badge
    await db.users.update_many(
        {"badges": "Most Generous Donor"},
        {"$pull": {"badges": "Most Generous Donor"}},
    )
    await db.users.update_one(
        {"email": leader_email},
        {"$addToSet": {"badges": "Most Generous Donor"}},
    )
    new_row.pop("_id", None)
    return new_row


async def close_all_open_rows(reason: str = "FY ended"):
    """Annual-rollover companion to top_donor.close_all_open_rows."""
    now_iso = datetime.now(timezone.utc).isoformat()
    await db.most_generous_ledger.update_many(
        {"ended_at": None},
        {"$set": {"ended_at": now_iso, "ended_reason": reason}},
    )
