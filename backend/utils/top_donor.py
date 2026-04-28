"""Real-time "Top Donor of the Year" engine.

On every confirmed donation or subscription charge we compute lifetime-in-FY
totals per donor from ``db.donations`` (status ∈ {confirmed}) and, if the
leader has changed, close the previous ledger row (capturing duration of
tenure) and open a new one. Every holder's stint is preserved for audit.
"""

import uuid
from datetime import datetime, timezone, date, timedelta

from config import db

IST = timezone(timedelta(hours=5, minutes=30))


def fy_for_date(d: date) -> tuple[date, date, str]:
    """Indian FY runs 1 Apr -> 31 Mar. Returns (start, end, label like ``2024-25``)."""
    if d.month >= 4:
        s = date(d.year, 4, 1)
        e = date(d.year + 1, 3, 31)
    else:
        s = date(d.year - 1, 4, 1)
        e = date(d.year, 3, 31)
    label = f"{s.year}-{str(e.year)[2:]}"
    return s, e, label


def current_fy():
    return fy_for_date(datetime.now(IST).date())


async def _totals_in_fy(fy_s: date, fy_e: date) -> list[dict]:
    """Aggregate confirmed donation totals grouped by email for the given FY
    window. Uses ``created_at`` (ISO string) — compares lexicographically since
    ISO-8601 sorts correctly as strings."""
    s_iso, e_iso = fy_s.isoformat(), fy_e.isoformat() + "T23:59:59"
    cursor = db.donations.aggregate([
        {"$match": {
            "status": "confirmed",
            "created_at": {"$gte": s_iso, "$lte": e_iso},
            "email": {"$exists": True, "$ne": ""},
        }},
        {"$group": {
            "_id": "$email",
            "total": {"$sum": "$amount"},
            "name": {"$last": "$name"},
            "last_at": {"$max": "$created_at"},
        }},
        {"$sort": {"total": -1, "last_at": 1}},
    ])
    return await cursor.to_list(500)


async def recompute_top_donor() -> dict | None:
    """Recompute the current FY's Top Donor. If the leader has changed, close
    the previous ledger row and open a new one. Idempotent — safe to call
    repeatedly (e.g. from donation & subscription confirmation hooks)."""
    fy_s, fy_e, fy_label = current_fy()
    totals = await _totals_in_fy(fy_s, fy_e)
    if not totals:
        return None
    leader = totals[0]
    leader_email = leader["_id"]
    leader_total = int(leader["total"] or 0)
    now_iso = datetime.now(timezone.utc).isoformat()

    # Find the current (unclosed) row for this FY
    active = await db.top_donor_ledger.find_one(
        {"fy_label": fy_label, "ended_at": None},
        {"_id": 0},
    )
    if active and active["donor_email"] == leader_email:
        # Same leader — just bump their running total snapshot
        if active.get("peak_amount", 0) != leader_total:
            await db.top_donor_ledger.update_one(
                {"id": active["id"]},
                {"$set": {"peak_amount": leader_total, "last_observed_at": now_iso}},
            )
        return {**active, "peak_amount": leader_total}

    # Leader has changed (or there was none). The successor must STRICTLY
    # exceed the previous leader's amount (user requirement). If the active
    # row exists, guard with that check.
    if active and leader_total <= int(active.get("peak_amount", 0)):
        return active
    # Close the previous active row (if any)
    if active:
        await db.top_donor_ledger.update_one(
            {"id": active["id"]},
            {"$set": {
                "ended_at": now_iso,
                "ended_reason": f"Overtaken by {leader.get('name', '')} (₹{leader_total:,})",
            }},
        )
    # Open a new row
    new_row = {
        "id": str(uuid.uuid4()),
        "fy_label": fy_label,
        "fy_start": fy_s.isoformat(),
        "fy_end": fy_e.isoformat(),
        "donor_email": leader_email,
        "donor_name": leader.get("name", ""),
        "peak_amount": leader_total,
        "awarded_at": now_iso,
        "last_observed_at": now_iso,
        "ended_at": None,
        "ended_reason": None,
    }
    await db.top_donor_ledger.insert_one(new_row)
    # Materialise the "Top Donor" badge on the user doc as well so the roster
    # shows the award. Remove it from any previous holders for this FY.
    await db.users.update_many(
        {"badges": "Top Donor"},
        {"$pull": {"badges": "Top Donor"}},
    )
    await db.users.update_one(
        {"email": leader_email},
        {"$addToSet": {"badges": "Top Donor"}},
    )
    new_row.pop("_id", None)
    return new_row


async def close_all_open_rows(reason: str = "FY ended"):
    """Called at FY rollover (1 Apr) by the annual job to freeze every open
    ledger row so the previous year's winners remain preserved."""
    now_iso = datetime.now(timezone.utc).isoformat()
    await db.top_donor_ledger.update_many(
        {"ended_at": None},
        {"$set": {"ended_at": now_iso, "ended_reason": reason}},
    )
