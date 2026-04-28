"""
LIVE Razorpay Subscription tests — verifies POST /api/subscriptions/create
hits real Razorpay and returns mode=live + sub_/short_url for all 4 plans.
Also verifies plan validation, auth, amount-from-server, admin list, and
regression on /api/heroic-patrons + /api/donations/create-order (LIVE one-time).
"""
import os
import uuid
import pytest
import requests
import sys
import asyncio

sys.path.insert(0, "/app/backend")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://hifi-donations-live.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "admin@heroichifi.org"
ADMIN_PASSWORD = "HHF@admin2024"

PLAN_AMOUNTS = {"monthly": 100, "quarterly": 275, "half_yearly": 525, "annual": 1000}


@pytest.fixture(scope="module")
def admin_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=20)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    token = r.json().get("token") or r.json().get("access_token")
    s.headers.update({"Authorization": f"Bearer {token}"})
    return s


@pytest.fixture(scope="module")
def seeded_user():
    """Seed a member user directly via Mongo (bypass OTP) and return JWT client."""
    from config import db
    from utils.auth import hash_password, create_access_token
    from datetime import datetime, timezone

    email = f"test_livesub_{uuid.uuid4().hex[:8]}@example.com"

    async def _seed():
        await db.users.delete_one({"email": email})
        doc = {
            "name": "Live Sub Tester",
            "email": email,
            "password_hash": hash_password("Patron@2026"),
            "phone": "9999999999",
            "role": "member",
            "email_verified": True,
            "volunteer_hours": 0, "badges": [], "specializations": [],
            "profile_pic_path": "", "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        result = await db.users.insert_one(doc)
        return str(result.inserted_id)

    user_id = asyncio.new_event_loop().run_until_complete(_seed())
    token = create_access_token(user_id, email)
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    return {"client": s, "email": email}


# ── 1. Auth required ──
class TestSubscriptionAuth:
    def test_create_requires_auth(self):
        r = requests.post(f"{BASE_URL}/api/subscriptions/create", json={
            "plan": "monthly", "name": "X", "email": "x@x.com",
            "phone": "9999999999", "pan_number": "ABCDE1234F",
        }, timeout=20)
        assert r.status_code in (401, 403), f"expected 401/403 got {r.status_code}"


# ── 2. Invalid plan rejected ──
class TestPlanValidation:
    def test_invalid_plan_returns_400(self, seeded_user):
        r = seeded_user["client"].post(f"{BASE_URL}/api/subscriptions/create", json={
            "plan": "invalid",
            "name": "Tester", "email": seeded_user["email"],
            "phone": "9999999999", "pan_number": "ABCDE1234F",
        }, timeout=20)
        assert r.status_code == 400
        body = r.json()
        assert "Plan must be one of" in (body.get("detail") or "")


# ── 3. LIVE subscription creation for all 4 plans ──
class TestLiveSubscriptionCreate:
    @pytest.mark.parametrize("plan,expected_amount", list(PLAN_AMOUNTS.items()))
    def test_create_live_sub(self, seeded_user, plan, expected_amount):
        # Send malicious 'amount' field — backend MUST ignore it
        payload = {
            "plan": plan,
            "name": "Live Tester",
            "email": seeded_user["email"],
            "phone": "9999999999",
            "pan_number": "ABCDE1234F",
            "address": "Test Addr",
            "amount": 1,  # extra field, ignored by Pydantic + server uses PLAN_AMOUNTS
        }
        r = seeded_user["client"].post(f"{BASE_URL}/api/subscriptions/create", json=payload, timeout=30)
        assert r.status_code == 200, f"plan={plan} status={r.status_code} body={r.text}"
        data = r.json()
        sub = data["subscription"]

        assert sub["plan"] == plan
        assert sub["amount"] == expected_amount, f"plan={plan} stored amount={sub['amount']} expected={expected_amount}"
        assert data.get("mode") == "live", f"plan={plan} mode={data.get('mode')} (expected live). full={data}"

        rz_sub_id = data.get("razorpay_subscription_id") or sub.get("razorpay_subscription_id")
        assert rz_sub_id and rz_sub_id.startswith("sub_"), f"plan={plan} razorpay_subscription_id={rz_sub_id!r}"

        short_url = data.get("short_url") or sub.get("short_url", "")
        assert short_url.startswith("https://rzp.io/") or short_url.startswith("https://"), \
            f"plan={plan} short_url={short_url!r}"

        assert data.get("razorpay_key") == "rzp_live_SiX7Z60muB4Hpg"


# ── 4. Admin lists subscriptions ──
class TestAdminListsSubscriptions:
    def test_admin_can_list(self, admin_client):
        r = admin_client.get(f"{BASE_URL}/api/admin/subscriptions", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        # Find at least one with mode=live
        live_subs = [s for s in data if s.get("mode") == "live"]
        assert len(live_subs) >= 1, f"No live mode subs found in admin list (total={len(data)})"
        for s in live_subs[:5]:
            assert "_id" not in s

    def test_non_admin_blocked(self, seeded_user):
        r = seeded_user["client"].get(f"{BASE_URL}/api/admin/subscriptions", timeout=20)
        assert r.status_code in (401, 403)


# ── 5. Regression: heroic-patrons still works ──
class TestHeroicPatronsRegression:
    def test_public_endpoint(self):
        r = requests.get(f"{BASE_URL}/api/heroic-patrons", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        for e in data:
            assert e.get("tier") == "heroic_patron"
            assert "_id" not in e


# ── 6. Regression: one-time donation order with LIVE keys ──
class TestOneTimeDonationLive:
    def test_create_order_live(self, seeded_user):
        payload = {
            "name": "Live Donor",
            "email": seeded_user["email"],
            "phone": "9999999999",
            "amount": 500,
            "pan_number": "ABCDE1234F",
            "address": "X",
            "message": "live test",
        }
        # Logged-in flow: no otp_token required (auth route bypasses OTP for users)
        r = seeded_user["client"].post(f"{BASE_URL}/api/donations/create-order", json=payload, timeout=30)
        assert r.status_code == 200, f"{r.status_code} {r.text}"
        data = r.json()
        order_id = data.get("razorpay_order_id", "")
        assert order_id.startswith("order_"), f"order_id={order_id!r} body={data}"
        assert data.get("razorpay_key") == "rzp_live_SiX7Z60muB4Hpg", f"key={data.get('razorpay_key')}"
        assert data.get("amount") == 500 * 100  # paise
