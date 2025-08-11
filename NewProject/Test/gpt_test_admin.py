import requests
import json
import random
import string
import time  # For unique timestamps and pauses
import sys
import warnings

# Suppress InsecureRequestWarning if you're testing against HTTP without certificate verification
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
# IMPORTANT: Fill this in with your actual FastAPI application URL
API_URL = "http://localhost:8000"  # <--- YOUR FASTAPI APP URL HERE

# If your system has a *hardcoded, unmodifiable SuperAdmin* user
# whose ID is NOT 1, change this value.
# This ID is used in negative tests to ensure regular admins cannot affect the SuperAdmin.
SUPERADMIN_ID = 1  # Commonly the first user or a hardcoded admin.

# --- GLOBAL TEST STATE ---
# Prefixes for unique usernames to avoid clashes if run multiple times
TEST_USER_PREFIX = f"testuser_{int(time.time())}_"

# Data for the user who will be manually promoted to admin
REGULAR_ADMIN_TEST_USER_DATA = {}
# Data for a normal user who will be the target of admin actions
NORMAL_TEST_USER_DATA = {}
NORMAL_USER_PROMPT_ID = None  # Stores a prompt ID created by the normal user

# Data for a third user, who will be promoted to admin by the REGULAR_ADMIN_TEST_USER,
# then immediately demoted, and finally deleted. Used for Test N6.
SECOND_ADMIN_TEST_USER_DATA = {}

# --- Test Reporting Variables ---
total_tests_run = 0
successful_tests = 0
failed_tests = 0
failed_test_cases = []  # Stores (test_name, url, method, status_code, expected_status, response_detail)


# --- UTILITY FUNCTIONS ---

def generate_random_string(length=8):
    """Generates a random string of lowercase letters and digits."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_user_data(prefix="user"):
    """Generates unique user creation data."""
    unique_id = generate_random_string(6)
    return {
        "username": f"{prefix}{unique_id}",
        "first_name": "Test",
        "last_name": "User",
        "email": f"{prefix}{unique_id}@example.com",
        "password": "SecurePassword123!"  # A strong dummy password
    }


def generate_prompt_data(content_prefix="Test prompt"):
    """Generates prompt creation data."""
    return {
        "content": f"{content_prefix} {generate_random_string(20)}",
        "is_public": True  # Make it public for easier testing
    }


def print_response_details(url, method, status_code, response_json=None):
    """Helper to print formatted response with a focus on detail for failures."""
    print(f"\n--- {method.upper()} {url} ---")
    print(f"Status Code: {status_code}")
    if response_json:
        try:
            # Print only relevant parts to avoid flooding console with HTTPValidationError
            if isinstance(response_json, dict) and "detail" in response_json:
                print(f"Response Detail: {json.dumps(response_json.get('detail'), indent=2)}")
            else:
                print(f"Response Body: {json.dumps(response_json, indent=2)}")
        except TypeError:  # If response_json is not JSON serializable
            print(f"Raw Response: {response_json}")
    else:
        print("Response Body: (No JSON content)")
    print("-" * (len(url) + len(method) + 8))


def record_test_result(test_name, url, method, status_code, expected_status_codes, response_text):
    """Records test outcome and updates global counters."""
    global total_tests_run, successful_tests, failed_tests, failed_test_cases

    total_tests_run += 1
    is_success = False

    # Ensure expected_status_codes is a list for consistent checking
    if isinstance(expected_status_codes, int):
        expected_status_codes = [expected_status_codes]

    response_detail = ""
    try:
        response_json = json.loads(response_text)
        if "detail" in response_json:
            response_detail = response_json['detail']
    except json.JSONDecodeError:
        response_detail = response_text[:150] + "..." if len(response_text) > 150 else response_text

    if status_code in expected_status_codes:
        is_success = True
        successful_tests += 1
        result_str = "SUCCESS"
    else:
        failed_tests += 1
        result_str = "FAILED"
        reason = f"Expected {expected_status_codes}, got {status_code}"
        if response_detail:
            reason += f" - Detail: {response_detail}"

        failed_test_cases.append({
            "test_name": test_name,
            "url": url,
            "method": method.upper(),
            "status_code": status_code,
            "expected_status": expected_status_codes,
            "reason": reason
        })

    print(f"\n### {test_name} ({method.upper()} {url})")
    print(f"Result: {result_str} (Status: {status_code}, Expected: {expected_status_codes})")
    if not is_success:
        print(f"Failure Reason: {reason}")
    print_response_details(url, method, status_code, json.loads(response_text) if response_text else None)


def make_request_and_report(method, url, headers=None, json_data=None, data=None, params=None,
                            expected_status_codes=200, test_name=""):
    """Wrapper to make an HTTP request and report the outcome."""
    try:
        response = requests.request(method, url, headers=headers, json=json_data, data=data, params=params,
                                    verify=False)
        record_test_result(test_name, url, method, response.status_code, expected_status_codes, response.text)
        return response
    except requests.exceptions.RequestException as e:
        record_test_result(test_name, url, method, "N/A", expected_status_codes, str(e))
        print(f"       Request Error: {e}")
        return None  # Indicate request failed
    except Exception as e:
        record_test_result(test_name, url, method, "N/A", expected_status_codes, str(e))
        print(f"       Unexpected Error: {e}")
        return None


def get_token(username, password):
    """Authenticates a user and returns an access token."""
    token_url = f"{API_URL}/auth/token"
    data = {"username": username, "password": password}  # Form data for /auth/token
    response = make_request_and_report("post", token_url, data=data, expected_status_codes=200,
                                       test_name=f"Auth: Get Token for {username}")
    if response and response.status_code == 200:
        return response.json().get("access_token")
    return None


def register_user(user_data):
    """Registers a new user."""
    register_url = f"{API_URL}/auth/register"
    response = make_request_and_report("post", register_url, json_data=user_data, expected_status_codes=201,
                                       test_name=f"User: Register {user_data['username']}")
    if response and response.status_code == 201:
        return response.json().get("id")
    return None


def create_prompt(token, prompt_data):
    """Creates a new prompt."""
    prompt_url = f"{API_URL}/prompts/"
    headers = {"Authorization": f"Bearer {token}"}
    response = make_request_and_report("post", prompt_url, headers=headers, json_data=prompt_data,
                                       expected_status_codes=201, test_name="Prompt: Create")
    if response and response.status_code == 201:
        return response.json().get("id")
    return None


def print_final_report():
    """Prints the consolidated test report."""
    print("\n" + "=" * 70)
    print("                     API Admin Privilege Test Summary")
    print("=" * 70)
    print(f"Total Tests Attempted: {total_tests_run}")
    print(f"Successful Tests:      {successful_tests}")
    print(f"Failed Tests:          {failed_tests}")

    if failed_tests > 0:
        print("\n--- Failed Test Cases Details ---")
        for i, failure in enumerate(failed_test_cases):
            print(f"\n{i + 1}. Test Name: {failure['test_name']}")
            print(f"   Endpoint: {failure['method']} {failure['url']}")
            print(f"   Status Code: {failure.get('status_code', 'N/A')}")
            print(f"   Expected: {failure['expected_status']}")
            print(f"   Reason: {failure['reason']}")
    else:
        print("\nAll admin privilege tests passed successfully!")
    print("=" * 70)


# --- Main Test Execution ---
if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

    print("--- Admin Privilege Test Setup ---")

    # Phase 1: Register and Prepare Users & Prompt
    # ---------------------------------------------
    print("\n## Phase 1: Setting Up Test Users and Data...")

    # 1. Register a Regular Admin Test User
    REGULAR_ADMIN_TEST_USER_DATA = generate_user_data(prefix=TEST_USER_PREFIX + "admin_")
    reg_admin_id = register_user(REGULAR_ADMIN_TEST_USER_DATA)
    if not reg_admin_id:
        print("FATAL ERROR: Failed to register regular admin test user. Cannot proceed. Exiting.")
        sys.exit(1)
    REGULAR_ADMIN_TEST_USER_DATA["id"] = reg_admin_id
    print(
        f"Registered **Regular Admin Test User**: Username: `{REGULAR_ADMIN_TEST_USER_DATA['username']}`, ID: `{REGULAR_ADMIN_TEST_USER_DATA['id']}`")

    # --- MANUAL INTERVENTION REQUIRED ---
    print("\n" + "=" * 80)
    print("                      MANUAL INTERVENTION REQUIRED")
    print(
        "IMPORTANT: Please log in as your **SuperAdmin** (the special, highest-privilege admin, typically ID 1) and promote the following user to a regular admin:")
    print(
        f"**User to promote**: Username: `{REGULAR_ADMIN_TEST_USER_DATA['username']}`, ID: `{REGULAR_ADMIN_TEST_USER_DATA['id']}`")
    print(
        f"You can typically do this by making a `POST` request to `{API_URL}/admin/add_admin/{REGULAR_ADMIN_TEST_USER_DATA['id']}` using your SuperAdmin's JWT token (e.g., via Swagger UI or curl).")
    print("\n**Press ENTER to continue** after you have successfully promoted the user.")
    input("==================================================================================")
    # --- END MANUAL INTERVENTION ---

    # 2. Login as the newly promoted Regular Admin
    REGULAR_ADMIN_TEST_USER_DATA["token"] = get_token(REGULAR_ADMIN_TEST_USER_DATA["username"],
                                                      REGULAR_ADMIN_TEST_USER_DATA["password"])
    if not REGULAR_ADMIN_TEST_USER_DATA["token"]:
        print(
            "FATAL ERROR: Failed to obtain token for regular admin test user after promotion. Cannot proceed. Exiting.")
        sys.exit(1)
    print("Logged in as **Regular Admin Test User**.")

    # 3. Register a Normal Test User (target for admin actions)
    NORMAL_TEST_USER_DATA = generate_user_data(prefix=TEST_USER_PREFIX + "normal_")
    normal_user_id = register_user(NORMAL_TEST_USER_DATA)
    if not normal_user_id:
        print("FATAL ERROR: Failed to register normal test user. Cannot proceed. Exiting.")
        sys.exit(1)
    NORMAL_TEST_USER_DATA["id"] = normal_user_id
    print(
        f"Registered **Normal Test User**: Username: `{NORMAL_TEST_USER_DATA['username']}`, ID: `{NORMAL_TEST_USER_DATA['id']}`")

    # 4. Login as Normal Test User to create a prompt
    NORMAL_TEST_USER_DATA["token"] = get_token(NORMAL_TEST_USER_DATA["username"], NORMAL_TEST_USER_DATA["password"])
    if not NORMAL_TEST_USER_DATA["token"]:
        print("FATAL ERROR: Failed to obtain token for normal test user. Cannot proceed. Exiting.")
        sys.exit(1)
    print("Logged in as **Normal Test User**.")

    # 5. Normal user creates a prompt (to be soft-deleted by admin later)
    NORMAL_USER_PROMPT_ID = create_prompt(NORMAL_TEST_USER_DATA["token"], generate_prompt_data())
    if not NORMAL_USER_PROMPT_ID:
        print("FATAL ERROR: Normal user failed to create prompt. Cannot proceed. Exiting.")
        sys.exit(1)
    print(f"Normal user created **Prompt ID**: `{NORMAL_USER_PROMPT_ID}`")

    # 6. Register a Second Admin Test User (to test admin-on-admin interactions for N6)
    SECOND_ADMIN_TEST_USER_DATA = generate_user_data(prefix=TEST_USER_PREFIX + "second_admin_")
    second_admin_id = register_user(SECOND_ADMIN_TEST_USER_DATA)
    if not second_admin_id:
        print("FATAL ERROR: Failed to register second admin test user. Cannot proceed. Exiting.")
        sys.exit(1)
    SECOND_ADMIN_TEST_USER_DATA["id"] = second_admin_id
    print(
        f"Registered **Second Admin Test User**: Username: `{SECOND_ADMIN_TEST_USER_DATA['username']}`, ID: `{SECOND_ADMIN_TEST_USER_DATA['id']}`")

    print("\n[PHASE 1] Setup complete. Starting admin privilege tests...")

    # --- Phase 2: Regular Admin Privilege Tests ---
    print("\n## Phase 2: Running Admin Privilege Tests (as Regular Admin)")

    admin_headers = {"Authorization": f"Bearer {REGULAR_ADMIN_TEST_USER_DATA['token']}"}

    print("\n--- POSITIVE TESTS (EXPECTED SUCCESS - 2xx status codes) ---")

    # Test P1: Regular Admin can list all users
    make_request_and_report("get", f"{API_URL}/admin/", headers=admin_headers, expected_status_codes=200,
                            test_name="Admin: View All Users")

    # Test P2: Regular Admin can list other admins (should include self and potentially SuperAdmin if the API lists them)
    make_request_and_report("get", f"{API_URL}/admin/list_admins", headers=admin_headers, expected_status_codes=200,
                            test_name="Admin: List Admins")

    # Test P3: Regular Admin can promote a normal user to admin
    # This will promote NORMAL_TEST_USER_DATA to admin.
    make_request_and_report("post", f"{API_URL}/admin/add_admin/{NORMAL_TEST_USER_DATA['id']}", headers=admin_headers,
                            expected_status_codes=201, test_name="Admin: Promote Normal User to Admin")

    # Test P4: Regular Admin can demote a user they promoted (the normal user, who is now admin)
    # The normal user is now an admin due to Test P3.
    make_request_and_report("delete", f"{API_URL}/admin/remove_admin/{NORMAL_TEST_USER_DATA['id']}",
                            headers=admin_headers, expected_status_codes=204,
                            test_name="Admin: Demote Normal User from Admin")

    # Test P5: Regular Admin can soft-delete a normal user's prompt
    if NORMAL_USER_PROMPT_ID:
        make_request_and_report("put", f"{API_URL}/admin/{NORMAL_USER_PROMPT_ID}/soft-delete", headers=admin_headers,
                                expected_status_codes=200, test_name="Admin: Soft-Delete Normal User's Prompt")
    else:
        record_test_result("Admin: Soft-Delete Normal User's Prompt", "N/A", "PUT", "N/A", 200,
                           "Prerequisite (Normal User Prompt) not met.")

    # Test P6: Regular Admin can delete a normal user (after they've been demoted from admin in P4)
    # This uses the specific admin delete endpoint.
    make_request_and_report("delete", f"{API_URL}/admin/{NORMAL_TEST_USER_DATA['id']}", headers=admin_headers,
                            expected_status_codes=204, test_name="Admin: Delete Normal User")

    print("\n--- NEGATIVE TESTS (EXPECTED FAILURES - 4xx status codes) ---")

    # Test N1: Regular Admin CANNOT promote SuperAdmin (ID 1) to admin (assuming ID 1 is already SuperAdmin)
    # Expected: 400 Bad Request (already admin) or 403 Forbidden (not allowed to modify superadmin status)
    make_request_and_report("post", f"{API_URL}/admin/add_admin/{SUPERADMIN_ID}", headers=admin_headers,
                            expected_status_codes=[400, 403],
                            test_name="Admin: Attempt to Promote SuperAdmin (ID 1) - Expected Fail")

    # Test N2: Regular Admin CANNOT demote SuperAdmin (ID 1)
    # Expected: 403 Forbidden (not allowed to touch superadmin status) or 404 Not Found (if SuperAdmin is not in demotable list)
    make_request_and_report("delete", f"{API_URL}/admin/remove_admin/{SUPERADMIN_ID}", headers=admin_headers,
                            expected_status_codes=[403, 404],
                            test_name="Admin: Attempt to Demote SuperAdmin (ID 1) - Expected Fail")

    # Test N3: Regular Admin CANNOT soft-delete SuperAdmin's (ID 1) prompt
    # Based on your OpenAPI spec: "Admins CANNOT delete posts authored by other administrators."
    # If SuperAdmin (ID 1) is an admin, a regular admin should not be able to delete their prompt.
    # Expected: 403 Forbidden (not allowed) or 404 Not Found (if prompt doesn't exist)
    make_request_and_report("put", f"{API_URL}/admin/{SUPERADMIN_ID}/soft-delete", headers=admin_headers,
                            expected_status_codes=[403, 404],
                            test_name="Admin: Attempt to Soft-Delete SuperAdmin's (ID 1) Prompt - Expected Fail")

    # Test N4: Regular Admin CANNOT delete SuperAdmin (ID 1)
    # Based on your OpenAPI spec: "An administrator could delete any account except for superadmin and other administrators."
    # Expected: 403 Forbidden
    make_request_and_report("delete", f"{API_URL}/admin/{SUPERADMIN_ID}", headers=admin_headers,
                            expected_status_codes=403,
                            test_name="Admin: Attempt to Delete SuperAdmin (ID 1) - Expected Fail")

    # Test N5: Normal User attempts to access an admin endpoint (e.g., list all users)
    normal_user_headers = {"Authorization": f"Bearer {NORMAL_TEST_USER_DATA['token']}"}
    make_request_and_report("get", f"{API_URL}/admin/", headers=normal_user_headers, expected_status_codes=403,
                            test_name="Normal User: Attempt to Access Admin Endpoint - Expected Fail")

    # Test N6: Regular Admin CANNOT delete another Regular Admin
    # First, promote the Second Admin Test User using the REGULAR_ADMIN_TEST_USER's token
    make_request_and_report("post", f"{API_URL}/admin/add_admin/{SECOND_ADMIN_TEST_USER_DATA['id']}",
                            headers=admin_headers, expected_status_codes=201,
                            test_name="Admin: Promote Second User to Admin (for N6)")

    # Now, attempt to delete the newly promoted admin using REGULAR_ADMIN_TEST_USER's token
    # OpenAPI spec: "An administrator could delete any account except for superadmin and other administrators."
    make_request_and_report("delete", f"{API_URL}/admin/{SECOND_ADMIN_TEST_USER_DATA['id']}", headers=admin_headers,
                            expected_status_codes=403,
                            test_name="Admin: Attempt to Delete Another Regular Admin (N6) - Expected Fail")

    # Clean up the second admin. This requires the SuperAdmin, or a general user delete if the admin-on-admin delete fails.
    # We will attempt to demote the second admin first using the REGULAR_ADMIN_TEST_USER, then delete it.
    make_request_and_report("delete", f"{API_URL}/admin/remove_admin/{SECOND_ADMIN_TEST_USER_DATA['id']}",
                            headers=admin_headers, expected_status_codes=204,
                            test_name="Admin: Demote Second Admin (for N6 Cleanup)")

    print("\n--- Phase 3: Cleanup ---")
    print("\n## Phase 3: Cleaning up test data...")

    # Cleanup the regular admin test user.
    # An admin should be able to delete their own account via /users/{user_id}.
    if REGULAR_ADMIN_TEST_USER_DATA.get("id"):
        cleanup_admin_headers = {"Authorization": f"Bearer {REGULAR_ADMIN_TEST_USER_DATA['token']}"}
        make_request_and_report("delete", f"{API_URL}/users/{REGULAR_ADMIN_TEST_USER_DATA['id']}",
                                headers=cleanup_admin_headers, expected_status_codes=[204, 404],
                                test_name="Cleanup: Delete Regular Admin Test User")
    else:
        print("Skipping cleanup for Regular Admin Test User: ID not found.")

    # Cleanup the second admin test user (after attempting to demote them in N6)
    if SECOND_ADMIN_TEST_USER_DATA.get("id"):
        # If the demotion was successful, the regular admin should now be able to delete this user via /admin/{user_id}
        # Or even the original registration token user, if applicable, to delete via /users/{user_id} if still active.
        # We'll try to delete them as the original regular admin test user, assuming demotion worked.
        make_request_and_report("delete", f"{API_URL}/admin/{SECOND_ADMIN_TEST_USER_DATA['id']}", headers=admin_headers,
                                expected_status_codes=[204, 404], test_name="Cleanup: Delete Second Admin Test User")
    else:
        print("Skipping cleanup for Second Admin Test User: ID not found.")

    # Note: NORMAL_TEST_USER was already deleted in P6.

    print_final_report()