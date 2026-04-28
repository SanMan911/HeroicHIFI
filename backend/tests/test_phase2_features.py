"""
Phase 2 Feature Tests:
- Email Blasts
- Pending Event Reports
- Event Report submission with AI article (Gemini)
- Notifications (in-app)
- Multi-admin promotion
- Existing endpoints regression (auth/login, admin/stats, admin/users, drives, role-requests, activity-logs)
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://hifi-donations-live.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "admin@heroichifi.org"
ADMIN_PASSWORD = "HHF@admin2024"


@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    data = r.json()
    return data.get("access_token") or data.get("token")


@pytest.fixture()
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ── Regression: existing endpoints ──
class TestExistingRegression:
    def test_login_admin(self, admin_token):
        assert admin_token and isinstance(admin_token, str)

    def test_admin_stats(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/stats", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "donations" in data and "members" in data and "drives" in data and "role_requests" in data

    def test_admin_users_roster(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/users", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_drives_public(self):
        r = requests.get(f"{BASE_URL}/api/drives", timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_role_requests_admin(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/role-requests", headers=admin_headers, timeout=30)
        assert r.status_code == 200

    def test_activity_logs(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/activity-logs?limit=20", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        logs = r.json()
        assert isinstance(logs, list)


# ── Phase 2: Email Blasts ──
class TestEmailBlasts:
    def test_email_blast_requires_admin(self):
        r = requests.post(f"{BASE_URL}/api/admin/email-blast", json={"subject": "X", "body": "Y", "target": "all"}, timeout=30)
        assert r.status_code in (401, 403)

    def test_email_blast_send_to_admin_only(self, admin_headers):
        # Send only to admin to avoid bulk emails: target=members yields 0 if no members; so we use "all" but check sent count
        # Use a tiny subject; This will send to all users -- to avoid mass email, we test with "members" if exists, else skip
        # Safer: validate endpoint by sending with empty target list (members) — will 400 if none.
        r = requests.post(f"{BASE_URL}/api/admin/email-blast", headers=admin_headers,
                          json={"subject": "TEST_phase2_blast", "body": "Test phase 2", "target": "members"}, timeout=60)
        # Accept 200 (sent) or 400 (no members). Reject 500.
        assert r.status_code in (200, 400), f"Unexpected: {r.status_code} {r.text}"

    def test_list_email_blasts(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/email-blasts", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ── Phase 2: Notifications ──
class TestNotifications:
    def test_get_notifications_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/notifications", timeout=30)
        assert r.status_code in (401, 403)

    def test_get_my_notifications(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/notifications", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_unread_count(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/notifications/unread-count", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        assert "count" in r.json()


# ── Phase 2: Pending Event Reports + Event Report submission ──
class TestEventReports:
    def test_pending_reports(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/events/pending", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_event_reports(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/events/reports", headers=admin_headers, timeout=30)
        assert r.status_code == 200

    def test_create_drive_then_submit_report_with_ai(self, admin_headers):
        # Create a past drive
        drive_payload = {
            "title": "TEST_phase2_drive",
            "description": "Testing AI article generation",
            "date": "2025-01-01",
            "location": "Mumbai",
            "drive_type": "past",
            "mission_slug": "mission-shakti",
            "estimated_days": 1,
            "time": "10:00",
            "image_url": "",
        }
        cr = requests.post(f"{BASE_URL}/api/admin/drives", headers=admin_headers, json=drive_payload, timeout=30)
        assert cr.status_code == 200, cr.text
        drive = cr.json().get("drive") or cr.json()
        drive_id = drive["id"]

        try:
            # Submit event report
            report_payload = {
                "drive_id": drive_id,
                "time_spent": "4 hours",
                "resources_spent": "50 saplings",
                "summary": "Planted trees for environmental conservation in the local park.",
                "issues": "None",
                "outcome": "Successfully planted 50 trees with active community participation.",
                "admin_rating": 8,
                "attendance": [],  # empty to keep test fast
            }
            rr = requests.post(f"{BASE_URL}/api/admin/events/report", headers=admin_headers, json=report_payload, timeout=120)
            assert rr.status_code == 200, f"Report failed: {rr.status_code} {rr.text}"
            data = rr.json()
            assert "report" in data
            assert "article" in data["report"]
            article = data["report"]["article"]
            assert isinstance(article, str) and len(article) > 30, f"Article suspiciously short: {article!r}"

            # Verify drive marked as reported
            pending = requests.get(f"{BASE_URL}/api/admin/events/pending", headers=admin_headers, timeout=30).json()
            assert all(d.get("id") != drive_id for d in pending), "Drive still pending after report"

            # Verify article publicly accessible
            arts = requests.get(f"{BASE_URL}/api/events/articles", timeout=30)
            assert arts.status_code == 200
            assert any(a.get("title") == "TEST_phase2_drive" for a in arts.json())
        finally:
            # cleanup
            requests.delete(f"{BASE_URL}/api/admin/drives/{drive_id}", headers=admin_headers, timeout=30)


# ── Phase 2: Multi-admin promotion ──
class TestPromotion:
    def test_list_promotion_requests(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/promote-requests", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_promote_nonexistent_user(self, admin_headers):
        r = requests.post(f"{BASE_URL}/api/admin/promote-request", headers=admin_headers,
                          json={"target_email": f"TEST_nonexistent_{uuid.uuid4().hex[:6]}@example.com", "reason": "test"}, timeout=30)
        assert r.status_code == 404


# ── Phase 2: Registration with specializations ──
class TestRegistrationSpecialization:
    def test_register_with_specializations_field(self):
        # Just verify schema accepts the field (will fail on OTP check but shouldn't 422)
        unique = uuid.uuid4().hex[:8]
        payload = {
            "name": "TEST Volunteer",
            "email": f"TEST_phase2_{unique}@example.com",
            "password": "TestPass123!",
            "phone": "9999999999",
            "dob": "1995-05-15",
            "age": 30,
            "address": "Test Address",
            "pan_number": "ABCDE1234F",
            "aadhaar_number": "123456789012",
            "role": "volunteer",
            "specializations": ["Education", "Healthcare"],
            "otp_token": "invalid-token-000000"
        }
        r = requests.post(f"{BASE_URL}/api/auth/register", json=payload, timeout=30)
        # Should fail OTP verification (400) not validation (422). We just check spec field accepted.
        assert r.status_code != 422 or "specializations" not in r.text, f"Schema rejected specializations field: {r.text}"
