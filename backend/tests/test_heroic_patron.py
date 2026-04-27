"""
Heroic Patron tier — backend regression suite.
Covers:
  - GET /api/heroic-patrons (public, sorted)
  - POST /api/admin/subscriptions/{id}/simulate-charge (admin only)
  - 6-charge promotion → badge + wall_of_fame entry
  - GET /api/admin/patrons/summary/{email}
  - POST /api/admin/patrons/recompute
  - Webhook subscription.charged smoke test (bad signature path)
"""
import os
import uuid
import pytest
import requests

def _load_base_url():
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if not url:
        # fallback: read frontend/.env
        try:
            with open("/app/frontend/.env") as f:
                for line in f:
                    if line.startswith("REACT_APP_BACKEND_URL="):
                        url = line.split("=", 1)[1].strip()
                        break
        except Exception:
            pass
    if not url:
        raise RuntimeError("REACT_APP_BACKEND_URL not set")
    return url.rstrip("/")


BASE_URL = _load_base_url()
ADMIN_EMAIL = "admin@heroichifi.org"
ADMIN_PASSWORD = "HHF@admin2024"


@pytest.fixture(scope="module")
def admin_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if r.status_code != 200:
        pytest.skip(f"Admin login failed: {r.status_code} {r.text}")
    token = r.json().get("token") or r.json().get("access_token")
    s.headers.update({"Authorization": f"Bearer {token}"})
    return s


@pytest.fixture(scope="module")
def test_user_email():
    return f"test_patron_{uuid.uuid4().hex[:8]}@example.com"


@pytest.fixture(scope="module")
def seeded_user(test_user_email):
    """Insert a user directly into MongoDB (bypasses OTP), then login via API."""
    import asyncio
    import sys
    sys.path.insert(0, "/app/backend")
    from config import db  # noqa
    from utils.auth import hash_password, create_access_token  # noqa
    from datetime import datetime, timezone

    password = "Patron@2026"
    pwhash = hash_password(password)

    async def _seed():
        await db.users.delete_one({"email": test_user_email})
        doc = {
            "name": "Test Patron",
            "email": test_user_email,
            "password_hash": pwhash,
            "phone": "9999999999",
            "role": "member",
            "email_verified": True,
            "volunteer_hours": 0,
            "badges": [],
            "specializations": [],
            "profile_pic_path": "",
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        result = await db.users.insert_one(doc)
        return str(result.inserted_id)

    user_id = asyncio.get_event_loop().run_until_complete(_seed()) if False else asyncio.new_event_loop().run_until_complete(_seed())
    token = create_access_token(user_id, test_user_email)

    s = requests.Session()
    s.headers.update({"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    return {"client": s, "email": test_user_email}


@pytest.fixture(scope="module")
def created_subscription(seeded_user):
    """User creates a monthly subscription (stub mode)."""
    payload = {
        "name": "Test Patron",
        "email": seeded_user["email"],
        "phone": "9999999999",
        "pan_number": "ABCDE1234F",
        "plan": "monthly",
        "amount": 500,
    }
    r = seeded_user["client"].post(f"{BASE_URL}/api/subscriptions/create", json=payload)
    assert r.status_code == 200, f"sub create failed: {r.status_code} {r.text}"
    data = r.json()
    sub = data["subscription"]
    assert sub["plan"] == "monthly"
    assert sub["amount"] == 500
    assert sub["status"] in ("placeholder_plan", "active", "created")
    assert "id" in sub
    return sub


# ── 1. GET /api/heroic-patrons (public) ──
class TestHeroicPatronsPublicList:
    def test_returns_list(self):
        r = requests.get(f"{BASE_URL}/api/heroic-patrons")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        # All entries should have tier=heroic_patron
        for entry in data:
            assert entry.get("tier") == "heroic_patron"
            assert "patron_charge_count" in entry
            assert "_id" not in entry  # Mongo ObjectId must be stripped

    def test_sorted_desc_by_charge_count(self):
        r = requests.get(f"{BASE_URL}/api/heroic-patrons")
        assert r.status_code == 200
        data = r.json()
        if len(data) >= 2:
            counts = [e.get("patron_charge_count", 0) for e in data]
            assert counts == sorted(counts, reverse=True), "Not sorted desc"


# ── 2. Simulate charge admin-only auth ──
class TestSimulateChargeAuth:
    def test_requires_admin(self, created_subscription):
        # No auth
        r = requests.post(f"{BASE_URL}/api/admin/subscriptions/{created_subscription['id']}/simulate-charge")
        assert r.status_code in (401, 403)

    def test_404_for_unknown_sub(self, admin_client):
        r = admin_client.post(f"{BASE_URL}/api/admin/subscriptions/does-not-exist-{uuid.uuid4().hex}/simulate-charge")
        assert r.status_code == 404


# ── 3. 6-charge promotion flow ──
class TestPromotionThreshold:
    def test_six_charges_promote_user(self, admin_client, created_subscription, seeded_user):
        sub_id = created_subscription["id"]
        results = []
        for i in range(6):
            r = admin_client.post(f"{BASE_URL}/api/admin/subscriptions/{sub_id}/simulate-charge")
            assert r.status_code == 200, f"charge {i+1} failed: {r.status_code} {r.text}"
            data = r.json()
            assert "patron" in data
            results.append(data["patron"])

        # First 5 must be promoted=False
        for i, p in enumerate(results[:5]):
            assert p.get("promoted") is False, f"charge #{i+1} unexpectedly promoted={p}"

        # 6th charge: promoted=True
        sixth = results[5]
        assert sixth.get("promoted") is True, f"6th charge did not promote: {sixth}"
        assert sixth.get("charge_count") == 6
        assert sixth.get("plan") == "monthly"
        assert sixth.get("total_amount") == 6 * 500

    def test_summary_reflects_qualification(self, admin_client, seeded_user):
        r = admin_client.get(f"{BASE_URL}/api/admin/patrons/summary/{seeded_user['email']}")
        assert r.status_code == 200
        d = r.json()
        assert d["charge_count"] >= 6
        assert d["qualified"] is True
        assert d["plan"] == "monthly"
        assert d["total_amount"] >= 3000

    def test_user_appears_in_public_patrons_list(self, seeded_user):
        r = requests.get(f"{BASE_URL}/api/heroic-patrons")
        assert r.status_code == 200
        data = r.json()
        emails = [e.get("email") for e in data]
        assert seeded_user["email"].lower() in emails, f"Promoted user not in patrons list. Got: {emails}"
        entry = next(e for e in data if e.get("email") == seeded_user["email"].lower())
        assert entry["tier"] == "heroic_patron"
        assert entry["patron_charge_count"] >= 6
        assert entry["patron_plan"] == "monthly"


# ── 4. Patron summary admin endpoint ──
class TestPatronSummaryAuth:
    def test_summary_requires_admin(self, seeded_user):
        r = requests.get(f"{BASE_URL}/api/admin/patrons/summary/{seeded_user['email']}")
        assert r.status_code in (401, 403)

    def test_summary_unknown_user(self, admin_client):
        # Should still return a structured response (count=0, qualified=False)
        unknown = f"TEST_unknown_{uuid.uuid4().hex[:6]}@example.com"
        r = admin_client.get(f"{BASE_URL}/api/admin/patrons/summary/{unknown}")
        assert r.status_code == 200
        d = r.json()
        assert d["charge_count"] == 0
        assert d["qualified"] is False


# ── 5. Recompute admin endpoint ──
class TestRecomputeEndpoint:
    def test_requires_admin(self):
        r = requests.post(f"{BASE_URL}/api/admin/patrons/recompute")
        assert r.status_code in (401, 403)

    def test_recompute_returns_threshold(self, admin_client):
        r = admin_client.post(f"{BASE_URL}/api/admin/patrons/recompute")
        assert r.status_code == 200
        d = r.json()
        assert "checked" in d
        assert "promoted" in d
        assert d.get("threshold") == 6
        assert isinstance(d["checked"], int)


# ── 6. Webhook subscription.charged smoke test ──
class TestWebhookSubscriptionCharged:
    def test_bad_signature_does_not_crash(self):
        # Stub webhook payload mimicking subscription.charged
        payload = {
            "event": "subscription.charged",
            "payload": {
                "subscription": {"entity": {"id": "sub_FAKE_TEST"}},
                "payment": {"entity": {"id": "pay_FAKE_TEST", "amount": 50000}},
            },
        }
        r = requests.post(
            f"{BASE_URL}/api/subscriptions/webhook",
            json=payload,
            headers={"x-razorpay-signature": "bogus"},
        )
        # With placeholder webhook secret signature is invalid -> verified:false but 200
        assert r.status_code == 200
        d = r.json()
        assert d.get("verified") is False
        assert d.get("status") == "received"
