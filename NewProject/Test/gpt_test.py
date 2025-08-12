import requests
import json
import random
import string
import time
import sys
import warnings

# Suppress InsecureRequestWarning if you're testing against HTTP without certificate verification
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
# IMPORTANT: Fill this in with your actual FastAPI application URL
API_URL = "http://localhost:8000"  # <--- YOUR FASTAPI APP URL HERE (was 10.6.20.153:8000)

# --- GLOBAL TEST STATE ---
TEST_USER_PREFIX = f"testuser_{int(time.time())}_"

PRIMARY_TEST_USER_DATA = {}
PRIMARY_TEST_USER_PROMPT_ID = None
PRIMARY_TEST_USER_COMMENT_ID = None

SECONDARY_TEST_USER_DATA = {}
SECONDARY_TEST_USER_PUBLIC_PROMPT_ID = None
SECONDARY_TEST_USER_PRIVATE_PROMPT_ID = None  # Renamed for clarity on public/private

THIRD_TEST_USER_DATA = {}  # For liking/unliking by multiple users

# List to keep track of all dynamically created user IDs for final cleanup
CREATED_USER_IDS = []

# --- Test Reporting Variables ---
total_tests_run = 0
successful_tests = 0
failed_tests = 0
failed_test_cases = []


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


def generate_prompt_data(content_prefix="Test prompt", is_public=None):
    """Generates prompt creation data."""
    if is_public is None:
        is_public = random.choice([True, False])
    return {
        "content": f"{content_prefix} {generate_random_string(20)}",
        "is_public": is_public
    }


def generate_comment_data(content_prefix="Test comment"):
    """Generates comment creation data."""
    return {
        "content": f"{content_prefix} {generate_random_string(15)}"
    }


def print_response_details(url, method, status_code, response_json=None):
    """Helper to print formatted response with a focus on detail for failures."""
    print(f"\n--- {method.upper()} {url} ---")
    print(f"Status Code: {status_code}")
    if response_json:
        try:
            if isinstance(response_json, dict) and "detail" in response_json:
                print(f"Response Detail: {json.dumps(response_json.get('detail'), indent=2)}")
            else:
                print(f"Response Body: {json.dumps(response_json, indent=2)}")
        except TypeError:
            print(f"Raw Response: {response_json}")
    else:
        print("Response Body: (No JSON content)")
    print("-" * (len(url) + len(method) + 8))


def record_test_result(test_name, url, method, status_code, expected_status_codes, response_text):
    """Records test outcome and updates global counters."""
    global total_tests_run, successful_tests, failed_tests, failed_test_cases

    total_tests_run += 1
    is_success = False

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
        return None
    except Exception as e:
        record_test_result(test_name, url, method, "N/A", expected_status_codes, str(e))
        print(f"       Unexpected Error: {e}")
        return None


def get_token(username, password):
    """Authenticates a user and returns an access token."""
    token_url = f"{API_URL}/auth/token"
    data = {"username": username, "password": password}
    response = make_request_and_report("post", token_url, data=data, expected_status_codes=200,
                                       test_name=f"Auth: Get Token for {username}")
    if response and response.status_code == 200:
        return response.json().get("access_token")
    return None


def register_user(user_data):
    """Registers a new user."""
    global CREATED_USER_IDS
    register_url = f"{API_URL}/auth/register"
    response = make_request_and_report("post", register_url, json_data=user_data, expected_status_codes=201,
                                       test_name=f"User: Register {user_data['username']}")
    if response and response.status_code == 201:
        user_id = response.json().get("id")
        CREATED_USER_IDS.append(user_id)  # Add to list for cleanup
        return user_id
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


def create_comment(token, prompt_id, comment_data):
    """Creates a new comment on a given prompt."""
    comment_url = f"{API_URL}/prompts/{prompt_id}/comments"
    headers = {"Authorization": f"Bearer {token}"}
    response = make_request_and_report("post", comment_url, headers=headers, json_data=comment_data,
                                       expected_status_codes=201, test_name=f"Comment: Create on Prompt {prompt_id}")
    if response and response.status_code == 201:
        return response.json().get("comment_id")  # Assuming the response returns 'comment_id'
    return None


def print_final_report():
    """Prints the consolidated test report."""
    print("\n" + "=" * 70)
    print("                     API User Functionalities Test Summary")
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
        print("\nAll user functionality tests passed successfully!")
    print("=" * 70)


# --- Main Test Execution ---
if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

    print("--- User Functionalities Test Setup ---")

    # Phase 1: Register and Prepare Users & Data
    # ---------------------------------------------
    print("\n## Phase 1: Setting Up Test Users and Data...")

    # 1. Register Primary Test User
    PRIMARY_TEST_USER_DATA = generate_user_data(prefix=TEST_USER_PREFIX + "primary_")
    primary_user_id = register_user(PRIMARY_TEST_USER_DATA)
    if not primary_user_id:
        print("FATAL ERROR: Failed to register primary test user. Cannot proceed. Exiting.")
        sys.exit(1)
    PRIMARY_TEST_USER_DATA["id"] = primary_user_id
    print(
        f"Registered **Primary Test User**: Username: `{PRIMARY_TEST_USER_DATA['username']}`, ID: `{PRIMARY_TEST_USER_DATA['id']}`")

    # 2. Login as Primary Test User
    PRIMARY_TEST_USER_DATA["token"] = get_token(PRIMARY_TEST_USER_DATA["username"], PRIMARY_TEST_USER_DATA["password"])
    if not PRIMARY_TEST_USER_DATA["token"]:
        print("FATAL ERROR: Failed to obtain token for primary test user. Cannot proceed. Exiting.")
        sys.exit(1)
    primary_user_headers = {"Authorization": f"Bearer {PRIMARY_TEST_USER_DATA['token']}"}
    print("Logged in as **Primary Test User**.")

    # 3. Register Secondary Test User
    SECONDARY_TEST_USER_DATA = generate_user_data(prefix=TEST_USER_PREFIX + "secondary_")
    secondary_user_id = register_user(SECONDARY_TEST_USER_DATA)
    if not secondary_user_id:
        print("FATAL ERROR: Failed to register secondary test user. Cannot proceed. Exiting.")
        sys.exit(1)
    SECONDARY_TEST_USER_DATA["id"] = secondary_user_id
    print(
        f"Registered **Secondary Test User**: Username: `{SECONDARY_TEST_USER_DATA['username']}`, ID: `{SECONDARY_TEST_USER_DATA['id']}`")

    # 4. Login as Secondary Test User
    SECONDARY_TEST_USER_DATA["token"] = get_token(SECONDARY_TEST_USER_DATA["username"],
                                                  SECONDARY_TEST_USER_DATA["password"])
    if not SECONDARY_TEST_USER_DATA["token"]:
        print("FATAL ERROR: Failed to obtain token for secondary test user. Cannot proceed. Exiting.")
        sys.exit(1)
    secondary_user_headers = {"Authorization": f"Bearer {SECONDARY_TEST_USER_DATA['token']}"}
    print("Logged in as **Secondary Test User**.")

    # 5. Register Third Test User (for liking/unliking by multiple users)
    THIRD_TEST_USER_DATA = generate_user_data(prefix=TEST_USER_PREFIX + "third_")
    third_user_id = register_user(THIRD_TEST_USER_DATA)
    if not third_user_id:
        print("FATAL ERROR: Failed to register third test user. Cannot proceed. Exiting.")
        sys.exit(1)
    THIRD_TEST_USER_DATA["id"] = third_user_id
    print(
        f"Registered **Third Test User**: Username: `{THIRD_TEST_USER_DATA['username']}`, ID: `{THIRD_TEST_USER_DATA['id']}`")

    # 6. Login as Third Test User
    THIRD_TEST_USER_DATA["token"] = get_token(THIRD_TEST_USER_DATA["username"], THIRD_TEST_USER_DATA["password"])
    if not THIRD_TEST_USER_DATA["token"]:
        print("FATAL ERROR: Failed to obtain token for third test user. Cannot proceed. Exiting.")
        sys.exit(1)
    third_user_headers = {"Authorization": f"Bearer {THIRD_TEST_USER_DATA['token']}"}
    print("Logged in as **Third Test User**.")

    # 7. Primary user creates a prompt
    PRIMARY_TEST_USER_PROMPT_ID = create_prompt(PRIMARY_TEST_USER_DATA["token"],
                                                generate_prompt_data(content_prefix="Primary User's Prompt",
                                                                     is_public=True))
    if not PRIMARY_TEST_USER_PROMPT_ID:
        print("FATAL ERROR: Primary user failed to create prompt. Cannot proceed. Exiting.")
        sys.exit(1)
    print(f"Primary user created **Prompt ID**: `{PRIMARY_TEST_USER_PROMPT_ID}`")

    # 8. Secondary user creates a PUBLIC prompt (for viewing/liking by others)
    SECONDARY_TEST_USER_PUBLIC_PROMPT_ID = create_prompt(SECONDARY_TEST_USER_DATA["token"], generate_prompt_data(
        content_prefix="Secondary User's Public Prompt", is_public=True))
    if not SECONDARY_TEST_USER_PUBLIC_PROMPT_ID:
        print("FATAL ERROR: Secondary user failed to create public prompt. Cannot proceed. Exiting.")
        sys.exit(1)
    print(f"Secondary user created **Public Prompt ID**: `{SECONDARY_TEST_USER_PUBLIC_PROMPT_ID}`")

    # 9. Secondary user creates a PRIVATE prompt (to test visibility)
    SECONDARY_TEST_USER_PRIVATE_PROMPT_ID = create_prompt(SECONDARY_TEST_USER_DATA["token"], generate_prompt_data(
        content_prefix="Secondary User's Private Prompt", is_public=False))
    if not SECONDARY_TEST_USER_PRIVATE_PROMPT_ID:
        print("FATAL ERROR: Secondary user failed to create private prompt. Cannot proceed. Exiting.")
        sys.exit(1)
    print(f"Secondary user created **Private Prompt ID**: `{SECONDARY_TEST_USER_PRIVATE_PROMPT_ID}`")

    # 10. Primary user creates a comment on their own prompt
    PRIMARY_TEST_USER_COMMENT_ID = create_comment(PRIMARY_TEST_USER_DATA["token"], PRIMARY_TEST_USER_PROMPT_ID,
                                                  generate_comment_data(content_prefix="Primary's Comment"))
    if not PRIMARY_TEST_USER_COMMENT_ID:
        print("FATAL ERROR: Primary user failed to create comment. Cannot proceed. Exiting.")
        sys.exit(1)
    print(
        f"Primary user created **Comment ID**: `{PRIMARY_TEST_USER_COMMENT_ID}` on Prompt `{PRIMARY_TEST_USER_PROMPT_ID}`")

    print("\n[PHASE 1] Setup complete. Starting user functionalities tests...")

    # --- Phase 2: User Functionalities Tests ---
    print("\n## Phase 2: Running User Functionalities Tests (as Primary Test User)")

    # --- USER PROFILE TESTS ---
    print("\n--- User Profile Tests ---")

    # Test U1: Get own user profile (using /auth/me)
    make_request_and_report("get", f"{API_URL}/auth/me", headers=primary_user_headers, expected_status_codes=200,
                            test_name="User: Get Own Profile (via /auth/me)")

    # Test U2: Update own user password (Correct endpoint from OpenAPI)
    old_password = PRIMARY_TEST_USER_DATA["password"]
    new_password = "NewSecurePassword456!"
    update_password_data = {
        "current_password": old_password,
        "new_password": new_password
    }
    make_request_and_report("put", f"{API_URL}/users/me/password", headers=primary_user_headers,
                            json_data=update_password_data, expected_status_codes=200,
                            test_name="User: Update Own Password")
    # Update stored password for subsequent logins
    PRIMARY_TEST_USER_DATA["password"] = new_password
    # Re-login to get a fresh token with new password (good practice)
    PRIMARY_TEST_USER_DATA["token"] = get_token(PRIMARY_TEST_USER_DATA["username"], PRIMARY_TEST_USER_DATA["password"])
    primary_user_headers = {"Authorization": f"Bearer {PRIMARY_TEST_USER_DATA['token']}"}

    # Test U3: Get another user's profile (Positive - if public)
    make_request_and_report("get", f"{API_URL}/users/{SECONDARY_TEST_USER_DATA['id']}", headers=primary_user_headers,
                            expected_status_codes=200, test_name="User: Get Another User's Public Profile")

    # Test U4: Unauthorized access to own profile (No Token) - using /auth/me
    make_request_and_report("get", f"{API_URL}/auth/me", expected_status_codes=401,
                            test_name="User: Get Own Profile (Unauthorized) - Expected Fail")

    # --- PROMPT TESTS ---
    print("\n--- Prompt Tests ---")

    # Test P1: Get all public prompts (using /prompts/)
    make_request_and_report("get", f"{API_URL}/prompts/", headers=primary_user_headers, expected_status_codes=200,
                            test_name="Prompt: Get All Public Prompts")

    # Test P2: Get own prompts (using /prompts/me/)
    make_request_and_report("get", f"{API_URL}/prompts/me/", headers=primary_user_headers, expected_status_codes=200,
                            test_name="Prompt: Get Own Prompts (via /prompts/me/)")

    # Test P3: Get specific own prompt by ID
    if PRIMARY_TEST_USER_PROMPT_ID:
        make_request_and_report("get", f"{API_URL}/prompts/{PRIMARY_TEST_USER_PROMPT_ID}", headers=primary_user_headers,
                                expected_status_codes=200, test_name="Prompt: Get Specific Own Prompt by ID")
    else:
        record_test_result("Prompt: Get Specific Own Prompt by ID", "N/A", "GET", "N/A", 200,
                           "Prerequisite (Primary User Prompt) not met.")

    # Test P4: Get another user's PUBLIC prompt by ID (using /prompts/{prompt_id})
    if SECONDARY_TEST_USER_PUBLIC_PROMPT_ID:
        make_request_and_report("get", f"{API_URL}/prompts/{SECONDARY_TEST_USER_PUBLIC_PROMPT_ID}",
                                headers=primary_user_headers, expected_status_codes=200,
                                test_name="Prompt: Get Another User's Public Prompt by ID")
    else:
        record_test_result("Prompt: Get Another User's Public Prompt by ID", "N/A", "GET", "N/A", 200,
                           "Prerequisite (Secondary Public Prompt) not met.")

    # Test P5: Attempt to get another user's PRIVATE prompt by ID (Negative)
    if SECONDARY_TEST_USER_PRIVATE_PROMPT_ID:
        make_request_and_report("get", f"{API_URL}/prompts/{SECONDARY_TEST_USER_PRIVATE_PROMPT_ID}",
                                headers=primary_user_headers, expected_status_codes=[403, 404],
                                test_name="Prompt: Attempt to Get Another User's Private Prompt - Expected Fail (403 or 404)")
    else:
        record_test_result("Prompt: Attempt to Get Another User's Private Prompt", "N/A", "GET", "N/A", [403, 404],
                           "Prerequisite (Secondary Private Prompt) not met.")

    # Test P6: Update own prompt
    if PRIMARY_TEST_USER_PROMPT_ID:
        update_prompt_data = {"content": "Updated content for my prompt.", "is_public": True}
        make_request_and_report("put", f"{API_URL}/prompts/{PRIMARY_TEST_USER_PROMPT_ID}", headers=primary_user_headers,
                                json_data=update_prompt_data, expected_status_codes=200,
                                test_name="Prompt: Update Own Prompt")
    else:
        record_test_result("Prompt: Update Own Prompt", "N/A", "PUT", "N/A", 200,
                           "Prerequisite (Primary User Prompt) not met.")

    # Test P7: Attempt to update another user's prompt (Negative)
    if SECONDARY_TEST_USER_PUBLIC_PROMPT_ID:
        malicious_update_data = {"content": "Hacked content!"}
        make_request_and_report("put", f"{API_URL}/prompts/{SECONDARY_TEST_USER_PUBLIC_PROMPT_ID}",
                                headers=primary_user_headers, json_data=malicious_update_data,
                                expected_status_codes=403,
                                test_name="Prompt: Attempt to Update Another User's Prompt - Expected Fail")
    else:
        record_test_result("Prompt: Attempt to Update Another User's Prompt", "N/A", "PUT", "N/A", 403,
                           "Prerequisite (Secondary Public Prompt) not met.")

    # --- PROMPT LIKING TESTS ---
    print("\n--- Prompt Liking Tests ---")

    # Test L1: Primary User Likes Secondary User's Public Prompt
    if SECONDARY_TEST_USER_PUBLIC_PROMPT_ID:
        make_request_and_report("post", f"{API_URL}/prompts/{SECONDARY_TEST_USER_PUBLIC_PROMPT_ID}/like",
                                headers=primary_user_headers, expected_status_codes=200,
                                test_name="Prompt Like: Primary User Likes Secondary's Public Prompt")
    else:
        record_test_result("Prompt Like: Primary User Likes Secondary's Public Prompt", "N/A", "POST", "N/A", 200,
                           "Prerequisite (Secondary Public Prompt) not met.")

    # Test L2: Primary User attempts to Like the same prompt again (Negative)
    if SECONDARY_TEST_USER_PUBLIC_PROMPT_ID:
        make_request_and_report("post", f"{API_URL}/prompts/{SECONDARY_TEST_USER_PUBLIC_PROMPT_ID}/like",
                                headers=primary_user_headers, expected_status_codes=[400, 409],
                                test_name="Prompt Like: Primary User Likes Same Prompt Again - Expected Fail (400 or 409)")
    else:
        record_test_result("Prompt Like: Primary User Likes Same Prompt Again", "N/A", "POST", "N/A", [400, 409],
                           "Prerequisite (Secondary Public Prompt) not met.")

    # Test L3: Third User Likes Secondary User's Public Prompt (multiple likes)
    if SECONDARY_TEST_USER_PUBLIC_PROMPT_ID:
        make_request_and_report("post", f"{API_URL}/prompts/{SECONDARY_TEST_USER_PUBLIC_PROMPT_ID}/like",
                                headers=third_user_headers, expected_status_codes=200,
                                test_name="Prompt Like: Third User Likes Secondary's Public Prompt")
    else:
        record_test_result("Prompt Like: Third User Likes Secondary's Public Prompt", "N/A", "POST", "N/A", 200,
                           "Prerequisite (Secondary Public Prompt) not met.")

    # Test L4: Primary User Unlikes Secondary User's Public Prompt (using DELETE)
    if SECONDARY_TEST_USER_PUBLIC_PROMPT_ID:
        make_request_and_report("delete", f"{API_URL}/prompts/{SECONDARY_TEST_USER_PUBLIC_PROMPT_ID}/unlike",
                                headers=primary_user_headers, expected_status_codes=204,
                                test_name="Prompt Like: Primary User Unlikes Secondary's Public Prompt")
    else:
        record_test_result("Prompt Like: Primary User Unlikes Secondary's Public Prompt", "N/A", "DELETE", "N/A", 204,
                           "Prerequisite (Secondary Public Prompt) not met.")

    # Test L5: Primary User attempts to Unlike the same prompt again (Negative)
    if SECONDARY_TEST_USER_PUBLIC_PROMPT_ID:
        make_request_and_report("delete", f"{API_URL}/prompts/{SECONDARY_TEST_USER_PUBLIC_PROMPT_ID}/unlike",
                                headers=primary_user_headers, expected_status_codes=[400, 404],
                                test_name="Prompt Like: Primary User Unlikes Same Prompt Again - Expected Fail (400 or 404 if no like to remove)")
    else:
        record_test_result("Prompt Like: Primary User Unlikes Same Prompt Again", "N/A", "DELETE", "N/A", [400, 404],
                           "Prerequisite (Secondary Public Prompt) not met.")

    # Test L6: Fetch publicly most liked prompts (using /prompts/most-liked/)
    make_request_and_report("get", f"{API_URL}/prompts/most-liked/", headers=primary_user_headers,
                            expected_status_codes=200, test_name="Prompt: Get Publicly Most Liked Prompts")

    # Test L7: Fetch user's own most liked prompts (as Primary User, using /prompts/favorites/)
    make_request_and_report("get", f"{API_URL}/prompts/favorites/", headers=primary_user_headers,
                            expected_status_codes=200, test_name="Prompt: Get Own Most Liked Prompts")

    # --- COMMENT TESTS ---
    print("\n--- Comment Tests ---")

    # Test C1: Get comments on own prompt
    if PRIMARY_TEST_USER_PROMPT_ID:
        make_request_and_report("get", f"{API_URL}/prompts/{PRIMARY_TEST_USER_PROMPT_ID}/comments",
                                headers=primary_user_headers, expected_status_codes=200,
                                test_name="Comment: Get Comments on Own Prompt")
    else:
        record_test_result("Comment: Get Comments on Own Prompt", "N/A", "GET", "N/A", 200,
                           "Prerequisite (Primary User Prompt) not met.")

    # Test C2: Update own comment (using /comments/{comment_id})
    if PRIMARY_TEST_USER_PROMPT_ID and PRIMARY_TEST_USER_COMMENT_ID:
        update_comment_data = {"content": "Updated comment content!"}
        make_request_and_report("put", f"{API_URL}/comments/{PRIMARY_TEST_USER_COMMENT_ID}",
                                headers=primary_user_headers, json_data=update_comment_data, expected_status_codes=200,
                                test_name="Comment: Update Own Comment")
    else:
        record_test_result("Comment: Update Own Comment", "N/A", "PUT", "N/A", 200,
                           "Prerequisite (Primary User Prompt/Comment) not met.")

    # Test C3: Attempt to comment on another user's public prompt (Positive)
    if SECONDARY_TEST_USER_PUBLIC_PROMPT_ID:
        make_request_and_report("post", f"{API_URL}/prompts/{SECONDARY_TEST_USER_PUBLIC_PROMPT_ID}/comments",
                                headers=primary_user_headers,
                                json_data=generate_comment_data(content_prefix="Primary commenting on Secondary's"),
                                expected_status_codes=201, test_name="Comment: Comment on Another User's Public Prompt")
    else:
        record_test_result("Comment: Comment on Another User's Public Prompt", "N/A", "POST", "N/A", 201,
                           "Prerequisite (Secondary Public Prompt) not met.")

    # Test C4: Attempt to update a comment on another user's prompt that was *not* authored by self (Negative)
    # This scenario needs a comment made by Secondary on Primary's prompt, then Primary tries to update it.
    secondary_comment_on_primary_prompt_id = None
    if PRIMARY_TEST_USER_PROMPT_ID and SECONDARY_TEST_USER_DATA.get("token"):
        secondary_comment_on_primary_prompt_id = create_comment(SECONDARY_TEST_USER_DATA["token"],
                                                                PRIMARY_TEST_USER_PROMPT_ID, generate_comment_data(
                content_prefix="Secondary's comment on Primary's prompt"))
        if secondary_comment_on_primary_prompt_id:
            malicious_comment_update = {"content": "Malicious edit!"}
            make_request_and_report("put", f"{API_URL}/comments/{secondary_comment_on_primary_prompt_id}",
                                    headers=primary_user_headers, json_data=malicious_comment_update,
                                    expected_status_codes=403,
                                    test_name="Comment: Attempt to Update Another User's Comment - Expected Fail")
        else:
            record_test_result("Comment: Attempt to Update Another User's Comment", "N/A", "PUT", "N/A", 403,
                               "Failed to create prerequisite comment for this test.")
    else:
        record_test_result("Comment: Attempt to Update Another User's Comment", "N/A", "PUT", "N/A", 403,
                           "Prerequisites (Primary Prompt / Secondary Token) not met.")

    # --- ADMIN FUNCTIONALITIES AS NORMAL USER (NEGATIVE TESTS) ---
    print("\n--- Admin Functionalities as Normal User (Negative Tests) ---")

    # Test A1: Normal User attempts to list all users via admin endpoint
    make_request_and_report("get", f"{API_URL}/admin/", headers=primary_user_headers, expected_status_codes=403,
                            test_name="Normal User: Access Admin Get All Users - Expected Fail")

    # Test A2: Normal User attempts to promote a user to admin
    # Use a dummy user ID since we don't have a real one for this negative test
    dummy_user_id_for_admin_test = 999999
    make_request_and_report("post", f"{API_URL}/admin/add_admin/{dummy_user_id_for_admin_test}",
                            headers=primary_user_headers, expected_status_codes=403,
                            test_name="Normal User: Promote User to Admin - Expected Fail")

    # Test A3: Normal User attempts to soft-delete a prompt via admin endpoint
    # Use the secondary user's public prompt ID for this
    if SECONDARY_TEST_USER_PUBLIC_PROMPT_ID:
        make_request_and_report("put", f"{API_URL}/admin/{SECONDARY_TEST_USER_PUBLIC_PROMPT_ID}/soft-delete",
                                headers=primary_user_headers, expected_status_codes=403,
                                test_name="Normal User: Soft-Delete Prompt via Admin Endpoint - Expected Fail")
    else:
        record_test_result("Normal User: Soft-Delete Prompt via Admin Endpoint", "N/A", "PUT", "N/A", 403,
                           "Prerequisite (Secondary Public Prompt) not met.")

    # Test A4: Normal User attempts to delete a user via admin endpoint
    # Use the secondary user's ID for this
    if SECONDARY_TEST_USER_DATA.get("id"):
        make_request_and_report("delete", f"{API_URL}/admin/{SECONDARY_TEST_USER_DATA['id']}",
                                headers=primary_user_headers, expected_status_codes=403,
                                test_name="Normal User: Delete User via Admin Endpoint - Expected Fail")
    else:
        record_test_result("Normal User: Delete User via Admin Endpoint", "N/A", "DELETE", "N/A", 403,
                           "Prerequisite (Secondary User) not met.")

    # --- DELETION TESTS (as Primary User) ---
    print("\n--- Deletion Tests ---")

    # Test D1: Delete own comment (using /comments/{comment_id})
    if PRIMARY_TEST_USER_PROMPT_ID and PRIMARY_TEST_USER_COMMENT_ID:
        make_request_and_report("delete", f"{API_URL}/comments/{PRIMARY_TEST_USER_COMMENT_ID}",
                                headers=primary_user_headers, expected_status_codes=204,
                                test_name="Comment: Delete Own Comment")
    else:
        record_test_result("Comment: Delete Own Comment", "N/A", "DELETE", "N/A", 204,
                           "Prerequisite (Primary User Prompt/Comment) not met.")

    # Test D2: Delete own prompt (using /prompts/{prompt_id})
    if PRIMARY_TEST_USER_PROMPT_ID:
        make_request_and_report("delete", f"{API_URL}/prompts/{PRIMARY_TEST_USER_PROMPT_ID}",
                                headers=primary_user_headers, expected_status_codes=204,
                                test_name="Prompt: Delete Own Prompt")
    else:
        record_test_result("Prompt: Delete Own Prompt", "N/A", "DELETE", "N/A", 204,
                           "Prerequisite (Primary User Prompt) not met.")

    # Test D3: Attempt to delete another user's prompt (Negative)
    if SECONDARY_TEST_USER_PUBLIC_PROMPT_ID:
        make_request_and_report("delete", f"{API_URL}/prompts/{SECONDARY_TEST_USER_PUBLIC_PROMPT_ID}",
                                headers=primary_user_headers, expected_status_codes=403,
                                test_name="Prompt: Attempt to Delete Another User's Prompt - Expected Fail")
    else:
        record_test_result("Prompt: Attempt to Delete Another User's Prompt", "N/A", "DELETE", "N/A", 403,
                           "Prerequisite (Secondary Public Prompt) not met.")

    # Test D4: Delete own user account (should be last test for the primary user)
    # Using /users/{user_id} with their own ID
    make_request_and_report("delete", f"{API_URL}/users/{PRIMARY_TEST_USER_DATA['id']}", headers=primary_user_headers,
                            expected_status_codes=204, test_name="User: Delete Own Account")

    # Final Check: Attempt to login with deleted user (Negative)
    make_request_and_report("post", f"{API_URL}/auth/token", data={"username": PRIMARY_TEST_USER_DATA['username'],
                                                                   "password": PRIMARY_TEST_USER_DATA['password']},
                            expected_status_codes=400, test_name="User: Login After Deletion - Expected Fail")

    # --- Phase 3: Cleanup (All Remaining Dynamically Created Users) ---
    print("\n## Phase 3: Cleaning up all dynamically created test data...")

    # Iterate through all created user IDs and delete them if they still exist
    # Note: Primary user is already deleted in D4.
    all_test_users_data = {
        PRIMARY_TEST_USER_DATA.get("id"): PRIMARY_TEST_USER_DATA,
        SECONDARY_TEST_USER_DATA.get("id"): SECONDARY_TEST_USER_DATA,
        THIRD_TEST_USER_DATA.get("id"): THIRD_TEST_USER_DATA
    }

    for user_id_to_delete in CREATED_USER_IDS:
        # If the user has already been successfully deleted, their data might not have a token
        current_user_data = all_test_users_data.get(user_id_to_delete)

        if current_user_data and current_user_data.get("token"):
            # Attempt to delete the user using their own token
            cleanup_headers = {"Authorization": f"Bearer {current_user_data['token']}"}
            make_request_and_report("delete", f"{API_URL}/users/{user_id_to_delete}", headers=cleanup_headers,
                                    expected_status_codes=[204, 404],
                                    test_name=f"Cleanup: Delete User ID {user_id_to_delete} ({current_user_data['username']})")
        else:
            print(
                f"Skipping direct cleanup for User ID {user_id_to_delete}: User's token not available or already handled (e.g., primary user already deleted).")
            # If a user's account could not be deleted by itself, it might need admin intervention
            # (which is outside the scope of a 'normal user' test script).

    # Attempt to delete any remaining prompts if they somehow weren't deleted with their owner
    if SECONDARY_TEST_USER_PUBLIC_PROMPT_ID and SECONDARY_TEST_USER_DATA.get("token"):
        make_request_and_report("delete", f"{API_URL}/prompts/{SECONDARY_TEST_USER_PUBLIC_PROMPT_ID}",
                                headers={"Authorization": f"Bearer {SECONDARY_TEST_USER_DATA['token']}"},
                                expected_status_codes=[204, 403, 404],
                                test_name="Cleanup: Delete Secondary User's Public Prompt")
    if SECONDARY_TEST_USER_PRIVATE_PROMPT_ID and SECONDARY_TEST_USER_DATA.get("token"):
        make_request_and_report("delete", f"{API_URL}/prompts/{SECONDARY_TEST_USER_PRIVATE_PROMPT_ID}",
                                headers={"Authorization": f"Bearer {SECONDARY_TEST_USER_DATA['token']}"},
                                expected_status_codes=[204, 403, 404],
                                test_name="Cleanup: Delete Secondary User's Private Prompt")
    if secondary_comment_on_primary_prompt_id and SECONDARY_TEST_USER_DATA.get("token"):
        make_request_and_report("delete", f"{API_URL}/comments/{secondary_comment_on_primary_prompt_id}",
                                headers={"Authorization": f"Bearer {SECONDARY_TEST_USER_DATA['token']}"},
                                expected_status_codes=[204, 403, 404],
                                test_name="Cleanup: Delete Secondary's Comment on Primary's Prompt")

    print_final_report()