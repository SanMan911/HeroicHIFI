from config import db

AUTO_BADGES = {
    "Helping Hero": lambda u, stats: True,
    "Century Hero": lambda u, stats: (u.get("volunteer_hours") or 0) >= 100,
    "Generous Soul": lambda u, stats: stats.get("total_donated", 0) >= 10000,
    "Community Builder": lambda u, stats: stats.get("messages_sent", 0) >= 50,
}
ADMIN_ONLY_BADGES = ["Star Volunteer of the Month", "Star Volunteer of the Quarter", "Star Volunteer of the Year", "Top Donor", "Most Generous Donor", "Rising Star"]


async def compute_auto_badges(user_doc):
    email = user_doc.get("email", "")
    total_donated_agg = await db.donations.aggregate([
        {"$match": {"email": email, "status": {"$in": ["confirmed", "pending"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    total_donated = total_donated_agg[0]["total"] if total_donated_agg else 0
    msgs_sent = await db.messages.count_documents({"sender_email": email})
    stats = {"total_donated": total_donated, "messages_sent": msgs_sent}
    earned = []
    for badge_name, check_fn in AUTO_BADGES.items():
        if check_fn(user_doc, stats):
            earned.append(badge_name)
    return earned, total_donated
