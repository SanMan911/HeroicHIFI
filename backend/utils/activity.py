import uuid
import asyncio

from config import db, logger
from datetime import datetime, timezone


async def log_activity(action: str, entity_type: str, entity_id: str = "", user_email: str = "", details: str = "", ip: str = ""):
    await db.activity_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "user_email": user_email,
        "details": details,
        "ip": ip,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
