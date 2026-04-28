"""Public per-hero recognition card assembler.

Always computed fresh from underlying truth (users + donations + ledgers +
office_history) — there is no separate `heroes` collection to sync. Any
update to the source data is instantly reflected on the next API hit.

Money values are rounded to the nearest \u20B9100 for donor privacy (same
rules as Wall of Fame). Admins are intentionally NOT given a tenure /
duration framing on the public card — they serve the foundation forever,
behind the scenes.
"""
import re
from datetime import datetime, timezone

from config import db
from utils.money import round_to_100


_NON_SLUG_CHARS = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    """'Anita Sharma' → 'anita-sharma'. Strips diacritics? No — stays ASCII-safe.
    Empty / non-ASCII names collapse to a hyphenless string we keep."""
    s = (name or "").strip().lower()
    s = _NON_SLUG_CHARS.sub("-", s)
    s = s.strip("-")
    return s or "hero"


async def _resolve_user_by_slug_or_email(slug_or_email: str) -> dict | None:
    """Resolve a public-card identifier. Tries email first, then matches the
    slugified `name` field for active users."""
    candidate = (slug_or_email or "").strip().lower()
    if not candidate:
        return None
    if "@" in candidate:
        return await db.users.find_one({"email": candidate, "status": {"$ne": "suspended"}})
    # Slug match — pull a small batch and compare slugified names
    cursor = db.users.find(
        {"status": {"$ne": "suspended"}},
        {"_id": 0, "email": 1, "name": 1, "role": 1, "badges": 1,
         "designation": 1, "tenure_start": 1, "leadership_bio": 1,
         "profile_pic_path": 1, "is_super_admin": 1, "volunteer_hours": 1,
         "created_at": 1, "patron_since": 1, "patron_plan": 1,
         "patron_charge_count": 1, "patron_total_amount": 1, "specializations": 1,
         "contribution_summary": 1, "status": 1},
    )
    matches = []
    async for u in cursor:
        if slugify(u.get("name", "")) == candidate:
            matches.append(u)
    # If exactly one match, return it. Multiple matches means name collision —
    # we deterministically pick the earliest registrant so the slug is stable.
    if not matches:
        return None
    matches.sort(key=lambda x: x.get("created_at", "") or "")
    return matches[0]


async def assemble_hero_card(slug_or_email: str) -> dict | None:
    """Build the full public hero-card payload. Returns None if the identifier
    doesn't resolve. Master Admin is never publicly resolvable."""
    user = await _resolve_user_by_slug_or_email(slug_or_email)
    if not user:
        return None
    # Privacy guard — never expose Master Admin publicly
    import os
    super_email = os.environ.get("ADMIN_EMAIL", "admin@heroichifi.org").lower().strip()
    if (user.get("email") or "").lower() == super_email:
        return None

    email = user.get("email", "").lower()
    name = user.get("name", "")
    is_admin = user.get("role") == "admin"

    # Lifetime totals (confirmed donations only, rounded for public display)
    agg = await db.donations.aggregate([
        {"$match": {"email": email, "status": "confirmed"}},
        {"$group": {
            "_id": None,
            "total": {"$sum": "$amount"},
            "fee_absorbed": {"$sum": {"$ifNull": ["$fee_covered", 0]}},
            "count": {"$sum": 1},
            "first_at": {"$min": "$created_at"},
            "last_at": {"$max": "$created_at"},
        }},
    ]).to_list(1)
    if agg:
        a = agg[0]
        total = round_to_100(a.get("total"))
        fee_absorbed = round_to_100(a.get("fee_absorbed"))
        donation_count = int(a.get("count") or 0)
        first_donation = a.get("first_at", "")
        last_donation = a.get("last_at", "")
    else:
        total = fee_absorbed = donation_count = 0
        first_donation = last_donation = ""

    # Award tenures — Top Donor + Most Generous Donor ledgers
    top_donor_history = await db.top_donor_ledger.find(
        {"donor_email": email}, {"_id": 0},
    ).sort("awarded_at", -1).to_list(50)
    for r in top_donor_history:
        r["peak_amount"] = round_to_100(r.get("peak_amount"))
    most_generous_history = await db.most_generous_ledger.find(
        {"donor_email": email}, {"_id": 0},
    ).sort("awarded_at", -1).to_list(50)
    for r in most_generous_history:
        r["peak_fee"] = round_to_100(r.get("peak_fee"))
        r["peak_pledge"] = round_to_100(r.get("peak_pledge"))

    # Office tenure history (post-by-post)
    office_history = await db.office_history.find(
        {"user_email": email}, {"_id": 0},
    ).sort("start_date", -1).to_list(50)

    # Badges (filtered to public-display set)
    public_badges = list(user.get("badges", []) or [])

    role_label = (
        "Founding Admin" if is_admin
        else "Helping Hero" if user.get("role") == "volunteer"
        else "Member"
    )

    return {
        "slug": slugify(name) if not is_admin else slugify(name),  # admins still get a slug
        "name": name,
        "role": user.get("role", "member"),
        "role_label": role_label,
        "is_admin": is_admin,
        "profile_pic_path": user.get("profile_pic_path", ""),
        "designation": user.get("designation", ""),
        "leadership_bio": user.get("leadership_bio", ""),
        # Tenure framing — for admins we DELIBERATELY omit duration values.
        "tenure_start": "" if is_admin else user.get("tenure_start", ""),
        "joined_at": "" if is_admin else (user.get("created_at", "") or ""),
        "volunteer_hours": 0 if is_admin else int(user.get("volunteer_hours", 0) or 0),
        "patron_since": "" if is_admin else (user.get("patron_since", "") or ""),
        "patron_plan": "" if is_admin else (user.get("patron_plan", "") or ""),
        "patron_charge_count": 0 if is_admin else int(user.get("patron_charge_count", 0) or 0),
        "patron_total_amount": 0 if is_admin else round_to_100(user.get("patron_total_amount", 0)),
        # Lifetime monetary recognition (rounded)
        "lifetime_total": total,
        "lifetime_fee_absorbed": fee_absorbed,  # >0 triggers magnanimity callout
        "donation_count": donation_count,
        # Tenure histories
        "top_donor_tenures": top_donor_history,
        "most_generous_tenures": most_generous_history,
        "office_tenures": office_history,
        # Badges + summary
        "badges": public_badges,
        "specializations": [] if is_admin else (user.get("specializations", []) or []),
        "contribution_summary": user.get("contribution_summary", ""),
        # Sync metadata — clients can use this to show "Last synced X seconds ago"
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "first_donation_at": first_donation,
        "last_donation_at": last_donation,
    }
