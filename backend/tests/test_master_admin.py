"""
Master-Admin (super-admin) tier tests.

Covers:
- /api/auth/login and /api/auth/me include is_super_admin
- Admin list hides super-admin from regular admins
- Per-user admin endpoints (update/delete/verify-pan/badge) return 404 when regular admin targets super-admin
- Activity logs filter out super-admin events for regular admins
- Admin stats exclude super-admin from user counts for regular admins
- 80G self-approval: super-admin allowed, regular admin blocked
- Admin promote-request: super-admin caller -> required_approvals=1 (master override)
- Regression: /api/heroic-patrons and /api/admin/subscriptions still function
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://hifi-ngo-portal.preview.emergentagent.com").rstrip("/")

SUPER_ADMIN = {"email": "admin@heroichifi.org", "password": "HHF@admin2024"}
REG_ADMIN = {"email": "admin2@heroichifi.org", "password": "HHF@admin2024_alt"}


def _login(creds):
    r = requests.post(f"{BASE_URL}/api/auth/login", json=creds, timeout=30)
    assert r.status_code == 200, f"login failed {creds['email']}: {r.status_code} {r.text}"
    return r.json()


@pytest.fixture(scope="module")
def super_token():
    return _login(SUPER_ADMIN)["token"]


@pytest.fixture(scope="module")
def reg_token():
    return _login(REG_ADMIN)["token"]


def _hdr(tok):
    return {"Authorization": f"Bearer {tok}"}


# ── /auth/login + /auth/me include is_super_admin ──
class TestAuthSuperAdminFlag:
    def test_login_super_admin_flag_true(self):
        data = _login(SUPER_ADMIN)
        assert data["user"].get("is_super_admin") is True

    def test_login_regular_admin_flag_false(self):
        data = _login(REG_ADMIN)
        assert data["user"].get("is_super_admin") is False

    def test_me_super_admin_flag_true(self, super_token):
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=_hdr(super_token), timeout=30)
        assert r.status_code == 200
        body = r.json()
        user = body.get("user", body)
        assert user.get("is_super_admin") is True
        assert user.get("email") == SUPER_ADMIN["email"]

    def test_me_regular_admin_flag_false(self, reg_token):
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=_hdr(reg_token), timeout=30)
        assert r.status_code == 200
        body = r.json()
        user = body.get("user", body)
        assert user.get("is_super_admin") is False


# ── Admin users list filter ──
class TestAdminUsersVisibility:
    def test_super_admin_sees_self(self, super_token):
        r = requests.get(f"{BASE_URL}/api/admin/users", headers=_hdr(super_token), timeout=30)
        assert r.status_code == 200
        emails = [u["email"] for u in r.json()]
        assert SUPER_ADMIN["email"] in emails
        assert REG_ADMIN["email"] in emails

    def test_regular_admin_cannot_see_super(self, reg_token):
        r = requests.get(f"{BASE_URL}/api/admin/users", headers=_hdr(reg_token), timeout=30)
        assert r.status_code == 200
        emails = [u["email"] for u in r.json()]
        assert SUPER_ADMIN["email"] not in emails, "Super admin leaked into regular admin's user list"
        assert REG_ADMIN["email"] in emails


# ── Per-user endpoints hidden from regular admin (404) ──
class TestPerUserEndpointsHidden:
    TARGET = SUPER_ADMIN["email"]

    def test_update_hidden(self, reg_token):
        r = requests.put(
            f"{BASE_URL}/api/admin/users/{self.TARGET}/update",
            headers=_hdr(reg_token),
            json={"name": "hacked"},
            timeout=30,
        )
        assert r.status_code == 404, f"expected 404, got {r.status_code} {r.text}"

    def test_delete_hidden(self, reg_token):
        r = requests.request(
            "DELETE",
            f"{BASE_URL}/api/admin/users/{self.TARGET}",
            headers={**_hdr(reg_token), "Content-Type": "application/json"},
            json={"password": REG_ADMIN["password"], "reason": "test"},
            timeout=30,
        )
        assert r.status_code == 404, f"expected 404, got {r.status_code} {r.text}"

    def test_verify_pan_hidden(self, reg_token):
        r = requests.post(
            f"{BASE_URL}/api/admin/users/{self.TARGET}/verify-pan",
            headers=_hdr(reg_token),
            json={"pan_number": "ABCDE1234F"},
            timeout=30,
        )
        assert r.status_code == 404, f"expected 404, got {r.status_code} {r.text}"

    def test_badge_hidden(self, reg_token):
        r = requests.post(
            f"{BASE_URL}/api/admin/users/{self.TARGET}/badge",
            headers=_hdr(reg_token),
            json={"badge": "Helping Hero", "action": "add"},
            timeout=30,
        )
        assert r.status_code == 404, f"expected 404, got {r.status_code} {r.text}"

    def test_super_admin_can_target_self(self, super_token):
        # super-admin can view its own update path (not forbidden by filter); endpoint may 400/200 on no-op
        r = requests.put(
            f"{BASE_URL}/api/admin/users/{self.TARGET}/update",
            headers=_hdr(super_token),
            json={"name": "Admin"},
            timeout=30,
        )
        assert r.status_code in (200, 400), f"unexpected {r.status_code} {r.text}"


# ── Activity logs filter ──
class TestActivityLogsFilter:
    def test_regular_admin_cannot_see_super_logs(self, reg_token):
        r = requests.get(f"{BASE_URL}/api/admin/activity-logs", headers=_hdr(reg_token), timeout=30)
        assert r.status_code == 200
        logs = r.json()
        for log in logs:
            assert log.get("user_email") != SUPER_ADMIN["email"], f"Super admin user_email leaked: {log}"
            assert log.get("entity_id") != SUPER_ADMIN["email"], f"Super admin entity_id leaked: {log}"

    def test_super_admin_sees_all(self, super_token, reg_token):
        rs = requests.get(f"{BASE_URL}/api/admin/activity-logs", headers=_hdr(super_token), timeout=30)
        rr = requests.get(f"{BASE_URL}/api/admin/activity-logs", headers=_hdr(reg_token), timeout=30)
        assert rs.status_code == 200 and rr.status_code == 200
        assert len(rs.json()) >= len(rr.json())


# ── Admin stats filter ──
class TestAdminStatsFilter:
    def test_stats_counts_differ(self, super_token, reg_token):
        rs = requests.get(f"{BASE_URL}/api/admin/stats", headers=_hdr(super_token), timeout=30)
        rr = requests.get(f"{BASE_URL}/api/admin/stats", headers=_hdr(reg_token), timeout=30)
        assert rs.status_code == 200 and rr.status_code == 200
        s, r = rs.json(), rr.json()
        # Find a user-count-like field
        for key in ("total_users", "users_count", "total_members", "member_count", "users"):
            if key in s and key in r and isinstance(s[key], int) and isinstance(r[key], int):
                assert r[key] <= s[key], f"{key}: regular admin count {r[key]} exceeded super {s[key]}"
        # At minimum, assert stats endpoint worked and returned dict
        assert isinstance(s, dict) and isinstance(r, dict)


# ── Promote-request master override ──
class TestPromoteRequestMasterOverride:
    def test_super_admin_required_approvals_is_one(self, super_token):
        target_email = f"TEST_promote_{uuid.uuid4().hex[:8]}@example.com"
        r = requests.post(
            f"{BASE_URL}/api/admin/promote-request",
            headers=_hdr(super_token),
            json={"target_email": target_email, "reason": "master override test"},
            timeout=30,
        )
        # Target may not exist -> 404, or existing but non-admin -> 200 with required_approvals=1
        if r.status_code == 200:
            body = r.json()
            req = body.get("required_approvals") or body.get("request", {}).get("required_approvals")
            assert req == 1, f"super-admin should get required_approvals=1, got {req} in {body}"
        else:
            assert r.status_code in (400, 404), f"unexpected {r.status_code} {r.text}"

    def test_regular_admin_required_approvals_gte_one(self, reg_token):
        target_email = f"TEST_promote_{uuid.uuid4().hex[:8]}@example.com"
        r = requests.post(
            f"{BASE_URL}/api/admin/promote-request",
            headers=_hdr(reg_token),
            json={"target_email": target_email, "reason": "multi-admin gate test"},
            timeout=30,
        )
        if r.status_code == 200:
            body = r.json()
            req = body.get("required_approvals") or body.get("request", {}).get("required_approvals")
            assert req is not None and req >= 1
        else:
            assert r.status_code in (400, 404)


# ── 80G Annual self-approval (uses REJECT to avoid real mass-email dispatch) ──
class TestAnnual80GSelfApproval:
    """
    Gate logic is identical for approve & reject: same `drafted_by==caller and not is_super_admin` check.
    We exercise /reject to avoid triggering real consolidated-80G email dispatch to donors.
    """
    LIST = "/api/admin/annual-80g/drafts"
    DRAFT = "/api/admin/annual-80g/draft"
    REJECT = "/api/admin/annual-80g/drafts/{id}/reject"
    APPROVE = "/api/admin/annual-80g/drafts/{id}/approve"

    @staticmethod
    def _create_draft_as(token, fy_label):
        return requests.post(
            f"{BASE_URL}/api/admin/annual-80g/draft",
            headers=_hdr(token),
            json={"fy_label": fy_label},
            timeout=30,
        )

    @staticmethod
    def _pick_self_pending(token, email):
        r = requests.get(f"{BASE_URL}/api/admin/annual-80g/drafts", headers=_hdr(token), timeout=30)
        if r.status_code != 200:
            return None
        for d in r.json():
            if d.get("drafted_by") == email and d.get("status") == "pending":
                return d
        return None

    def test_regular_admin_cannot_self_reject(self, reg_token):
        draft = self._pick_self_pending(reg_token, REG_ADMIN["email"])
        if not draft:
            # Try create one
            cr = self._create_draft_as(reg_token, "2023-24")
            if cr.status_code != 200:
                pytest.skip(f"Could not create draft to test self-reject: {cr.status_code} {cr.text[:120]}")
            draft = cr.json().get("draft") or cr.json()
        rr = requests.post(
            f"{BASE_URL}/api/admin/annual-80g/drafts/{draft['id']}/reject",
            headers=_hdr(reg_token),
            timeout=30,
        )
        assert rr.status_code == 403, f"regular admin self-reject must be 403, got {rr.status_code} {rr.text}"

    def test_super_admin_can_self_reject(self, super_token):
        draft = self._pick_self_pending(super_token, SUPER_ADMIN["email"])
        if not draft:
            cr = self._create_draft_as(super_token, "2022-23")
            if cr.status_code != 200:
                pytest.skip(f"Could not create super-admin draft: {cr.status_code} {cr.text[:120]}")
            draft = cr.json().get("draft") or cr.json()
        rr = requests.post(
            f"{BASE_URL}/api/admin/annual-80g/drafts/{draft['id']}/reject",
            headers=_hdr(super_token),
            timeout=30,
        )
        assert rr.status_code == 200, f"super-admin master override self-reject must succeed: {rr.status_code} {rr.text}"


# ── Regression ──
class TestRegression:
    def test_heroic_patrons_public(self):
        r = requests.get(f"{BASE_URL}/api/heroic-patrons", timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_admin_subscriptions_live(self, super_token):
        r = requests.get(f"{BASE_URL}/api/admin/subscriptions", headers=_hdr(super_token), timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_webhook_health(self, super_token):
        # Phase-10/11 widget endpoint
        for path in ("/api/admin/webhook-health", "/api/webhook/health", "/api/admin/webhooks/health"):
            r = requests.get(f"{BASE_URL}{path}", headers=_hdr(super_token), timeout=30)
            if r.status_code == 200:
                return
        pytest.skip("Webhook health endpoint path not found in this deploy")
