"""
Test Procedure: TP-07-004
Test Case:      TC-07-005
Feature:        F007 – User Management
Covered:        TCOV-07-008, TCOV-07-009
Title:          Verify that admin can update a user's status and permanently
                remove a user from the system.

Intercase Dependency: TC-07-002

Test Steps:
    TC-07-005-A  Status change "Pending" → "Verified":
                 Inline "Verify" button updates the status badge in the table;
                 no dialog is shown — the list refreshes silently.

    TC-07-005-B  Delete user:
                 Trash icon opens a confirmation dialog ("Delete User" /
                 "This action cannot be undone." / "⚠️ This action is
                 irreversible"), clicking "Delete" triggers a success dialog
                 ("User deleted successfully."), and the user no longer
                 appears in the list after dismissal.

Setup strategy:
    Two dedicated test users are created via the invite API in setUpClass;
    both receive status "Pending" by default (as per backend logic).
    tearDownClass cleans up the status-change user if it still exists
    (i.e. TC-07-005-A passed but no teardown happened).
    The delete-target user is removed by TC-07-005-B itself.
"""

import time
import unittest
from datetime import datetime

import requests as http
from html_runner import make_runner
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ── Configuration ─────────────────────────────────────────────────────────────
BASE_URL = "http://localhost:3000"
API_URL  = "http://localhost:4000"

ADMIN_EMAIL    = "admin1@drone4dengue.com"
ADMIN_PASSWORD = "adminpass1"

TS = datetime.now().strftime("%H%M%S")

# User created in setUpClass for TC-07-005-A (status change)
STATUS_USER_EMAIL = f"pending.status.{TS}@test.com"

# User created in setUpClass for TC-07-005-B (deletion)
DELETE_USER_EMAIL = f"ali.delete.{TS}@test.com"

TIMEOUT = 15


# ── Helpers ───────────────────────────────────────────────────────────────────
def build_driver() -> webdriver.Chrome:
    opts = Options()
    # opts.add_argument("--headless=new")   # uncomment for CI
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1440,900")
    return webdriver.Chrome(options=opts)


def login(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    driver.get(BASE_URL)
    wait.until(EC.visibility_of_element_located((By.ID, "email"))).send_keys(ADMIN_EMAIL)
    driver.find_element(By.ID, "password").send_keys(ADMIN_PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    wait.until(EC.url_contains("/dashboard"))


def go_to_user_management(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    driver.get(f"{BASE_URL}/user-management")
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//h1[contains(text(), 'User Management')]")
        )
    )
    wait.until(
        EC.invisibility_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Loading users...')]")
        )
    )


def get_browser_token(driver: webdriver.Chrome) -> str:
    token = driver.execute_script("return localStorage.getItem('token');")
    if not token:
        raise RuntimeError("No auth token in localStorage")
    return token


def api_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def invite_user(token: str, email: str, company_id: str) -> dict:
    """Create a test user via the invite API (status will be 'Pending')."""
    res = http.post(
        f"{API_URL}/users/invite",
        headers=api_headers(token),
        json={"email": email, "role": "user", "companyId": company_id},
    )
    res.raise_for_status()
    return res.json()


def get_user_by_email(token: str, email: str) -> dict | None:
    """Return user dict for the given email, or None if not found."""
    res = http.get(
        f"{API_URL}/users",
        headers=api_headers(token),
        params={"search": email, "limit": "10"},
    )
    res.raise_for_status()
    matches = [u for u in res.json().get("users", []) if u["email"] == email]
    return matches[0] if matches else None


def delete_user_via_api(token: str, user_id: str) -> None:
    http.delete(f"{API_URL}/users/{user_id}", headers=api_headers(token))


def get_company_id(token: str) -> str:
    """Retrieve the companyId of the logged-in admin from the API."""
    res = http.get(f"{API_URL}/users", headers=api_headers(token), params={"limit": "1"})
    res.raise_for_status()
    # The API middleware attaches companyId to the token; read it from
    # the summary endpoint which is scoped to the same company.
    summary = http.get(f"{API_URL}/users/summary/dashboard", headers=api_headers(token))
    summary.raise_for_status()
    # Fall back to looking up admin1 directly
    admin = get_user_by_email(token, ADMIN_EMAIL)
    return admin["companyId"] if admin else ""


def search_for_user(driver: webdriver.Chrome, wait: WebDriverWait, email: str) -> None:
    """Type into the search box and wait for the list to filter."""
    search = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//input[@placeholder='Search users...']")
        )
    )
    search.clear()
    search.send_keys(email)
    time.sleep(1)  # allow search debounce / re-render


# ── Test Class ────────────────────────────────────────────────────────────────
class TC07005UserStatusDelete(unittest.TestCase):
    """TC-07-005 – Update user status (Pending → Verified) and delete user."""

    @classmethod
    def setUpClass(cls):
        cls.driver = build_driver()
        cls.wait   = WebDriverWait(cls.driver, TIMEOUT)
        login(cls.driver, cls.wait)

        cls.token      = get_browser_token(cls.driver)
        cls.company_id = get_company_id(cls.token)

        # Create both test users (status will be 'Pending')
        invite_user(cls.token, STATUS_USER_EMAIL, cls.company_id)
        invite_user(cls.token, DELETE_USER_EMAIL, cls.company_id)

    @classmethod
    def tearDownClass(cls):
        # Clean up the status-change user if it still exists
        user = get_user_by_email(cls.token, STATUS_USER_EMAIL)
        if user:
            delete_user_via_api(cls.token, user["id"])
        cls.driver.quit()

    def setUp(self):
        go_to_user_management(self.driver, self.wait)

    # ── TC-07-005-A ──────────────────────────────────────────────────────────
    def test_A_pending_status_updated_to_verified(self):
        """
        TC-07-005-A
        Input:    Status change "Pending" → "Verified" for STATUS_USER_EMAIL.
        Expected: Status indicator updates to "Verified" in the user list.
                  No dialog is shown — the list refreshes silently after
                  clicking the inline "Verify" button.
        Special Procedural Requirements: User must have "Pending" status.
        """
        search_for_user(self.driver, self.wait, STATUS_USER_EMAIL)

        # ── Precondition: user row is visible with "Pending" status ──────────
        target_row = self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH,
                 f"//tr[.//td[.//*[contains(text(), '{STATUS_USER_EMAIL}')]]]")
            )
        )
        pending_badge = target_row.find_element(
            By.XPATH, ".//span[contains(@class,'text-yellow-800') and "
                      "contains(normalize-space(text()), 'Pending')]"
        )
        self.assertTrue(
            pending_badge.is_displayed(),
            f"Pre-condition failed: '{STATUS_USER_EMAIL}' should have status 'Pending'"
        )

        # ── Action: click the inline "Verify" button ─────────────────────────
        verify_btn = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH,
                 f"//tr[.//td[.//*[contains(text(), '{STATUS_USER_EMAIL}')]]]"
                 f"//button[@title='Verify User']")
            )
        )
        verify_btn.click()

        # ── Expected: "Verified" green badge appears; "Verify" button gone ───
        # No dialog is shown — status updates inline; wait for the green badge
        verified_badge = self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH,
                 f"//tr[.//td[.//*[contains(text(), '{STATUS_USER_EMAIL}')]]]"
                 f"//span[contains(@class,'text-green-600') and "
                 f"contains(normalize-space(text()), 'Verified')]")
            )
        )
        self.assertTrue(
            verified_badge.is_displayed(),
            "Status badge did not update to 'Verified' after clicking Verify"
        )

        # The "Verify" button must be gone (only shown for Pending users)
        remaining_verify_btns = self.driver.find_elements(
            By.XPATH,
            f"//tr[.//td[.//*[contains(text(), '{STATUS_USER_EMAIL}')]]]"
            f"//button[@title='Verify User']"
        )
        self.assertEqual(
            len(remaining_verify_btns), 0,
            "Inline 'Verify' button should disappear after status is set to Verified"
        )

        print(f"\n[PASS] TC-07-005-A: '{STATUS_USER_EMAIL}' status updated "
              f"Pending → Verified.")

    # ── TC-07-005-B ──────────────────────────────────────────────────────────
    def test_B_delete_user_removed_from_list(self):
        """
        TC-07-005-B
        Input:    Admin clicks delete on DELETE_USER_EMAIL.
        Expected: Confirmation dialog appears → admin confirms → success dialog
                  "User deleted successfully." → user no longer appears in the
                  user list.
        """
        search_for_user(self.driver, self.wait, DELETE_USER_EMAIL)

        # ── Confirm user exists before deletion ──────────────────────────────
        target_row = self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH,
                 f"//tr[.//td[.//*[contains(text(), '{DELETE_USER_EMAIL}')]]]")
            )
        )

        # ── Action: click the trash (delete) icon — second SVG button ────────
        delete_btn = target_row.find_element(
            By.XPATH, ".//button[.//*[name()='svg']][2]"
        )
        delete_btn.click()

        # ── Confirmation dialog must appear ───────────────────────────────────
        confirm_title = self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//h2[contains(text(), 'Delete User')]")
            )
        )
        self.assertTrue(confirm_title.is_displayed(), "'Delete User' dialog title not shown")

        confirm_msg = self.driver.find_element(
            By.XPATH,
            "//*[contains(text(), 'Are you sure you want to delete this user?')]"
        )
        self.assertTrue(
            confirm_msg.is_displayed(),
            "Confirmation message not visible in delete dialog"
        )

        irreversible_warning = self.driver.find_element(
            By.XPATH, "//*[contains(text(), 'This action is irreversible')]"
        )
        self.assertTrue(
            irreversible_warning.is_displayed(),
            "'This action is irreversible' warning not shown"
        )

        # ── Grab backdrop reference for staleness check ───────────────────────
        # (AnimatePresence removes the element from DOM after exit animation;
        #  staleness_of is more reliable than invisibility_of for Framer Motion)
        confirm_backdrop = self.driver.find_element(
            By.XPATH,
            "//div[contains(@class,'fixed') and contains(@class,'inset-0') "
            "and contains(@class,'backdrop-blur-sm')]"
        )

        # ── Action: click "Delete" to confirm ────────────────────────────────
        delete_confirm_btn = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[normalize-space(text())='Delete']")
            )
        )
        delete_confirm_btn.click()

        # Confirmation dialog must close
        self.wait.until(EC.staleness_of(confirm_backdrop))

        # ── Success dialog must appear ────────────────────────────────────────
        success_msg = self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//*[contains(text(), 'User deleted successfully')]")
            )
        )
        self.assertTrue(
            success_msg.is_displayed(),
            "'User deleted successfully.' success dialog not shown"
        )

        # Grab backdrop for success dialog staleness check
        success_backdrop = self.driver.find_element(
            By.XPATH,
            "//div[contains(@class,'fixed') and contains(@class,'inset-0') "
            "and contains(@class,'z-[100]')]"
        )

        # Dismiss success dialog
        great_btn = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[normalize-space(text())='Great!']")
            )
        )
        great_btn.click()

        # Wait for success dialog to be fully removed from DOM
        self.wait.until(EC.staleness_of(success_backdrop))

        # ── Verify: deleted user no longer appears in the list ────────────────
        search_for_user(self.driver, self.wait, DELETE_USER_EMAIL)

        remaining_rows = self.driver.find_elements(
            By.XPATH,
            f"//tr[.//td[.//*[contains(text(), '{DELETE_USER_EMAIL}')]]]"
        )
        self.assertEqual(
            len(remaining_rows), 0,
            f"Deleted user '{DELETE_USER_EMAIL}' still appears in the user list"
        )

        print(f"\n[PASS] TC-07-005-B: '{DELETE_USER_EMAIL}' deleted and removed "
              f"from user list.")


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromTestCase(TC07005UserStatusDelete)

    runner = make_runner(
        report_name="TC-07-005-UserStatusDelete",
        report_title="TP-07-004 | User Status & Delete Test Report",
    )
    runner.run(suite)
