"""
P0 Cover-Fee + P2 Admin CSV Export tests.

Covers:
  - GET /api/donations/mine returns only signed-in donor's donations w/ fee_covered & gross_amount.
  - GET /api/admin/export/{roster,donations,activity}.csv:
      • text/csv content-type, header rows correct
      • Master-admin row hidden from regular admin in roster CSV
      • Master-admin actions hidden from regular admin in activity CSV
      • Non-admin (volunteer/member) -> 403
"""
import os
import csv
import io
import uuid
import time
import pytest
import requests

def _read_frontend_env():
    p = "/app/frontend/.env"
    if os.path.exists(p):
        for line in open(p):
            if line.strip().startswith("REACT_APP_BACKEND_URL="):
                return line.strip().split("=", 1)[1]
    return None

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or _read_frontend_env() or "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL not set"
API = f"{BASE_URL}/api"

SUPER = {"email": "admin@heroichifi.org", "password": "HHF@admin2024"}
REG = {"email": "admin2@heroichifi.org", "password": "HHF@admin2024_alt"}


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=20)
    if r.status_code != 200:
        return None
    return r.json().get("token")


@pytest.fixture(scope="module")
def super_token():
    t = _login(SUPER)
    if not t:
        pytest.skip("super admin login failed")
    return t


@pytest.fixture(scope="module")
def reg_token():
    t = _login(REG)
    if not t:
        # Fallback: maybe the password got rotated
        t2 = _login({"email": REG["email"], "password": "HHF@admin2024"})
        if not t2:
            pytest.skip("regular admin login failed (password mismatch)")
        return t2
    return t


@pytest.fixture(scope="module")
def mongo_env():
    """Read MONGO_URL/DB_NAME from backend/.env if not in process env."""
    mu = os.environ.get("MONGO_URL")
    dn = os.environ.get("DB_NAME")
    if not (mu and dn):
        try:
            for line in open("/app/backend/.env"):
                k, _, v = line.strip().partition("=")
                v = v.strip().strip('"').strip("'")
                if k == "MONGO_URL" and not mu:
                    mu = v
                if k == "DB_NAME" and not dn:
                    dn = v
        except Exception:
            pass
    return mu, dn


@pytest.fixture(scope="module")
def member_token(mongo_env):
    """Seed a verified volunteer user directly in DB so we can login without OTP flow."""
    mu, dn = mongo_env
    if not (mu and dn):
        pytest.skip("mongo env not available for seeding test member")
    email = f"test_member_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPass@123"
    try:
        from pymongo import MongoClient
        import sys
        sys.path.insert(0, "/app/backend")
        from utils.auth import hash_password
        cli = MongoClient(mu)
        cli[dn]["users"].insert_one({
            "email": email, "name": "Test Member", "phone": "9999900000",
            "role": "volunteer", "designation": "Volunteer",
            "specializations": ["Education", "Healthcare", "Environment"],
            "password_hash": hash_password(password),
            "email_verified": True,
            "pan_number": "", "aadhaar_number": "", "address": "",
            "age": 25, "dob": "2000-01-01",
            "created_at": "2026-01-01T00:00:00+00:00",
        })
        cli.close()
    except Exception as e:
        pytest.skip(f"could not seed test member: {e}")
    t = _login({"email": email, "password": password})
    if not t:
        pytest.skip("seeded volunteer login failed")
    yield t, email
    try:
        from pymongo import MongoClient
        cli = MongoClient(mu); cli[dn]["users"].delete_one({"email": email}); cli.close()
    except Exception:
        pass


# ── /api/donations/mine ──────────────────────────────────────────────
class TestDonationsMine:
    def test_mine_admin_returns_list(self, super_token):
        r = requests.get(f"{API}/donations/mine", headers={"Authorization": f"Bearer {super_token}"}, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        # Each row should have defaults applied
        for d in data:
            assert "fee_covered" in d
            assert "gross_amount" in d
            assert d.get("email", "").lower() == SUPER["email"].lower()

    def test_mine_seeded_row_with_fee(self, super_token, mongo_env):
        """Seed a donation in DB for super admin email then verify it surfaces."""
        from pymongo import MongoClient
        mongo_url, db_name = mongo_env
        if not mongo_url or not db_name:
            pytest.skip("Mongo env not exposed in test env")
        cli = MongoClient(mongo_url)
        coll = cli[db_name]["donations"]
        did = f"TEST_DON_{uuid.uuid4().hex[:8]}"
        try:
            coll.insert_one({
                "id": did, "name": "Admin", "email": SUPER["email"],
                "phone": "9000000000", "amount": 1000,
                "fee_covered": 24, "gross_amount": 1024,
                "pan_number": "ABCDE1234F", "status": "confirmed",
                "created_at": "2026-01-01T00:00:00+00:00",
            })
            r = requests.get(f"{API}/donations/mine", headers={"Authorization": f"Bearer {super_token}"}, timeout=20)
            assert r.status_code == 200
            rows = r.json()
            row = next((x for x in rows if x.get("id") == did), None)
            assert row is not None, "seeded donation not returned"
            assert row["fee_covered"] == 24
            assert row["gross_amount"] == 1024
            assert row["amount"] == 1000
            assert row["status"] == "confirmed"
            assert row.get("pan_number") == "ABCDE1234F"
        finally:
            coll.delete_one({"id": did})
            cli.close()

    def test_mine_isolated_per_user(self, super_token, reg_token):
        r1 = requests.get(f"{API}/donations/mine", headers={"Authorization": f"Bearer {super_token}"}, timeout=20).json()
        r2 = requests.get(f"{API}/donations/mine", headers={"Authorization": f"Bearer {reg_token}"}, timeout=20).json()
        ids1 = {x["id"] for x in r1 if x.get("id")}
        ids2 = {x["id"] for x in r2 if x.get("id")}
        # No leak across accounts
        assert ids1.isdisjoint(ids2)
        for x in r2:
            assert x.get("email", "").lower() == REG["email"].lower()

    def test_mine_unauthenticated_blocked(self):
        r = requests.get(f"{API}/donations/mine", timeout=20)
        assert r.status_code in (401, 403)


# ── /api/admin/export/*.csv ──────────────────────────────────────────
class TestCsvExports:
    def _csv_rows(self, text):
        return list(csv.DictReader(io.StringIO(text)))

    def test_export_roster_super(self, super_token):
        r = requests.get(f"{API}/admin/export/roster.csv",
                         headers={"Authorization": f"Bearer {super_token}"}, timeout=30)
        assert r.status_code == 200, r.text
        assert "text/csv" in r.headers.get("content-type", "")
        assert "attachment" in r.headers.get("content-disposition", "").lower()
        first_line = r.text.splitlines()[0]
        for col in ["name", "email", "phone", "role", "designation",
                    "specializations", "badges", "specialization_edits_remaining"]:
            assert col in first_line, f"missing column: {col}"
        rows = self._csv_rows(r.text)
        emails = {x["email"] for x in rows}
        assert SUPER["email"] in emails  # super sees self

    def test_export_roster_hides_master_from_regular(self, reg_token):
        r = requests.get(f"{API}/admin/export/roster.csv",
                         headers={"Authorization": f"Bearer {reg_token}"}, timeout=30)
        assert r.status_code == 200
        rows = self._csv_rows(r.text)
        emails = {x["email"] for x in rows}
        assert SUPER["email"] not in emails, "regular admin should NOT see master admin"
        assert REG["email"] in emails

    def test_export_donations_super(self, super_token):
        r = requests.get(f"{API}/admin/export/donations.csv",
                         headers={"Authorization": f"Bearer {super_token}"}, timeout=30)
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")
        first_line = r.text.splitlines()[0]
        for col in ["id", "name", "email", "amount", "fee_covered", "gross_amount", "status"]:
            assert col in first_line, f"missing column: {col}"

    def test_export_activity_super(self, super_token):
        r = requests.get(f"{API}/admin/export/activity.csv",
                         headers={"Authorization": f"Bearer {super_token}"}, timeout=30)
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")
        first_line = r.text.splitlines()[0]
        for col in ["timestamp", "action", "entity_type", "entity_id", "user_email", "details", "ip"]:
            assert col in first_line, f"missing column: {col}"

    def test_export_activity_hides_master_from_regular(self, super_token, reg_token):
        # Trigger an action by super (already done by fetching exports earlier — log_activity is called)
        # Do another super-only call to ensure recent log:
        requests.get(f"{API}/admin/export/roster.csv",
                     headers={"Authorization": f"Bearer {super_token}"}, timeout=30)
        time.sleep(0.5)
        r = requests.get(f"{API}/admin/export/activity.csv",
                         headers={"Authorization": f"Bearer {reg_token}"}, timeout=30)
        assert r.status_code == 200
        rows = list(csv.DictReader(io.StringIO(r.text)))
        for row in rows:
            assert row.get("user_email") != SUPER["email"], \
                f"regular admin saw master action: {row}"

    def test_export_csv_403_for_non_admin(self, member_token):
        token, _email = member_token
        for k in ("roster", "donations", "activity"):
            r = requests.get(f"{API}/admin/export/{k}.csv",
                             headers={"Authorization": f"Bearer {token}"}, timeout=20)
            assert r.status_code == 403, f"{k}: expected 403 got {r.status_code} {r.text[:160]}"

    def test_export_csv_unauthenticated(self):
        for k in ("roster", "donations", "activity"):
            r = requests.get(f"{API}/admin/export/{k}.csv", timeout=20)
            assert r.status_code in (401, 403)
