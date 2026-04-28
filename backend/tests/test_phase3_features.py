"""
Phase 3 feature tests:
- Razorpay Subscriptions (create/mine/cancel/admin-list/webhook)
- Sandbox PAN verification (per-user + adhoc)
- Admin user delete with mandatory reason
- Admin user suspend with mandatory reason
- Star Hero aggregate smoke
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://hifi-volunteer-hub.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@heroichifi.org"
ADMIN_PASSWORD = "HHF@admin2024"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=20)
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ── Subscriptions ──────────────────────────────────────────────────────────
class TestSubscriptions:
    sub_id = None

    def test_create_subscription_monthly_stub(self, admin_headers):
        payload = {
            "plan": "monthly", "amount": 500,
            "name": "TEST_Sub_User", "email": "test_sub@example.com",
            "phone": "9999999999", "pan_number": "ABCDE1234F",
            "address": "Bangalore",
        }
        r = requests.post(f"{API}/subscriptions/create", json=payload, headers=admin_headers, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["mode"] == "stub"
        assert data["subscription"]["status"] == "placeholder_plan"
        assert data["subscription"]["plan"] == "monthly"
        assert data["subscription"]["amount"] == 500
        assert "id" in data["subscription"]
        TestSubscriptions.sub_id = data["subscription"]["id"]

    def test_create_subscription_invalid_plan(self, admin_headers):
        r = requests.post(f"{API}/subscriptions/create", json={
            "plan": "weekly", "amount": 500, "name": "x", "email": "x@e.com",
            "phone": "1", "pan_number": "ABCDE1234F",
        }, headers=admin_headers, timeout=15)
        assert r.status_code == 400

    def test_create_subscription_min_amount(self, admin_headers):
        r = requests.post(f"{API}/subscriptions/create", json={
            "plan": "monthly", "amount": 50, "name": "x", "email": "x@e.com",
            "phone": "1", "pan_number": "ABCDE1234F",
        }, headers=admin_headers, timeout=15)
        assert r.status_code == 400

    def test_subscriptions_mine(self, admin_headers):
        r = requests.get(f"{API}/subscriptions/mine", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert any(s["id"] == TestSubscriptions.sub_id for s in data)

    def test_admin_subscriptions_list(self, admin_headers):
        r = requests.get(f"{API}/admin/subscriptions", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert any(s["id"] == TestSubscriptions.sub_id for s in data)

    def test_admin_subscriptions_requires_admin(self):
        r = requests.get(f"{API}/admin/subscriptions", timeout=15)
        assert r.status_code in (401, 403)

    def test_cancel_subscription(self, admin_headers):
        assert TestSubscriptions.sub_id, "Need sub_id from create test"
        r = requests.post(f"{API}/subscriptions/{TestSubscriptions.sub_id}/cancel",
                          headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        # Verify status changed
        r2 = requests.get(f"{API}/subscriptions/mine", headers=admin_headers, timeout=15)
        match = next((s for s in r2.json() if s["id"] == TestSubscriptions.sub_id), None)
        assert match is not None
        assert match["status"] == "cancelled"
        assert match["cancelled_at"] is not None

    def test_cancel_subscription_not_found(self, admin_headers):
        r = requests.post(f"{API}/subscriptions/nonexistent-id/cancel",
                          headers=admin_headers, timeout=15)
        assert r.status_code == 404

    def test_webhook_invalid_signature(self):
        body = {"event": "subscription.charged", "payload": {}}
        r = requests.post(f"{API}/subscriptions/webhook", json=body,
                          headers={"x-razorpay-signature": "deadbeef"}, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["verified"] is False
        assert data["status"] == "received"


# ── PAN Verification ───────────────────────────────────────────────────────
class TestPANVerification:
    def test_verify_pan_adhoc_placeholder(self, admin_headers):
        r = requests.post(f"{API}/admin/verify-pan-adhoc", json={
            "pan": "ABCDE1234F", "aadhaar": "123456789012", "name": "Test User",
        }, headers=admin_headers, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["pan"]["status"] == "placeholder_keys"
        assert data["pan"]["mode"] == "stub"
        assert data["aadhaar_link"]["status"] == "placeholder_keys"

    def test_verify_pan_adhoc_invalid_format(self, admin_headers):
        r = requests.post(f"{API}/admin/verify-pan-adhoc", json={
            "pan": "INVALID", "name": "Test User",
        }, headers=admin_headers, timeout=15)
        assert r.status_code == 200
        assert r.json()["pan"]["status"] == "invalid_format"

    def test_verify_pan_adhoc_requires_admin(self):
        r = requests.post(f"{API}/admin/verify-pan-adhoc",
                          json={"pan": "ABCDE1234F", "name": "x"}, timeout=15)
        assert r.status_code in (401, 403)

    def test_verify_pan_user(self, admin_headers):
        # Admin user has no PAN -> 400. Try with an existing user via list.
        r = requests.get(f"{API}/admin/users", headers=admin_headers, timeout=20)
        assert r.status_code == 200
        users = r.json()
        target = next((u for u in users if u.get("pan_number")), None)
        if not target:
            pytest.skip("No user with PAN on file")
        r2 = requests.post(f"{API}/admin/users/{target['email']}/verify-pan",
                           headers=admin_headers, timeout=20)
        assert r2.status_code == 200, r2.text
        data = r2.json()
        assert data["status"] == "placeholder_keys"
        assert data["mode"] == "stub"

    def test_verify_pan_user_not_found(self, admin_headers):
        r = requests.post(f"{API}/admin/users/nonexistent@example.com/verify-pan",
                          headers=admin_headers, timeout=15)
        assert r.status_code == 404


# ── Admin User Delete with Mandatory Reason ─────────────────────────────────
class TestAdminDeleteUser:
    test_email = None

    @pytest.fixture(autouse=True, scope="class")
    def _create_test_user(self, admin_headers):
        # Create a throwaway user via OTP-bypassing path: use direct DB via register endpoint?
        # Instead, just attempt delete on a fake user and check 400/404 behaviors.
        TestAdminDeleteUser.test_email = f"test_delete_{uuid.uuid4().hex[:6]}@example.com"
        yield

    def test_delete_user_requires_reason(self, admin_headers):
        # No body
        r = requests.delete(f"{API}/admin/users/some@example.com",
                            headers=admin_headers, timeout=15)
        # FastAPI may 422 on missing body schema
        assert r.status_code in (400, 422)

    def test_delete_user_short_reason(self, admin_headers):
        r = requests.delete(f"{API}/admin/users/some@example.com",
                            json={"reason": "ok"}, headers=admin_headers, timeout=15)
        assert r.status_code == 400

    def test_delete_user_not_found(self, admin_headers):
        r = requests.delete(f"{API}/admin/users/nope_{uuid.uuid4().hex[:5]}@example.com",
                            json={"reason": "Removed for testing — valid reason"},
                            headers=admin_headers, timeout=15)
        assert r.status_code == 404

    def test_delete_self_blocked(self, admin_headers):
        r = requests.delete(f"{API}/admin/users/{ADMIN_EMAIL}",
                            json={"reason": "Removing self test"},
                            headers=admin_headers, timeout=15)
        assert r.status_code == 400


# ── Admin Suspend User with Reason ──────────────────────────────────────────
class TestAdminSuspendUser:
    def test_suspend_requires_reason(self, admin_headers):
        # Suspend admin (against self) - first find any non-admin user, else use admin self
        r = requests.get(f"{API}/admin/users", headers=admin_headers, timeout=20)
        users = r.json()
        target = next((u for u in users if u.get("role") != "admin"), None)
        if not target:
            pytest.skip("No non-admin user available")
        # No reason -> 400
        r2 = requests.put(f"{API}/admin/users/{target['email']}/update",
                          json={"status": "suspended"}, headers=admin_headers, timeout=15)
        assert r2.status_code == 400, r2.text

    def test_suspend_short_reason(self, admin_headers):
        r = requests.get(f"{API}/admin/users", headers=admin_headers, timeout=20)
        users = r.json()
        target = next((u for u in users if u.get("role") != "admin"), None)
        if not target:
            pytest.skip("No non-admin user available")
        r2 = requests.put(f"{API}/admin/users/{target['email']}/update",
                          json={"status": "suspended", "suspension_reason": "ok"},
                          headers=admin_headers, timeout=15)
        assert r2.status_code == 400

    def test_suspend_with_valid_reason_then_unsuspend(self, admin_headers):
        r = requests.get(f"{API}/admin/users", headers=admin_headers, timeout=20)
        users = r.json()
        target = next((u for u in users if u.get("role") != "admin" and u.get("status") != "suspended"), None)
        if not target:
            pytest.skip("No suitable user")
        email = target["email"]
        r2 = requests.put(f"{API}/admin/users/{email}/update",
                          json={"status": "suspended", "suspension_reason": "Violated community guidelines (test)"},
                          headers=admin_headers, timeout=15)
        assert r2.status_code == 200, r2.text
        # Verify
        r3 = requests.get(f"{API}/admin/users", headers=admin_headers, timeout=20)
        u = next((x for x in r3.json() if x["email"] == email), None)
        assert u and u["status"] == "suspended"
        assert u.get("suspended_by") == ADMIN_EMAIL
        assert u.get("suspension_reason", "").startswith("Violated")
        # Unsuspend
        r4 = requests.put(f"{API}/admin/users/{email}/update",
                          json={"status": "active"}, headers=admin_headers, timeout=15)
        assert r4.status_code == 200


# ── Star Hero aggregate smoke test ──────────────────────────────────────────
class TestStarHeroAggregate:
    def test_pending_events_endpoint(self, admin_headers):
        r = requests.get(f"{API}/admin/events/pending", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_admin_stats_includes_verification(self, admin_headers):
        r = requests.get(f"{API}/admin/stats", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "verification" in data
        assert "pan_verified" in data["verification"]
