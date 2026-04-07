"""
Wall of Fame Feature Tests
Tests for:
- GET /api/wall-of-fame (public, no auth)
- POST /api/admin/wall-of-fame/{email} (admin only)
- DELETE /api/admin/wall-of-fame/{email} (admin only)
- PUT /api/admin/wall-of-fame/{email} (admin only)
- Non-admin cannot add/remove from wall of fame
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@heroichifi.org"
ADMIN_PASSWORD = "HHF@admin2024"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json()["token"]


class TestWallOfFamePublicEndpoint:
    """Tests for GET /api/wall-of-fame (public endpoint)"""
    
    def test_wall_of_fame_no_auth_required(self):
        """GET /api/wall-of-fame should work without authentication"""
        response = requests.get(f"{BASE_URL}/api/wall-of-fame")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Should return a list
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
    
    def test_wall_of_fame_returns_expected_fields(self):
        """Wall of Fame entries should have expected fields"""
        response = requests.get(f"{BASE_URL}/api/wall-of-fame")
        assert response.status_code == 200
        
        data = response.json()
        if len(data) > 0:
            entry = data[0]
            expected_fields = ["email", "name", "role", "volunteer_hours", "total_donated", "badges"]
            for field in expected_fields:
                assert field in entry, f"Missing field: {field}"
    
    def test_wall_of_fame_contains_admin(self):
        """Admin should be on wall of fame (added in previous test)"""
        response = requests.get(f"{BASE_URL}/api/wall-of-fame")
        assert response.status_code == 200
        
        data = response.json()
        emails = [e["email"] for e in data]
        assert ADMIN_EMAIL in emails, f"Admin should be on wall of fame. Found: {emails}"


class TestWallOfFameAdminEndpoints:
    """Tests for admin-only Wall of Fame endpoints"""
    
    def test_add_admin_to_wall_of_fame_duplicate_check(self, admin_token):
        """Adding admin (already on wall) should fail with 400"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Admin is already on wall of fame, so this should fail
        response = requests.post(
            f"{BASE_URL}/api/admin/wall-of-fame/{ADMIN_EMAIL}",
            headers=headers
        )
        # Should be 400 since admin is already on wall
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        assert "already on the Wall of Fame" in response.json().get("detail", "")
    
    def test_update_admin_wall_entry_contribution_summary(self, admin_token):
        """PUT /api/admin/wall-of-fame/{email} updates contribution_summary"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Update contribution summary for admin
        summary = "Founding member and visionary leader of Heroic HIFI Foundation"
        response = requests.put(
            f"{BASE_URL}/api/admin/wall-of-fame/{ADMIN_EMAIL}",
            headers=headers,
            json={"contribution_summary": summary}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify update
        wof_response = requests.get(f"{BASE_URL}/api/wall-of-fame")
        wof_data = wof_response.json()
        admin_entry = next((e for e in wof_data if e["email"] == ADMIN_EMAIL), None)
        assert admin_entry is not None
        assert admin_entry["contribution_summary"] == summary
    
    def test_remove_nonexistent_user_fails(self, admin_token):
        """Removing user not on wall of fame should fail"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/wall-of-fame/nonexistent_user@example.com",
            headers=headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_add_nonexistent_user_fails(self, admin_token):
        """Adding nonexistent user to wall of fame should fail"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/wall-of-fame/nonexistent_user_xyz@example.com",
            headers=headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_update_nonexistent_wall_entry_fails(self, admin_token):
        """Updating nonexistent wall entry should fail"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.put(
            f"{BASE_URL}/api/admin/wall-of-fame/nonexistent_user@example.com",
            headers=headers,
            json={"contribution_summary": "Test"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_update_with_empty_body_fails(self, admin_token):
        """Updating with empty body should fail"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.put(
            f"{BASE_URL}/api/admin/wall-of-fame/{ADMIN_EMAIL}",
            headers=headers,
            json={}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"


class TestWallOfFameNonAdminAccess:
    """Tests to verify non-admin users cannot modify wall of fame"""
    
    def test_unauthenticated_cannot_add_to_wall(self):
        """Unauthenticated request cannot add to wall of fame"""
        response = requests.post(
            f"{BASE_URL}/api/admin/wall-of-fame/test@example.com"
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_unauthenticated_cannot_remove_from_wall(self):
        """Unauthenticated request cannot remove from wall of fame"""
        response = requests.delete(
            f"{BASE_URL}/api/admin/wall-of-fame/test@example.com"
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_unauthenticated_cannot_update_wall_entry(self):
        """Unauthenticated request cannot update wall of fame entry"""
        response = requests.put(
            f"{BASE_URL}/api/admin/wall-of-fame/test@example.com",
            json={"contribution_summary": "Hacked!"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


class TestResendEmailConfiguration:
    """Tests to verify Resend email configuration"""
    
    def test_otp_email_is_sent(self):
        """OTP email should be sent via Resend (email_sent: true)"""
        response = requests.post(f"{BASE_URL}/api/auth/send-otp", json={
            "email": "test_resend_check@example.com",
            "purpose": "registration"
        })
        assert response.status_code == 200
        
        data = response.json()
        # With live Resend API key, email_sent should be true
        assert data.get("email_sent") == True, f"Email should be sent. Got: {data}"
        # otp_debug should be None when email is actually sent
        assert data.get("otp_debug") is None, "OTP should not be exposed when email is sent"
