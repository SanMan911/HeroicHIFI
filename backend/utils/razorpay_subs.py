"""
Razorpay Subscriptions integration — recurring monthly/quarterly donations.

Architecture is wired up; placeholder plan IDs in .env let admins test the
flow. To go live: create real plans in Razorpay dashboard and set
RAZORPAY_PLAN_MONTHLY / RAZORPAY_PLAN_QUARTERLY in backend/.env.

Razorpay subscription flow:
1. Client calls POST /api/subscriptions/create with plan + amount.
2. Backend creates a Subscription via Razorpay API and returns
   subscription_id + key_id.
3. Frontend opens Razorpay Checkout in 'subscription' mode.
4. On success, Razorpay sends webhook events (subscription.charged) which
   we record in the donations collection.

This module exposes:
  - create_subscription(plan, amount, customer)
  - cancel_subscription(sub_id)
  - verify_webhook_signature(body, signature)
"""
import os
import hmac
import hashlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)

PLAN_TO_INTERVAL = {"monthly": ("monthly", 1), "quarterly": ("monthly", 3)}


def _placeholder_plans() -> bool:
    p = os.environ.get("RAZORPAY_PLAN_MONTHLY", "")
    return not p or p.startswith("plan_PLACEHOLDER")


async def create_subscription(plan: str, amount_rupees: int, customer: dict) -> dict:
    """
    Create (or simulate) a Razorpay subscription.
    Returns: { subscription_id, key_id, plan_id, short_url, status, mode }
    """
    rz_key = os.environ.get("RAZORPAY_KEY_ID")
    rz_secret = os.environ.get("RAZORPAY_KEY_SECRET")

    plan_env_key = "RAZORPAY_PLAN_MONTHLY" if plan == "monthly" else "RAZORPAY_PLAN_QUARTERLY"
    plan_id = os.environ.get(plan_env_key, "")

    if not rz_key or not rz_secret:
        return {"subscription_id": "", "key_id": "", "plan_id": plan_id, "short_url": "",
                "status": "razorpay_not_configured", "mode": "stub"}

    if _placeholder_plans():
        # Architecture ready, plans not yet created in Razorpay dashboard.
        return {
            "subscription_id": f"sub_PENDING_{plan}_{customer.get('email', '')[:8]}",
            "key_id": rz_key,
            "plan_id": plan_id,
            "short_url": "",
            "status": "placeholder_plan",
            "mode": "stub",
            "note": "Create real plans in Razorpay dashboard, then set RAZORPAY_PLAN_MONTHLY / RAZORPAY_PLAN_QUARTERLY in .env",
        }

    try:
        import razorpay
        cli = razorpay.Client(auth=(rz_key, rz_secret))
        sub = cli.subscription.create({
            "plan_id": plan_id,
            "total_count": 12 if plan == "monthly" else 4,  # 1-year horizon
            "customer_notify": 1,
            "notes": {
                "donor_name": customer.get("name", ""),
                "donor_email": customer.get("email", ""),
                "donor_pan": customer.get("pan_number", ""),
                "amount_rupees": str(amount_rupees),
            },
        })
        return {"subscription_id": sub["id"], "key_id": rz_key, "plan_id": plan_id,
                "short_url": sub.get("short_url", ""), "status": sub.get("status", "created"), "mode": "live"}
    except Exception as e:
        logger.warning(f"Razorpay subscription create failed: {e}")
        return {"subscription_id": "", "key_id": rz_key, "plan_id": plan_id,
                "short_url": "", "status": f"error: {e}", "mode": "live"}


async def cancel_subscription(sub_id: str) -> dict:
    rz_key = os.environ.get("RAZORPAY_KEY_ID")
    rz_secret = os.environ.get("RAZORPAY_KEY_SECRET")
    if not rz_key or not rz_secret or _placeholder_plans():
        return {"cancelled": False, "status": "placeholder_or_not_configured"}
    try:
        import razorpay
        cli = razorpay.Client(auth=(rz_key, rz_secret))
        cli.subscription.cancel(sub_id)
        return {"cancelled": True, "status": "cancelled"}
    except Exception as e:
        return {"cancelled": False, "status": f"error: {e}"}


def verify_webhook_signature(body_bytes: bytes, signature: str) -> bool:
    secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")
    if not secret or secret.startswith("placeholder"):
        # Architecture ready — real webhooks will be verified once the secret is set.
        return False
    expected = hmac.new(secret.encode(), body_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature or "")
