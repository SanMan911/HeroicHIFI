import requests
import sys
import json
from datetime import datetime

class HeroicHIFIAPITester:
    def __init__(self, base_url="https://hifi-donor-portal.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if headers:
            test_headers.update(headers)
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(str(response_data)) < 500:
                        print(f"   Response: {response_data}")
                    elif isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
                except:
                    print(f"   Response: {response.text[:200]}...")
            else:
                self.failed_tests.append({
                    'name': name,
                    'expected': expected_status,
                    'actual': response.status_code,
                    'response': response.text[:200]
                })
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}")

            return success, response.json() if success and response.text and response.headers.get('content-type', '').startswith('application/json') else {}

        except Exception as e:
            self.failed_tests.append({
                'name': name,
                'error': str(e)
            })
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health(self):
        """Test health endpoint"""
        return self.run_test("Health Check", "GET", "health", 200)

    def test_missions_list(self):
        """Test missions list endpoint"""
        success, response = self.run_test("Get Missions List", "GET", "missions", 200)
        if success and isinstance(response, list):
            print(f"   Found {len(response)} missions")
            return True, response
        return False, []

    def test_mission_detail(self, slug):
        """Test individual mission detail endpoint"""
        return self.run_test(f"Get Mission Detail: {slug}", "GET", f"missions/{slug}", 200)

    def test_login(self, email, password):
        """Test login and get token"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": email, "password": password}
        )
        if success and 'token' in response:
            self.token = response['token']
            print(f"   Token received: {self.token[:20]}...")
            return True, response
        return False, {}

    def test_send_otp(self, email, purpose="registration"):
        """Test OTP sending"""
        return self.run_test(
            f"Send OTP for {purpose}",
            "POST",
            "auth/send-otp",
            200,
            data={"email": email, "purpose": purpose}
        )

    def test_verify_otp(self, email, otp, purpose="registration"):
        """Test OTP verification"""
        return self.run_test(
            f"Verify OTP for {purpose}",
            "POST",
            "auth/verify-otp",
            200,
            data={"email": email, "otp": otp, "purpose": purpose}
        )

    def test_register_with_otp(self, name, email, password, phone, pan_number, aadhaar_number, otp_token, age=None, dob=None, address=None):
        """Test user registration with OTP token"""
        data = {
            "name": name,
            "email": email,
            "password": password,
            "phone": phone,
            "pan_number": pan_number,
            "aadhaar_number": aadhaar_number,
            "otp_token": otp_token
        }
        if age:
            data["age"] = age
        if dob:
            data["dob"] = dob
        if address:
            data["address"] = address
            
        return self.run_test(
            "User Registration with OTP",
            "POST",
            "auth/register",
            200,
            data=data
        )

    def test_register_without_otp(self, name, email, password, phone, pan_number, aadhaar_number):
        """Test user registration without OTP token (should fail)"""
        return self.run_test(
            "User Registration without OTP (should fail)",
            "POST",
            "auth/register",
            400,
            data={
                "name": name,
                "email": email,
                "password": password,
                "phone": phone,
                "pan_number": pan_number,
                "aadhaar_number": aadhaar_number,
                "otp_token": "invalid_token"
            }
        )

    def test_get_me(self):
        """Test get current user endpoint"""
        return self.run_test("Get Current User", "GET", "auth/me", 200)

    def test_logout(self):
        """Test logout endpoint"""
        return self.run_test("Logout", "POST", "auth/logout", 200)

    def test_create_donation(self):
        """Test donation creation"""
        donation_data = {
            "name": "Test Donor",
            "email": "testdonor@example.com",
            "phone": "9876543210",
            "amount": 1000,
            "pan_number": "ABCDE1234F",
            "aadhaar_number": "123456789012",
            "address": "Test Address",
            "message": "Test donation for API testing"
        }
        return self.run_test("Create Donation", "POST", "donations", 200, data=donation_data)

    def test_create_donation_without_pan(self):
        """Test donation creation without PAN (should fail)"""
        donation_data = {
            "name": "Test Donor No PAN",
            "email": "testdonornopan@example.com",
            "phone": "9876543210",
            "amount": 1000,
            "message": "Test donation without PAN"
        }
        return self.run_test("Create Donation without PAN", "POST", "donations", 422, data=donation_data)

    def test_create_order_with_otp(self, otp_token):
        """Test donation order creation with OTP token for non-logged users"""
        donation_data = {
            "name": "Test OTP Donor",
            "email": "testotpdonor@example.com",
            "phone": "9876543210",
            "amount": 2000,
            "pan_number": "ABCDE1234F",
            "aadhaar_number": "123456789012",
            "address": "Test Address",
            "message": "Test donation with OTP",
            "otp_token": otp_token
        }
        return self.run_test("Create Order with OTP", "POST", "donations/create-order", 200, data=donation_data)

    def test_create_order_without_auth_or_otp(self):
        """Test donation order creation without auth or OTP (should fail)"""
        donation_data = {
            "name": "Test No Auth Donor",
            "email": "testnoauth@example.com",
            "phone": "9876543210",
            "amount": 1500,
            "pan_number": "ABCDE1234F",
            "message": "Test donation without auth or OTP"
        }
        # Temporarily remove token
        temp_token = self.token
        self.token = None
        result = self.run_test("Create Order without Auth/OTP", "POST", "donations/create-order", 400, data=donation_data)
        self.token = temp_token
        return result

    def test_80g_certificate(self, donation_id):
        """Test 80G certificate generation"""
        return self.run_test(
            "Download 80G Certificate",
            "GET",
            f"donations/{donation_id}/certificate",
            200
        )

    def test_80g_certificate_without_pan(self, donation_id):
        """Test 80G certificate generation without PAN (should fail)"""
        return self.run_test(
            "Download 80G Certificate without PAN",
            "GET",
            f"donations/{donation_id}/certificate",
            400
        )

    def test_create_volunteer(self):
        """Test volunteer registration"""
        volunteer_data = {
            "name": "Test Volunteer",
            "email": "testvolunteer@example.com",
            "phone": "9876543210",
            "city": "Test City",
            "interests": ["mission-shakti", "mission-roshni"],
            "message": "Test volunteer registration"
        }
        return self.run_test("Register Volunteer", "POST", "volunteers", 200, data=volunteer_data)

    def test_create_query(self):
        """Test query submission"""
        query_data = {
            "name": "Test User",
            "email": "testuser@example.com",
            "mission": "mission-shakti",
            "subject": "Test Query",
            "message": "This is a test query for API testing"
        }
        return self.run_test("Submit Query", "POST", "queries", 200, data=query_data)

    def test_razorpay_create_order(self):
        """Test Razorpay create order endpoint (should return null order_id when keys not set)"""
        donation_data = {
            "name": "Test Razorpay Donor",
            "email": "testrazorpay@example.com",
            "phone": "9876543210",
            "amount": 2000,
            "pan_number": "ABCDE1234F",
            "message": "Test Razorpay donation"
        }
        success, response = self.run_test("Create Razorpay Order", "POST", "donations/create-order", 200, data=donation_data)
        if success:
            # Should return razorpay_order_id=null when keys not configured
            if response.get('razorpay_order_id') is None:
                print("   ✅ Correctly returned null order_id (Razorpay keys not configured)")
            else:
                print("   ⚠️  Unexpected: Got razorpay_order_id when keys should not be set")
        return success, response

    def test_admin_stats(self):
        """Test admin stats endpoint (requires admin auth)"""
        return self.run_test("Get Admin Stats", "GET", "admin/stats", 200)

    def test_admin_donations(self):
        """Test admin donations list endpoint"""
        return self.run_test("Get Admin Donations", "GET", "admin/donations", 200)

    def test_admin_volunteers(self):
        """Test admin volunteers list endpoint"""
        return self.run_test("Get Admin Volunteers", "GET", "admin/volunteers", 200)

    def test_admin_queries(self):
        """Test admin queries list endpoint"""
        return self.run_test("Get Admin Queries", "GET", "admin/queries", 200)

    def test_admin_users(self):
        """Test admin users list endpoint"""
        return self.run_test("Get Admin Users", "GET", "admin/users", 200)

    def test_admin_delete_user(self, user_email):
        """Test admin delete user endpoint"""
        return self.run_test(
            f"Delete User {user_email}",
            "DELETE",
            f"admin/users/{user_email}",
            200
        )

    def test_admin_delete_self(self, admin_email):
        """Test admin cannot delete self (should fail)"""
        return self.run_test(
            "Admin Delete Self (should fail)",
            "DELETE",
            f"admin/users/{admin_email}",
            400
        )

    def test_admin_update_donation_status(self, donation_id, status):
        """Test updating donation status"""
        return self.run_test(
            f"Update Donation Status to {status}",
            "PUT",
            f"admin/donations/{donation_id}/status",
            200,
            data={"status": status}
        )

    def test_admin_update_volunteer_status(self, volunteer_id, status):
        """Test updating volunteer status"""
        return self.run_test(
            f"Update Volunteer Status to {status}",
            "PUT",
            f"admin/volunteers/{volunteer_id}/status",
            200,
            data={"status": status}
        )

    def test_admin_update_query_status(self, query_id, status):
        """Test updating query status"""
        return self.run_test(
            f"Update Query Status to {status}",
            "PUT",
            f"admin/queries/{query_id}/status",
            200,
            data={"status": status}
        )

    def test_non_admin_access(self):
        """Test that non-admin users get 403 on admin endpoints"""
        # First register a regular user and login
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_email = f"nonadmin_{timestamp}@example.com"
        
        # Register regular user
        reg_success, reg_response = self.run_test(
            "Register Non-Admin User",
            "POST",
            "auth/register",
            400,  # Should fail because no OTP token
            data={
                "name": "Non Admin User", 
                "email": test_email, 
                "password": "TestPass123!",
                "phone": "9876543210",
                "pan_number": "ABCDE1234F",
                "aadhaar_number": "123456789012",
                "otp_token": "invalid_token"
            }
        )
        
        if reg_success and 'token' in reg_response:
            # Store current admin token
            admin_token = self.token
            # Use non-admin token
            self.token = reg_response['token']
            
            # Test admin endpoints should return 403
            print("\n   Testing non-admin access to admin endpoints...")
            self.run_test("Non-Admin Stats Access", "GET", "admin/stats", 403)
            self.run_test("Non-Admin Donations Access", "GET", "admin/donations", 403)
            self.run_test("Non-Admin Volunteers Access", "GET", "admin/volunteers", 403)
            self.run_test("Non-Admin Queries Access", "GET", "admin/queries", 403)
            
            # Restore admin token
            self.token = admin_token
            return True
        return False

def main():
    print("🚀 Starting Heroic HIFI Foundation API Testing")
    print("=" * 60)
    
    # Setup
    tester = HeroicHIFIAPITester()
    
    # Test basic endpoints
    print("\n📋 TESTING BASIC ENDPOINTS")
    print("-" * 40)
    tester.test_health()
    
    # Test missions endpoints
    print("\n🎯 TESTING MISSIONS ENDPOINTS")
    print("-" * 40)
    success, missions = tester.test_missions_list()
    
    if success and missions:
        # Test first few mission details
        mission_slugs = [m.get('slug') for m in missions[:3] if m.get('slug')]
        for slug in mission_slugs:
            tester.test_mission_detail(slug)
    
    # Test OTP verification flow
    print("\n📧 TESTING OTP VERIFICATION")
    print("-" * 40)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_email = f"testuser_{timestamp}@example.com"
    
    # Test OTP sending
    otp_send_success, otp_response = tester.test_send_otp(test_email, "registration")
    otp_debug = None
    otp_token = None
    
    if otp_send_success:
        otp_debug = otp_response.get('otp_debug')
        if otp_debug:
            print(f"   Debug OTP received: {otp_debug}")
            # Test OTP verification
            verify_success, verify_response = tester.test_verify_otp(test_email, otp_debug, "registration")
            if verify_success:
                otp_token = verify_response.get('otp_token')
                print(f"   OTP Token received: {otp_token[:20]}...")
    
    # Test registration with OTP
    print("\n🔐 TESTING REGISTRATION WITH OTP")
    print("-" * 40)
    
    if otp_token:
        # Test successful registration with OTP
        reg_success, reg_response = tester.test_register_with_otp(
            "Test User", test_email, "TestPass123!", "9876543210", 
            "ABCDE1234F", "123456789012", otp_token, 
            age=25, dob="1999-01-01", address="Test Address"
        )
        
        if reg_success and 'token' in reg_response:
            print(f"   Registration successful, token: {reg_response['token'][:20]}...")
    
    # Test registration without OTP (should fail)
    test_email_2 = f"testuser2_{timestamp}@example.com"
    tester.test_register_without_otp(
        "Test User 2", test_email_2, "TestPass123!", "9876543210", 
        "ABCDE1234F", "123456789012"
    )
    
    # Test authentication
    print("\n🔐 TESTING AUTHENTICATION")
    print("-" * 40)
    
    # Test admin login
    admin_email = "admin@heroichifi.org"
    admin_password = "HHF@admin2024"
    login_success, login_response = tester.test_login(admin_email, admin_password)
    
    if login_success:
        # Test authenticated endpoints
        tester.test_get_me()
        
        # Check if login response includes new fields
        user_data = login_response.get('user', {})
        expected_fields = ['phone', 'pan_number', 'aadhaar_number', 'address', 'age', 'dob']
        print("   Checking login response fields:")
        for field in expected_fields:
            if field in user_data:
                print(f"   ✅ {field}: {user_data[field]}")
            else:
                print(f"   ❌ Missing field: {field}")
        
        tester.test_logout()
    
    # Test donation flow with OTP
    print("\n💰 TESTING DONATION WITH OTP")
    print("-" * 40)
    
    # Test OTP for donation
    donation_email = f"donor_{timestamp}@example.com"
    otp_send_success, otp_response = tester.test_send_otp(donation_email, "donation")
    donation_otp_token = None
    
    if otp_send_success:
        otp_debug = otp_response.get('otp_debug')
        if otp_debug:
            verify_success, verify_response = tester.test_verify_otp(donation_email, otp_debug, "donation")
            if verify_success:
                donation_otp_token = verify_response.get('otp_token')
    
    # Test donation order creation with OTP
    if donation_otp_token:
        order_success, order_response = tester.test_create_order_with_otp(donation_otp_token)
        if order_success:
            donation_id = order_response.get('donation', {}).get('id')
            if donation_id:
                print(f"   Donation created with ID: {donation_id}")
                # Test 80G certificate generation
                tester.test_80g_certificate(donation_id)
    
    # Test donation without auth or OTP (should fail)
    tester.test_create_order_without_auth_or_otp()
    
    # Test form submissions
    print("\n📝 TESTING FORM SUBMISSIONS")
    print("-" * 40)
    donation_success, donation_response = tester.test_create_donation()
    tester.test_create_donation_without_pan()
    volunteer_success, volunteer_response = tester.test_create_volunteer()
    query_success, query_response = tester.test_create_query()
    
    # Test Razorpay create order (should return null when keys not set)
    print("\n💳 TESTING RAZORPAY INTEGRATION")
    print("-" * 40)
    tester.test_razorpay_create_order()
    
    # Test admin endpoints (need admin login first)
    print("\n👑 TESTING ADMIN ENDPOINTS")
    print("-" * 40)
    
    # Re-login as admin for admin tests
    admin_login_success, _ = tester.test_login(admin_email, admin_password)
    
    if admin_login_success:
        # Test admin stats and lists
        tester.test_admin_stats()
        admin_donations_success, admin_donations = tester.test_admin_donations()
        admin_volunteers_success, admin_volunteers = tester.test_admin_volunteers()
        admin_queries_success, admin_queries = tester.test_admin_queries()
        admin_users_success, admin_users = tester.test_admin_users()
        
        # Test status updates if we have data
        if admin_donations_success and admin_donations and len(admin_donations) > 0:
            donation_id = admin_donations[0].get('id')
            if donation_id:
                tester.test_admin_update_donation_status(donation_id, "confirmed")
        
        if admin_volunteers_success and admin_volunteers and len(admin_volunteers) > 0:
            volunteer_id = admin_volunteers[0].get('id')
            if volunteer_id:
                tester.test_admin_update_volunteer_status(volunteer_id, "approved")
        
        if admin_queries_success and admin_queries and len(admin_queries) > 0:
            query_id = admin_queries[0].get('id')
            if query_id:
                tester.test_admin_update_query_status(query_id, "responded")
        
        # Test user management
        print("\n👥 TESTING USER MANAGEMENT")
        print("-" * 40)
        
        if admin_users_success and admin_users:
            print(f"   Found {len(admin_users)} users")
            # Find a non-admin user to test deletion
            non_admin_user = None
            for user in admin_users:
                if user.get('role') != 'admin' and user.get('email') != admin_email:
                    non_admin_user = user
                    break
            
            if non_admin_user:
                # Test deleting non-admin user
                tester.test_admin_delete_user(non_admin_user['email'])
            
            # Test admin cannot delete self
            tester.test_admin_delete_self(admin_email)
        
        # Test non-admin access restrictions
        print("\n🚫 TESTING NON-ADMIN ACCESS RESTRICTIONS")
        print("-" * 40)
        tester.test_non_admin_access()
    
    # Print results
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {len(tester.failed_tests)}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.failed_tests:
        print("\n❌ FAILED TESTS:")
        for i, test in enumerate(tester.failed_tests, 1):
            print(f"{i}. {test['name']}")
            if 'expected' in test:
                print(f"   Expected: {test['expected']}, Got: {test['actual']}")
                print(f"   Response: {test['response']}")
            if 'error' in test:
                print(f"   Error: {test['error']}")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())