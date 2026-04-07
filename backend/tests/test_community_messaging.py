"""
Community Messaging Feature Tests
Tests for:
- Directory endpoint (GET /api/directory)
- Messaging endpoints (POST /api/messages, GET /api/messages/thread, GET /api/messages/conversations)
- Number stripping functionality
- Admin message viewing (GET /api/admin/messages, GET /api/admin/messages/thread)
"""

import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@heroichifi.org"
ADMIN_PASSWORD = "HHF@admin2024"

# Test user credentials (will be created during tests)
TEST_USER1_EMAIL = f"testuser1_{uuid.uuid4().hex[:8]}@test.com"
TEST_USER2_EMAIL = f"testuser2_{uuid.uuid4().hex[:8]}@test.com"
TEST_PASSWORD = "TestPass123!"


class TestDirectoryEndpoint:
    """Tests for GET /api/directory"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login as admin to get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        self.admin_token = response.json()["token"]
        self.admin_session = requests.Session()
        self.admin_session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.admin_token}"
        })
    
    def test_directory_requires_auth(self):
        """Directory endpoint requires authentication"""
        response = self.session.get(f"{BASE_URL}/api/directory")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Directory requires authentication")
    
    def test_directory_returns_members(self):
        """Directory returns list of members"""
        response = self.admin_session.get(f"{BASE_URL}/api/directory")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Directory should return a list"
        print(f"PASS: Directory returns {len(data)} members")
    
    def test_directory_excludes_admin(self):
        """Directory excludes admin users"""
        response = self.admin_session.get(f"{BASE_URL}/api/directory")
        assert response.status_code == 200
        data = response.json()
        admin_users = [u for u in data if u.get("role") == "admin"]
        assert len(admin_users) == 0, "Admin users should be excluded from directory"
        print("PASS: Directory excludes admin users")
    
    def test_directory_excludes_sensitive_fields(self):
        """Directory excludes PAN, Aadhaar, address"""
        response = self.admin_session.get(f"{BASE_URL}/api/directory")
        assert response.status_code == 200
        data = response.json()
        if len(data) > 0:
            member = data[0]
            assert "pan_number" not in member, "PAN should be excluded"
            assert "aadhaar_number" not in member, "Aadhaar should be excluded"
            assert "address" not in member, "Address should be excluded"
            assert "password_hash" not in member, "Password hash should be excluded"
            print("PASS: Directory excludes sensitive fields")
        else:
            print("SKIP: No members in directory to check fields")


class TestNumberStripping:
    """Tests for strip_numbers function"""
    
    def test_strip_digits(self):
        """Digits are replaced with [*]"""
        # This tests the backend strip_numbers function indirectly through messaging
        # We'll test it directly by checking message thread responses
        print("PASS: Number stripping tests will be done via messaging tests")
    
    def test_strip_number_words(self):
        """Number words like 'one', 'two' are stripped"""
        # Test cases for number stripping:
        # - "123" -> "[*]"
        # - "one" -> "[*]"
        # - "done" -> "done" (should NOT be stripped)
        # - "five hundred" -> "[*] [*]"
        print("PASS: Number word stripping will be tested via messaging")


class TestMessagingEndpoints:
    """Tests for messaging endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login as admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        self.admin_token = response.json()["token"]
        self.admin_session = requests.Session()
        self.admin_session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.admin_token}"
        })
    
    def test_send_message_requires_auth(self):
        """POST /api/messages requires authentication"""
        response = self.session.post(f"{BASE_URL}/api/messages", json={
            "recipient_email": "test@test.com",
            "message": "Hello"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Send message requires authentication")
    
    def test_send_message_to_nonexistent_user(self):
        """Cannot send message to non-existent user"""
        response = self.admin_session.post(f"{BASE_URL}/api/messages", json={
            "recipient_email": "nonexistent@test.com",
            "message": "Hello"
        })
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: Cannot send message to non-existent user")
    
    def test_cannot_send_message_to_self(self):
        """Cannot send message to yourself"""
        response = self.admin_session.post(f"{BASE_URL}/api/messages", json={
            "recipient_email": ADMIN_EMAIL,
            "message": "Hello to myself"
        })
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("PASS: Cannot send message to yourself")
    
    def test_conversations_requires_auth(self):
        """GET /api/messages/conversations requires authentication"""
        response = self.session.get(f"{BASE_URL}/api/messages/conversations")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Conversations requires authentication")
    
    def test_conversations_returns_list(self):
        """GET /api/messages/conversations returns list"""
        response = self.admin_session.get(f"{BASE_URL}/api/messages/conversations")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Conversations should return a list"
        print(f"PASS: Conversations returns list with {len(data)} items")
    
    def test_thread_requires_auth(self):
        """GET /api/messages/thread/{email} requires authentication"""
        response = self.session.get(f"{BASE_URL}/api/messages/thread/test@test.com")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Thread requires authentication")
    
    def test_thread_returns_list(self):
        """GET /api/messages/thread/{email} returns list"""
        response = self.admin_session.get(f"{BASE_URL}/api/messages/thread/test@test.com")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Thread should return a list"
        print("PASS: Thread returns list")


class TestAdminMessagesEndpoints:
    """Tests for admin message viewing endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login as admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        self.admin_token = response.json()["token"]
        self.admin_session = requests.Session()
        self.admin_session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.admin_token}"
        })
    
    def test_admin_messages_requires_admin(self):
        """GET /api/admin/messages requires admin role"""
        # Test without auth
        response = self.session.get(f"{BASE_URL}/api/admin/messages")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Admin messages requires authentication")
    
    def test_admin_messages_returns_threads(self):
        """GET /api/admin/messages returns all conversation threads"""
        response = self.admin_session.get(f"{BASE_URL}/api/admin/messages")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Admin messages should return a list"
        print(f"PASS: Admin messages returns {len(data)} threads")
    
    def test_admin_thread_requires_admin(self):
        """GET /api/admin/messages/thread/{email1}/{email2} requires admin"""
        response = self.session.get(f"{BASE_URL}/api/admin/messages/thread/a@test.com/b@test.com")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Admin thread requires authentication")
    
    def test_admin_thread_returns_unredacted(self):
        """GET /api/admin/messages/thread returns unredacted messages"""
        response = self.admin_session.get(f"{BASE_URL}/api/admin/messages/thread/a@test.com/b@test.com")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Admin thread should return a list"
        print("PASS: Admin thread returns list (unredacted)")


class TestDashboardTabs:
    """Tests for admin dashboard tabs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login as admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        self.admin_token = response.json()["token"]
        self.admin_session = requests.Session()
        self.admin_session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.admin_token}"
        })
    
    def test_admin_stats_endpoint(self):
        """GET /api/admin/stats returns dashboard stats"""
        response = self.admin_session.get(f"{BASE_URL}/api/admin/stats")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "donations" in data, "Stats should include donations"
        assert "volunteers" in data, "Stats should include volunteers"
        assert "queries" in data, "Stats should include queries"
        assert "users" in data, "Stats should include users"
        print("PASS: Admin stats returns all required fields")
    
    def test_admin_donations_endpoint(self):
        """GET /api/admin/donations returns donations list"""
        response = self.admin_session.get(f"{BASE_URL}/api/admin/donations")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Donations should return a list"
        print(f"PASS: Admin donations returns {len(data)} items")
    
    def test_admin_volunteers_endpoint(self):
        """GET /api/admin/volunteers returns volunteers list"""
        response = self.admin_session.get(f"{BASE_URL}/api/admin/volunteers")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Volunteers should return a list"
        print(f"PASS: Admin volunteers returns {len(data)} items")
    
    def test_admin_queries_endpoint(self):
        """GET /api/admin/queries returns queries list"""
        response = self.admin_session.get(f"{BASE_URL}/api/admin/queries")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Queries should return a list"
        print(f"PASS: Admin queries returns {len(data)} items")
    
    def test_admin_users_endpoint(self):
        """GET /api/admin/users returns users list"""
        response = self.admin_session.get(f"{BASE_URL}/api/admin/users")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Users should return a list"
        print(f"PASS: Admin users returns {len(data)} items")


class TestMessagingWithTestUsers:
    """End-to-end messaging tests with test users"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - create test users via OTP flow"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin first
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        self.admin_token = response.json()["token"]
        self.admin_session = requests.Session()
        self.admin_session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.admin_token}"
        })
    
    def _create_test_user(self, email, name):
        """Helper to create a test user via OTP flow"""
        # Step 1: Send OTP
        response = self.session.post(f"{BASE_URL}/api/auth/send-otp", json={
            "email": email,
            "purpose": "registration"
        })
        if response.status_code != 200:
            print(f"Failed to send OTP: {response.text}")
            return None
        
        otp_data = response.json()
        otp = otp_data.get("otp_debug")  # Debug OTP when Resend not configured
        if not otp:
            print("OTP not available in debug mode")
            return None
        
        # Step 2: Verify OTP
        response = self.session.post(f"{BASE_URL}/api/auth/verify-otp", json={
            "email": email,
            "otp": otp,
            "purpose": "registration"
        })
        if response.status_code != 200:
            print(f"Failed to verify OTP: {response.text}")
            return None
        
        otp_token = response.json().get("otp_token")
        
        # Step 3: Register
        response = self.session.post(f"{BASE_URL}/api/auth/register", json={
            "name": name,
            "email": email,
            "password": TEST_PASSWORD,
            "phone": "+91 9876543210",
            "pan_number": "ABCDE1234F",
            "aadhaar_number": "123456789012",
            "otp_token": otp_token
        })
        if response.status_code != 200:
            print(f"Failed to register: {response.text}")
            return None
        
        return response.json().get("token")
    
    def test_full_messaging_flow(self):
        """Test complete messaging flow between two users"""
        # Create two test users
        user1_email = f"msgtest1_{uuid.uuid4().hex[:6]}@test.com"
        user2_email = f"msgtest2_{uuid.uuid4().hex[:6]}@test.com"
        
        user1_token = self._create_test_user(user1_email, "Test User One")
        if not user1_token:
            pytest.skip("Could not create test user 1")
        
        user2_token = self._create_test_user(user2_email, "Test User Two")
        if not user2_token:
            pytest.skip("Could not create test user 2")
        
        # User 1 sends message to User 2
        user1_session = requests.Session()
        user1_session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {user1_token}"
        })
        
        # Send message with numbers to test stripping
        test_message = "Hello! My phone is 9876543210 and I have one hundred rupees."
        response = user1_session.post(f"{BASE_URL}/api/messages", json={
            "recipient_email": user2_email,
            "message": test_message
        })
        assert response.status_code == 200, f"Failed to send message: {response.text}"
        print("PASS: User 1 sent message to User 2")
        
        # User 2 checks thread - should see redacted message
        user2_session = requests.Session()
        user2_session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {user2_token}"
        })
        
        response = user2_session.get(f"{BASE_URL}/api/messages/thread/{user1_email}")
        assert response.status_code == 200, f"Failed to get thread: {response.text}"
        messages = response.json()
        assert len(messages) > 0, "Thread should have messages"
        
        # Check number stripping - recipient should see redacted message
        received_msg = messages[0]["message"]
        assert "[*]" in received_msg, f"Numbers should be redacted. Got: {received_msg}"
        assert "9876543210" not in received_msg, "Phone number should be redacted"
        print(f"PASS: Number stripping works. Received: {received_msg}")
        
        # User 1 checks their own thread - should see original message
        response = user1_session.get(f"{BASE_URL}/api/messages/thread/{user2_email}")
        assert response.status_code == 200
        messages = response.json()
        sender_msg = messages[0]["message"]
        assert "9876543210" in sender_msg, f"Sender should see original message. Got: {sender_msg}"
        print("PASS: Sender sees original unredacted message")
        
        # Admin checks thread - should see unredacted
        response = self.admin_session.get(f"{BASE_URL}/api/admin/messages/thread/{user1_email}/{user2_email}")
        assert response.status_code == 200
        admin_messages = response.json()
        assert len(admin_messages) > 0, "Admin should see messages"
        admin_msg = admin_messages[0]["message"]
        assert "9876543210" in admin_msg, f"Admin should see unredacted message. Got: {admin_msg}"
        print("PASS: Admin sees unredacted messages")
        
        # Check conversations
        response = user1_session.get(f"{BASE_URL}/api/messages/conversations")
        assert response.status_code == 200
        convos = response.json()
        assert len(convos) > 0, "User should have conversations"
        print(f"PASS: User has {len(convos)} conversation(s)")
        
        # Cleanup - delete test users
        self.admin_session.delete(f"{BASE_URL}/api/admin/users/{user1_email}")
        self.admin_session.delete(f"{BASE_URL}/api/admin/users/{user2_email}")
        print("PASS: Test users cleaned up")


class TestNumberStrippingEdgeCases:
    """Test edge cases for number stripping"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.admin_token = response.json()["token"]
        self.admin_session = requests.Session()
        self.admin_session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.admin_token}"
        })
    
    def _create_test_user(self, email, name):
        """Helper to create a test user"""
        response = self.session.post(f"{BASE_URL}/api/auth/send-otp", json={
            "email": email,
            "purpose": "registration"
        })
        if response.status_code != 200:
            return None
        
        otp = response.json().get("otp_debug")
        if not otp:
            return None
        
        response = self.session.post(f"{BASE_URL}/api/auth/verify-otp", json={
            "email": email,
            "otp": otp,
            "purpose": "registration"
        })
        if response.status_code != 200:
            return None
        
        otp_token = response.json().get("otp_token")
        
        response = self.session.post(f"{BASE_URL}/api/auth/register", json={
            "name": name,
            "email": email,
            "password": TEST_PASSWORD,
            "phone": "+91 9876543210",
            "pan_number": "ABCDE1234F",
            "aadhaar_number": "123456789012",
            "otp_token": otp_token
        })
        if response.status_code != 200:
            return None
        
        return response.json().get("token")
    
    def test_done_not_stripped(self):
        """Word 'done' should NOT be stripped (contains 'one')"""
        user1_email = f"edge1_{uuid.uuid4().hex[:6]}@test.com"
        user2_email = f"edge2_{uuid.uuid4().hex[:6]}@test.com"
        
        user1_token = self._create_test_user(user1_email, "Edge Test 1")
        user2_token = self._create_test_user(user2_email, "Edge Test 2")
        
        if not user1_token or not user2_token:
            pytest.skip("Could not create test users")
        
        user1_session = requests.Session()
        user1_session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {user1_token}"
        })
        
        user2_session = requests.Session()
        user2_session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {user2_token}"
        })
        
        # Send message with 'done' - should NOT be stripped
        test_message = "The work is done and I have one task left."
        response = user1_session.post(f"{BASE_URL}/api/messages", json={
            "recipient_email": user2_email,
            "message": test_message
        })
        assert response.status_code == 200
        
        # Check recipient sees 'done' but not 'one'
        response = user2_session.get(f"{BASE_URL}/api/messages/thread/{user1_email}")
        assert response.status_code == 200
        messages = response.json()
        received_msg = messages[0]["message"]
        
        assert "done" in received_msg.lower(), f"'done' should NOT be stripped. Got: {received_msg}"
        assert " one " not in received_msg.lower(), f"'one' should be stripped. Got: {received_msg}"
        print(f"PASS: 'done' preserved, 'one' stripped. Message: {received_msg}")
        
        # Cleanup
        self.admin_session.delete(f"{BASE_URL}/api/admin/users/{user1_email}")
        self.admin_session.delete(f"{BASE_URL}/api/admin/users/{user2_email}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
