"""
Test suite for new features in Heroic HIFI Foundation:
- Role Change Requests (POST /api/role-requests, GET /api/admin/role-requests, PUT approve/reject)
- Drives CRUD (GET /api/drives, POST/DELETE /api/admin/drives)
- Activity Logs (GET /api/admin/activity-logs)
- Admin Stats (role_requests.pending, members.total, drives.total)
- Registration with role selection (member/volunteer)
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@heroichifi.org"
ADMIN_PASSWORD = "HHF@admin2024"


class TestAdminLogin:
    """Test admin login works with correct credentials"""
    
    def test_admin_login_success(self):
        """Admin login works with admin@heroichifi.org / HHF@admin2024"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert data["user"]["role"] == "admin"
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"✓ Admin login successful, role: {data['user']['role']}")


class TestAdminStats:
    """Test admin stats endpoint returns new fields"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_admin_stats_has_new_fields(self, admin_token):
        """Admin stats endpoint returns role_requests, members, drives counts"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check new fields exist
        assert "role_requests" in data, "Missing role_requests in stats"
        assert "pending" in data["role_requests"], "Missing role_requests.pending"
        
        assert "members" in data, "Missing members in stats"
        assert "total" in data["members"], "Missing members.total"
        
        assert "drives" in data, "Missing drives in stats"
        assert "total" in data["drives"], "Missing drives.total"
        
        assert "volunteers" in data, "Missing volunteers in stats"
        
        print(f"✓ Admin stats: volunteers={data['volunteers']['total']}, members={data['members']['total']}, pending_requests={data['role_requests']['pending']}, drives={data['drives']['total']}")


class TestDrives:
    """Test Drives CRUD operations"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_get_drives_public(self):
        """GET /api/drives is public (no auth required)"""
        response = requests.get(f"{BASE_URL}/api/drives")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"✓ GET /api/drives returns {len(response.json())} drives (public)")
    
    def test_create_drive_requires_auth(self):
        """POST /api/admin/drives requires admin auth"""
        response = requests.post(f"{BASE_URL}/api/admin/drives", json={
            "title": "Test Drive",
            "description": "Test",
            "date": "2026-02-01",
            "location": "Test Location",
            "drive_type": "upcoming"
        })
        assert response.status_code == 401
        print("✓ POST /api/admin/drives requires auth (401)")
    
    def test_create_drive_success(self, admin_token):
        """Admin can create a new drive"""
        drive_data = {
            "title": f"TEST_Drive_{uuid.uuid4().hex[:8]}",
            "description": "Test drive for automated testing",
            "date": "2026-03-15",
            "location": "Test City, India",
            "drive_type": "upcoming"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/drives",
            json=drive_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Create drive failed: {response.text}"
        data = response.json()
        assert "drive" in data
        assert data["drive"]["title"] == drive_data["title"]
        assert data["drive"]["drive_type"] == "upcoming"
        assert "id" in data["drive"]
        print(f"✓ Created drive: {data['drive']['title']} (id: {data['drive']['id'][:8]}...)")
        return data["drive"]["id"]
    
    def test_create_and_delete_drive(self, admin_token):
        """Admin can create and delete a drive"""
        # Create
        drive_data = {
            "title": f"TEST_DeleteMe_{uuid.uuid4().hex[:8]}",
            "description": "Will be deleted",
            "date": "2026-04-01",
            "location": "Nowhere",
            "drive_type": "past"
        }
        create_resp = requests.post(
            f"{BASE_URL}/api/admin/drives",
            json=drive_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert create_resp.status_code == 200
        drive_id = create_resp.json()["drive"]["id"]
        
        # Verify it exists
        get_resp = requests.get(f"{BASE_URL}/api/drives")
        drives = get_resp.json()
        assert any(d["id"] == drive_id for d in drives), "Created drive not found in list"
        
        # Delete
        delete_resp = requests.delete(
            f"{BASE_URL}/api/admin/drives/{drive_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert delete_resp.status_code == 200
        
        # Verify deleted
        get_resp2 = requests.get(f"{BASE_URL}/api/drives")
        drives2 = get_resp2.json()
        assert not any(d["id"] == drive_id for d in drives2), "Drive still exists after delete"
        print(f"✓ Drive created and deleted successfully")
    
    def test_delete_nonexistent_drive(self, admin_token):
        """Deleting nonexistent drive returns 404"""
        response = requests.delete(
            f"{BASE_URL}/api/admin/drives/nonexistent-id-12345",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404
        print("✓ DELETE nonexistent drive returns 404")


class TestRoleRequests:
    """Test Role Change Request flow"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_get_admin_role_requests(self, admin_token):
        """GET /api/admin/role-requests returns list"""
        response = requests.get(
            f"{BASE_URL}/api/admin/role-requests",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"✓ GET /api/admin/role-requests returns {len(response.json())} requests")
    
    def test_role_requests_requires_auth(self):
        """POST /api/role-requests requires authentication"""
        response = requests.post(f"{BASE_URL}/api/role-requests", json={
            "requested_role": "volunteer",
            "reason": "Test"
        })
        assert response.status_code == 401
        print("✓ POST /api/role-requests requires auth (401)")
    
    def test_admin_role_requests_requires_admin(self):
        """GET /api/admin/role-requests requires admin role"""
        response = requests.get(f"{BASE_URL}/api/admin/role-requests")
        assert response.status_code == 401
        print("✓ GET /api/admin/role-requests requires admin auth (401)")
    
    def test_approve_nonexistent_request(self, admin_token):
        """Approving nonexistent request returns 404"""
        response = requests.put(
            f"{BASE_URL}/api/admin/role-requests/nonexistent-id/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404
        print("✓ Approve nonexistent request returns 404")
    
    def test_reject_nonexistent_request(self, admin_token):
        """Rejecting nonexistent request returns 404"""
        response = requests.put(
            f"{BASE_URL}/api/admin/role-requests/nonexistent-id/reject",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404
        print("✓ Reject nonexistent request returns 404")


class TestActivityLogs:
    """Test Activity Logs endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_get_activity_logs(self, admin_token):
        """GET /api/admin/activity-logs returns list of logs"""
        response = requests.get(
            f"{BASE_URL}/api/admin/activity-logs",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        logs = response.json()
        assert isinstance(logs, list)
        
        # Check log structure if any exist
        if logs:
            log = logs[0]
            assert "action" in log
            assert "timestamp" in log
            print(f"✓ GET /api/admin/activity-logs returns {len(logs)} logs, latest action: {log['action']}")
        else:
            print("✓ GET /api/admin/activity-logs returns empty list (no activity yet)")
    
    def test_activity_logs_requires_admin(self):
        """GET /api/admin/activity-logs requires admin auth"""
        response = requests.get(f"{BASE_URL}/api/admin/activity-logs")
        assert response.status_code == 401
        print("✓ GET /api/admin/activity-logs requires admin auth (401)")
    
    def test_activity_logs_with_limit(self, admin_token):
        """Activity logs respects limit parameter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/activity-logs?limit=5",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        logs = response.json()
        assert len(logs) <= 5
        print(f"✓ Activity logs with limit=5 returns {len(logs)} logs")


class TestRoster:
    """Test unified roster (admin/users endpoint)"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_get_users_list(self, admin_token):
        """GET /api/admin/users returns unified roster"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        
        # Check user structure
        if users:
            user = users[0]
            assert "email" in user
            assert "role" in user
            # Check roles are valid
            roles = set(u["role"] for u in users)
            print(f"✓ GET /api/admin/users returns {len(users)} users, roles: {roles}")
        else:
            print("✓ GET /api/admin/users returns empty list")
    
    def test_users_requires_admin(self):
        """GET /api/admin/users requires admin auth"""
        response = requests.get(f"{BASE_URL}/api/admin/users")
        assert response.status_code == 401
        print("✓ GET /api/admin/users requires admin auth (401)")


class TestRegistrationRoleSelection:
    """Test registration with role selection"""
    
    def test_registration_endpoint_exists(self):
        """POST /api/auth/register endpoint exists"""
        # Just check endpoint exists (will fail validation but not 404)
        response = requests.post(f"{BASE_URL}/api/auth/register", json={})
        assert response.status_code != 404, "Register endpoint not found"
        # Should be 422 (validation error) or 400 (missing OTP)
        assert response.status_code in [400, 422]
        print("✓ POST /api/auth/register endpoint exists")
    
    def test_send_otp_endpoint(self):
        """POST /api/auth/send-otp endpoint works"""
        response = requests.post(f"{BASE_URL}/api/auth/send-otp", json={
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "purpose": "registration"
        })
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ POST /api/auth/send-otp works: {data['message'][:50]}...")


class TestAdminUserManagement:
    """Test admin can delete users"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_delete_nonexistent_user(self, admin_token):
        """DELETE /api/admin/users/{email} returns 404 for nonexistent user"""
        response = requests.delete(
            f"{BASE_URL}/api/admin/users/nonexistent@example.com",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404
        print("✓ DELETE nonexistent user returns 404")
    
    def test_admin_cannot_delete_self(self, admin_token):
        """Admin cannot delete their own account"""
        response = requests.delete(
            f"{BASE_URL}/api/admin/users/{ADMIN_EMAIL}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        assert "own account" in response.json().get("detail", "").lower()
        print("✓ Admin cannot delete self (400)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
