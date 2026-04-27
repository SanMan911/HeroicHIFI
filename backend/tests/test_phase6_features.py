"""
Test Phase 6 Features: Profile, Badges, Tickets, Password Reset, Admin User Management
Tests for Heroic HIFI Foundation NGO website new features
"""
import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://hifi-ngo-portal.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@heroichifi.org"
ADMIN_PASSWORD = "HHF@admin2024"

# Test user data
TEST_USER_PREFIX = "TEST_PHASE6_"
TEST_USER_EMAIL = f"{TEST_USER_PREFIX}{uuid.uuid4().hex[:8]}@test.com"
TEST_USER_PASSWORD = "TestPass123!"
TEST_USER_NAME = f"{TEST_USER_PREFIX}User"


class TestHelpers:
    """Helper methods for tests"""
    
    @staticmethod
    def get_admin_token():
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    @staticmethod
    def create_test_user():
        """Create a test user via OTP flow (debug mode)"""
        email = f"{TEST_USER_PREFIX}{uuid.uuid4().hex[:8]}@test.com"
        
        # Step 1: Send OTP
        otp_response = requests.post(f"{BASE_URL}/api/auth/send-otp", json={
            "email": email,
            "purpose": "registration"
        })
        if otp_response.status_code != 200:
            return None, None, None
        
        otp = otp_response.json().get("otp_debug")
        if not otp:
            return None, None, None
        
        # Step 2: Verify OTP
        verify_response = requests.post(f"{BASE_URL}/api/auth/verify-otp", json={
            "email": email,
            "otp": otp,
            "purpose": "registration"
        })
        if verify_response.status_code != 200:
            return None, None, None
        
        otp_token = verify_response.json().get("otp_token")
        
        # Step 3: Register
        register_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": f"{TEST_USER_PREFIX}User",
            "email": email,
            "password": TEST_USER_PASSWORD,
            "phone": "9876543210",
            "pan_number": "ABCDE1234F",
            "aadhaar_number": "123456789012",
            "otp_token": otp_token
        })
        if register_response.status_code != 200:
            return None, None, None
        
        token = register_response.json().get("token")
        return email, token, TEST_USER_PASSWORD


# ============ PROFILE TESTS ============

class TestProfile:
    """Tests for Profile endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test user"""
        self.email, self.token, self.password = TestHelpers.create_test_user()
        if not self.token:
            pytest.skip("Could not create test user")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        yield
        # Cleanup: Delete test user via admin
        admin_token = TestHelpers.get_admin_token()
        if admin_token:
            requests.delete(
                f"{BASE_URL}/api/admin/users/{self.email}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
    
    def test_get_profile_returns_user_data(self):
        """GET /api/profile returns profile with badges, volunteer_hours, total_donated"""
        response = requests.get(f"{BASE_URL}/api/profile", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "name" in data
        assert "email" in data
        assert "badges" in data
        assert "volunteer_hours" in data
        assert "total_donated" in data
        assert "profile_pic_path" in data
        assert "status" in data
        
        # Verify auto-badge "Helping Hero" is assigned
        assert "Helping Hero" in data["badges"], "Helping Hero badge should be auto-assigned"
        assert data["status"] == "active"
    
    def test_update_profile_name_phone_address(self):
        """PUT /api/profile updates name, phone, address"""
        update_data = {
            "name": "Updated Test Name",
            "phone": "1234567890",
            "address": "123 Test Street"
        }
        response = requests.put(f"{BASE_URL}/api/profile", json=update_data, headers=self.headers)
        assert response.status_code == 200
        
        # Verify changes persisted
        get_response = requests.get(f"{BASE_URL}/api/profile", headers=self.headers)
        assert get_response.status_code == 200
        profile = get_response.json()
        assert profile["name"] == "Updated Test Name"
        assert profile["phone"] == "1234567890"
        assert profile["address"] == "123 Test Street"
    
    def test_profile_requires_auth(self):
        """Profile endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/profile")
        assert response.status_code == 401


# ============ PASSWORD RESET TESTS ============

class TestPasswordReset:
    """Tests for Password Reset flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test user"""
        self.email, self.token, self.password = TestHelpers.create_test_user()
        if not self.token:
            pytest.skip("Could not create test user")
        yield
        # Cleanup
        admin_token = TestHelpers.get_admin_token()
        if admin_token:
            requests.delete(
                f"{BASE_URL}/api/admin/users/{self.email}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
    
    def test_forgot_password_sends_reset_link(self):
        """POST /api/auth/forgot-password returns debug_link in debug mode"""
        response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": self.email
        })
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        # In debug mode (no Resend API key), debug_link should be returned
        assert "debug_link" in data, "Debug link should be returned when Resend API key is not set"
        assert "token=" in data["debug_link"]
        # Email is lowercased in the link
        assert f"email={self.email.lower()}" in data["debug_link"]
    
    def test_forgot_password_nonexistent_email(self):
        """POST /api/auth/forgot-password with non-existent email still returns success (security)"""
        response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": "nonexistent@test.com"
        })
        assert response.status_code == 200
        # Should not reveal if email exists
        assert "message" in response.json()
    
    def test_reset_password_with_valid_token(self):
        """POST /api/auth/reset-password resets password with valid token"""
        # Get reset token
        forgot_response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": self.email
        })
        debug_link = forgot_response.json().get("debug_link", "")
        
        # Extract token from debug_link
        import urllib.parse
        parsed = urllib.parse.urlparse(debug_link)
        params = urllib.parse.parse_qs(parsed.query)
        token = params.get("token", [""])[0]
        
        assert token, "Token should be present in debug_link"
        
        # Reset password
        new_password = "NewTestPass456!"
        reset_response = requests.post(f"{BASE_URL}/api/auth/reset-password", json={
            "email": self.email,
            "token": token,
            "new_password": new_password
        })
        assert reset_response.status_code == 200
        
        # Verify can login with new password
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.email,
            "password": new_password
        })
        assert login_response.status_code == 200
    
    def test_reset_password_invalid_token(self):
        """POST /api/auth/reset-password fails with invalid token"""
        response = requests.post(f"{BASE_URL}/api/auth/reset-password", json={
            "email": self.email,
            "token": "invalid_token_12345",
            "new_password": "NewPass123!"
        })
        assert response.status_code == 400
    
    def test_reset_password_short_password(self):
        """POST /api/auth/reset-password fails with password < 6 chars"""
        # Get valid token first
        forgot_response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": self.email
        })
        debug_link = forgot_response.json().get("debug_link", "")
        import urllib.parse
        parsed = urllib.parse.urlparse(debug_link)
        params = urllib.parse.parse_qs(parsed.query)
        token = params.get("token", [""])[0]
        
        response = requests.post(f"{BASE_URL}/api/auth/reset-password", json={
            "email": self.email,
            "token": token,
            "new_password": "12345"  # Too short
        })
        assert response.status_code == 400


# ============ TICKETS TESTS ============

class TestTickets:
    """Tests for Grievance Ticket system"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test user"""
        self.email, self.token, self.password = TestHelpers.create_test_user()
        if not self.token:
            pytest.skip("Could not create test user")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.admin_token = TestHelpers.get_admin_token()
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        self.created_ticket_id = None
        yield
        # Cleanup
        if self.admin_token:
            requests.delete(
                f"{BASE_URL}/api/admin/users/{self.email}",
                headers=self.admin_headers
            )
    
    def test_create_ticket(self):
        """POST /api/tickets creates a grievance ticket"""
        ticket_data = {
            "subject": "Test Ticket Subject",
            "description": "This is a test ticket description for testing purposes.",
            "priority": "medium"
        }
        response = requests.post(f"{BASE_URL}/api/tickets", json=ticket_data, headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "ticket" in data
        assert data["ticket"]["subject"] == ticket_data["subject"]
        assert data["ticket"]["description"] == ticket_data["description"]
        assert data["ticket"]["priority"] == "medium"
        assert data["ticket"]["status"] == "open"
        self.created_ticket_id = data["ticket"]["id"]
    
    def test_get_user_tickets(self):
        """GET /api/tickets returns user's own tickets"""
        # Create a ticket first
        requests.post(f"{BASE_URL}/api/tickets", json={
            "subject": "Test Ticket",
            "description": "Test description",
            "priority": "low"
        }, headers=self.headers)
        
        response = requests.get(f"{BASE_URL}/api/tickets", headers=self.headers)
        assert response.status_code == 200
        
        tickets = response.json()
        assert isinstance(tickets, list)
        assert len(tickets) >= 1
        # Email is lowercased in the backend
        assert tickets[0]["user_email"] == self.email.lower()
    
    def test_admin_get_all_tickets(self):
        """GET /api/admin/tickets returns all tickets (admin only)"""
        response = requests.get(f"{BASE_URL}/api/admin/tickets", headers=self.admin_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_admin_update_ticket_status(self):
        """PUT /api/admin/tickets/{id}/status updates ticket status"""
        # Create ticket
        create_response = requests.post(f"{BASE_URL}/api/tickets", json={
            "subject": "Status Test Ticket",
            "description": "Testing status update",
            "priority": "high"
        }, headers=self.headers)
        ticket_id = create_response.json()["ticket"]["id"]
        
        # Update status
        response = requests.put(
            f"{BASE_URL}/api/admin/tickets/{ticket_id}/status",
            json={"status": "in-progress"},
            headers=self.admin_headers
        )
        assert response.status_code == 200
        
        # Verify status changed
        tickets = requests.get(f"{BASE_URL}/api/tickets", headers=self.headers).json()
        ticket = next((t for t in tickets if t["id"] == ticket_id), None)
        assert ticket is not None
        assert ticket["status"] == "in-progress"
    
    def test_admin_respond_to_ticket(self):
        """PUT /api/admin/tickets/{id}/respond adds admin response"""
        # Create ticket
        create_response = requests.post(f"{BASE_URL}/api/tickets", json={
            "subject": "Response Test Ticket",
            "description": "Testing admin response",
            "priority": "medium"
        }, headers=self.headers)
        ticket_id = create_response.json()["ticket"]["id"]
        
        # Add response
        response = requests.put(
            f"{BASE_URL}/api/admin/tickets/{ticket_id}/respond",
            json={"response": "This is the admin response to your ticket."},
            headers=self.admin_headers
        )
        assert response.status_code == 200
        
        # Verify response added
        tickets = requests.get(f"{BASE_URL}/api/tickets", headers=self.headers).json()
        ticket = next((t for t in tickets if t["id"] == ticket_id), None)
        assert ticket is not None
        assert ticket["admin_response"] == "This is the admin response to your ticket."
        assert ticket["status"] == "responded"
    
    def test_tickets_require_auth(self):
        """Ticket endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/tickets")
        assert response.status_code == 401
        
        response = requests.post(f"{BASE_URL}/api/tickets", json={
            "subject": "Test", "description": "Test", "priority": "low"
        })
        assert response.status_code == 401


# ============ ADMIN USER MANAGEMENT TESTS ============

class TestAdminUserManagement:
    """Tests for Admin User Management features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup admin and test user"""
        self.admin_token = TestHelpers.get_admin_token()
        if not self.admin_token:
            pytest.skip("Could not get admin token")
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        self.test_email, self.test_token, _ = TestHelpers.create_test_user()
        if not self.test_token:
            pytest.skip("Could not create test user")
        self.test_headers = {"Authorization": f"Bearer {self.test_token}"}
        yield
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/admin/users/{self.test_email}",
            headers=self.admin_headers
        )
    
    def test_admin_update_user_role_promote(self):
        """PUT /api/admin/users/{email}/update - promote to admin"""
        response = requests.put(
            f"{BASE_URL}/api/admin/users/{self.test_email}/update",
            json={"role": "admin"},
            headers=self.admin_headers
        )
        assert response.status_code == 200
        
        # Verify role changed (email is lowercased in backend)
        users = requests.get(f"{BASE_URL}/api/admin/users", headers=self.admin_headers).json()
        user = next((u for u in users if u["email"] == self.test_email.lower()), None)
        assert user is not None
        assert user["role"] == "admin"
        
        # Demote back
        requests.put(
            f"{BASE_URL}/api/admin/users/{self.test_email}/update",
            json={"role": "volunteer"},
            headers=self.admin_headers
        )
    
    def test_admin_update_volunteer_hours(self):
        """PUT /api/admin/users/{email}/update - update volunteer hours"""
        response = requests.put(
            f"{BASE_URL}/api/admin/users/{self.test_email}/update",
            json={"volunteer_hours": 150},
            headers=self.admin_headers
        )
        assert response.status_code == 200
        
        # Verify hours updated (email is lowercased)
        users = requests.get(f"{BASE_URL}/api/admin/users", headers=self.admin_headers).json()
        user = next((u for u in users if u["email"] == self.test_email.lower()), None)
        assert user is not None
        assert user["volunteer_hours"] == 150
    
    def test_admin_update_merchandise_issued(self):
        """PUT /api/admin/users/{email}/update - update merchandise issued"""
        response = requests.put(
            f"{BASE_URL}/api/admin/users/{self.test_email}/update",
            json={"merchandise_issued": True},
            headers=self.admin_headers
        )
        assert response.status_code == 200
        
        # Verify merchandise flag (email is lowercased)
        users = requests.get(f"{BASE_URL}/api/admin/users", headers=self.admin_headers).json()
        user = next((u for u in users if u["email"] == self.test_email.lower()), None)
        assert user is not None
        assert user["merchandise_issued"] == True
    
    def test_admin_update_comments(self):
        """PUT /api/admin/users/{email}/update - update admin comments"""
        comment = "This is a test admin comment."
        response = requests.put(
            f"{BASE_URL}/api/admin/users/{self.test_email}/update",
            json={"admin_comments": comment},
            headers=self.admin_headers
        )
        assert response.status_code == 200
        
        # Verify comment (email is lowercased)
        users = requests.get(f"{BASE_URL}/api/admin/users", headers=self.admin_headers).json()
        user = next((u for u in users if u["email"] == self.test_email.lower()), None)
        assert user is not None
        assert user["admin_comments"] == comment
    
    def test_admin_suspend_user(self):
        """PUT /api/admin/users/{email}/update - suspend user"""
        response = requests.put(
            f"{BASE_URL}/api/admin/users/{self.test_email}/update",
            json={
                "status": "suspended",
                "suspension_reason": "Test suspension",
                "suspended_until": "2026-12-31"
            },
            headers=self.admin_headers
        )
        assert response.status_code == 200
        
        # Verify user is suspended (email is lowercased)
        users = requests.get(f"{BASE_URL}/api/admin/users", headers=self.admin_headers).json()
        user = next((u for u in users if u["email"] == self.test_email.lower()), None)
        assert user is not None
        assert user["status"] == "suspended"
    
    def test_suspended_user_cannot_login(self):
        """Suspended user cannot log in (returns 403)"""
        # First suspend the user
        requests.put(
            f"{BASE_URL}/api/admin/users/{self.test_email}/update",
            json={"status": "suspended", "suspension_reason": "Test"},
            headers=self.admin_headers
        )
        
        # Try to login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.test_email,
            "password": TEST_USER_PASSWORD
        })
        assert login_response.status_code == 403
        assert "suspended" in login_response.json().get("detail", "").lower()
        
        # Unsuspend for cleanup
        requests.put(
            f"{BASE_URL}/api/admin/users/{self.test_email}/update",
            json={"status": "active"},
            headers=self.admin_headers
        )
    
    def test_admin_unsuspend_user(self):
        """PUT /api/admin/users/{email}/update - unsuspend user"""
        # First suspend
        requests.put(
            f"{BASE_URL}/api/admin/users/{self.test_email}/update",
            json={"status": "suspended"},
            headers=self.admin_headers
        )
        
        # Then unsuspend
        response = requests.put(
            f"{BASE_URL}/api/admin/users/{self.test_email}/update",
            json={"status": "active"},
            headers=self.admin_headers
        )
        assert response.status_code == 200
        
        # Verify user can login again
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": self.test_email,
            "password": TEST_USER_PASSWORD
        })
        assert login_response.status_code == 200


# ============ BADGE MANAGEMENT TESTS ============

class TestBadgeManagement:
    """Tests for Badge system"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup admin and test user"""
        self.admin_token = TestHelpers.get_admin_token()
        if not self.admin_token:
            pytest.skip("Could not get admin token")
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        self.test_email, self.test_token, _ = TestHelpers.create_test_user()
        if not self.test_token:
            pytest.skip("Could not create test user")
        self.test_headers = {"Authorization": f"Bearer {self.test_token}"}
        yield
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/admin/users/{self.test_email}",
            headers=self.admin_headers
        )
    
    def test_auto_badge_helping_hero(self):
        """Helping Hero badge is auto-assigned to all members"""
        response = requests.get(f"{BASE_URL}/api/profile", headers=self.test_headers)
        assert response.status_code == 200
        badges = response.json().get("badges", [])
        assert "Helping Hero" in badges
    
    def test_admin_add_badge(self):
        """POST /api/admin/users/{email}/badge adds a badge"""
        badge_name = "Star Volunteer of the Month"
        response = requests.post(
            f"{BASE_URL}/api/admin/users/{self.test_email}/badge",
            json={"badge": badge_name},
            headers=self.admin_headers
        )
        assert response.status_code == 200
        assert badge_name in response.json().get("badges", [])
        
        # Verify badge persisted
        profile = requests.get(f"{BASE_URL}/api/profile", headers=self.test_headers).json()
        assert badge_name in profile["badges"]
    
    def test_admin_remove_badge(self):
        """DELETE /api/admin/users/{email}/badge/{badge} removes a badge"""
        badge_name = "Top Donor"
        
        # First add the badge
        requests.post(
            f"{BASE_URL}/api/admin/users/{self.test_email}/badge",
            json={"badge": badge_name},
            headers=self.admin_headers
        )
        
        # Then remove it
        response = requests.delete(
            f"{BASE_URL}/api/admin/users/{self.test_email}/badge/{badge_name}",
            headers=self.admin_headers
        )
        assert response.status_code == 200
        assert badge_name not in response.json().get("badges", [])
        
        # Verify badge removed
        profile = requests.get(f"{BASE_URL}/api/profile", headers=self.test_headers).json()
        assert badge_name not in profile["badges"]
    
    def test_century_hero_badge_auto_assign(self):
        """Century Hero badge auto-assigned when volunteer_hours >= 100"""
        # Set volunteer hours to 100
        requests.put(
            f"{BASE_URL}/api/admin/users/{self.test_email}/update",
            json={"volunteer_hours": 100},
            headers=self.admin_headers
        )
        
        # Get profile (triggers auto-badge computation)
        profile = requests.get(f"{BASE_URL}/api/profile", headers=self.test_headers).json()
        assert "Century Hero" in profile["badges"]


# ============ ADMIN STATS TESTS ============

class TestAdminStats:
    """Tests for Admin Stats endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup admin token"""
        self.admin_token = TestHelpers.get_admin_token()
        if not self.admin_token:
            pytest.skip("Could not get admin token")
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
    
    def test_admin_stats_includes_tickets(self):
        """GET /api/admin/stats includes tickets stats"""
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers=self.admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "tickets" in data
        assert "total" in data["tickets"]
        assert "open" in data["tickets"]
        assert "donations" in data
        assert "volunteers" in data
        assert "queries" in data
        assert "users" in data


# ============ DIRECTORY TESTS ============

class TestDirectory:
    """Tests for Community Directory with badges and hours"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test user"""
        self.email, self.token, _ = TestHelpers.create_test_user()
        if not self.token:
            pytest.skip("Could not create test user")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.admin_token = TestHelpers.get_admin_token()
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        yield
        # Cleanup
        if self.admin_token:
            requests.delete(
                f"{BASE_URL}/api/admin/users/{self.email}",
                headers=self.admin_headers
            )
    
    def test_directory_returns_badges_and_hours(self):
        """GET /api/directory returns badges and volunteer_hours for members"""
        response = requests.get(f"{BASE_URL}/api/directory", headers=self.headers)
        assert response.status_code == 200
        
        members = response.json()
        assert isinstance(members, list)
        
        # Find our test user
        test_member = next((m for m in members if m["email"] == self.email), None)
        if test_member:
            assert "badges" in test_member
            assert "volunteer_hours" in test_member


# ============ RUN TESTS ============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
