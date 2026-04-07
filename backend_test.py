import requests
import sys
import json
from datetime import datetime

class HeroicHIFIAPITester:
    def __init__(self, base_url="https://hifi-missions-hub.preview.emergentagent.com"):
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

            return success, response.json() if success and response.text else {}

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

    def test_register(self, name, email, password):
        """Test user registration"""
        return self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={"name": name, "email": email, "password": password}
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
            "message": "Test donation for API testing"
        }
        return self.run_test("Create Donation", "POST", "donations", 200, data=donation_data)

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
            200,
            data={"name": "Non Admin User", "email": test_email, "password": "TestPass123!"}
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
        tester.test_logout()
    
    # Test registration with unique email
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_email = f"testuser_{timestamp}@example.com"
    tester.test_register("Test User", test_email, "TestPass123!")
    
    # Test form submissions
    print("\n📝 TESTING FORM SUBMISSIONS")
    print("-" * 40)
    donation_success, donation_response = tester.test_create_donation()
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