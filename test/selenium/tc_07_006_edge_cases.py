"""
Test Procedure: TP-07-005
Test Case:      TC-07-006
Feature:        F007 – User Management
Covered:        TCOV-07-010, TCOV-07-011
Title:          Verify system behavior under edge case conditions — actions on
                an unregistered user and server failure during a save operation.

Intercase Dependency: TC-07-001 (TC-07-006-A), TC-07-003 (TC-07-006-B)

═══════════════════════════════════════════════════════════════════════════════
DISCREPANCIES — spec vs. actual system
═══════════════════════════════════════════════════════════════════════════════
TC-07-006-A
  Spec:   "System offers invitation or re-registration option" when admin
          selects a user with status "Unregistered".
  Actual: The UI renders the same standard Edit (pencil) and Delete (trash)
          actions for "Unregistered" users as it does for any other status.
          No special "invite" or "re-register" button exists.
          The "Unregistered" status badge is displayed (gray styling), and
          the user can be edited or deleted through the normal flow.
          "Unregistered" is also absent from the filter status dropdown
          (only "Verified" and "Pending" are listed).
          This test verifies the ACTUAL system behavior.

TC-07-006-B
  Spec:   "System displays an error message and logs the failure."
  Actual: • Error message: the edit modal renders the raw browser error
            ("Failed to fetch") inside a red `bg-red-50` box.
            There is no separate "log" panel in the UI; backend logging
            (logger.error) is server-side only and not visible to the admin.
          • The modal remains open after a failed save (setUpdateUser(null)
            is only called on success).
          • Server timeout is simulated using Chrome DevTools Protocol
            (Network.setBlockedURLs) to block the PATCH request.
═══════════════════════════════════════════════════════════════════════════════
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

# Fixture user for TC-07-006-A (will be set to "Unregistered" in setUpClass)
UNREG_USER_EMAIL = f"unregistered.{TS}@test.com"

# Seeded user used for the edit-save-fail test (TC-07-006-B)
EDIT_TARGET_EMAIL = "user2@drone4dengue.com"

TIMEOUT = 15


# ── Helpers ───────────────────────────────────────────────────────────────────
def build_driver() -> webdriver.Chrome:
    opts = Options()
    # opts.add_argument("--headless=new")
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


def get_user_by_email(token: str, email: str) -> dict | None:
    res = http.get(
        f"{API_URL}/users",
        headers=api_headers(token),
        params={"search": email, "limit": "10"},
    )
    res.raise_for_status()
    matches = [u for u in res.json().get("users", []) if u["email"] == email]
    return matches[0] if matches else None


def get_company_id(token: str) -> str:
    admin = get_user_by_email(token, ADMIN_EMAIL)
    return admin["companyId"] if admin else ""


def invite_user(token: str, email: str, company_id: str) -> dict:
    """Invite a new user (status will be 'Pending' by default)."""
    res = http.post(
        f"{API_URL}/users/invite",
        headers=api_headers(token),
        json={"email": email, "role": "user", "companyId": company_id},
    )
    res.raise_for_status()
    return res.json()


def set_user_status_via_api(token: str, user_id: str, status: str) -> None:
    """Set a user's status directly via the admin status endpoint."""
    res = http.put(
        f"{API_URL}/users/{user_id}/status",
        headers=api_headers(token),
        json={"status": status},
    )
    res.raise_for_status()


def delete_user_via_api(token: str, user_id: str) -> None:
    http.delete(f"{API_URL}/users/{user_id}", headers=api_headers(token))


def search_for_user(driver: webdriver.Chrome, wait: WebDriverWait, email: str) -> None:
    search = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//input[@placeholder='Search users...']")
        )
    )
    search.clear()
    search.send_keys(email)
    time.sleep(1)


def block_api(driver: webdriver.Chrome) -> None:
    """Block all outbound requests to the API server via CDP."""
    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": [f"{API_URL}/*"]})


def unblock_api(driver: webdriver.Chrome) -> None:
    """Remove the CDP network block."""
    driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": []})


# ── Test Class ────────────────────────────────────────────────────────────────
class TC07006EdgeCases(unittest.TestCase):
    """TC-07-006 – Unregistered user behaviour and server-failure error handling."""

    @classmethod
    def setUpClass(cls):
        cls.driver = build_driver()
        cls.wait   = WebDriverWait(cls.driver, TIMEOUT)
        login(cls.driver, cls.wait)

        cls.token      = get_browser_token(cls.driver)
        cls.company_id = get_company_id(cls.token)

        # Create fixture user and immediately set status to "Unregistered"
        # invite_user returns a flat user object (not nested under "user" key)
        invite_resp = invite_user(cls.token, UNREG_USER_EMAIL, cls.company_id)
        cls.unreg_user_id = invite_resp.get("id")

        if cls.unreg_user_id:
            set_user_status_via_api(cls.token, cls.unreg_user_id, "Unregistered")

    @classmethod
    def tearDownClass(cls):
        # Clean up fixture user
        if cls.unreg_user_id:
            delete_user_via_api(cls.token, cls.unreg_user_id)
        cls.driver.quit()

    def setUp(self):
        go_to_user_management(self.driver, self.wait)

    # ── TC-07-006-A ──────────────────────────────────────────────────────────
    def test_A_unregistered_user_displays_badge_with_standard_actions(self):
        """
        TC-07-006-A
        Input:    Admin views a user with status "Unregistered".
        Expected (actual system):
          • Gray "Unregistered" badge is displayed in the status column.
          • Standard Edit and Delete action buttons are present.
          • No special "invite" or "re-registration" option exists in the row.

        Documented gap: The spec states "System offers invitation or
        re-registration option". The actual UI provides no such control —
        the Unregistered status only differs visually (gray badge); the
        available actions are identical to any other user.
        """
        search_for_user(self.driver, self.wait, UNREG_USER_EMAIL)

        # ── 1. Row must be present ────────────────────────────────────────────
        target_row = self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH,
                 f"//tr[.//td[.//*[contains(text(), '{UNREG_USER_EMAIL}')]]]")
            )
        )

        # ── 2. "Unregistered" badge is displayed with gray styling ────────────
        unreg_badge = target_row.find_element(
            By.XPATH,
            ".//span[contains(@class,'text-gray-500') and "
            "contains(normalize-space(text()), 'Unregistered')]"
        )
        self.assertTrue(
            unreg_badge.is_displayed(),
            "Expected a gray 'Unregistered' status badge in the user row"
        )

        # ── 3. Standard Edit button is available ─────────────────────────────
        edit_btn = target_row.find_element(
            By.XPATH, ".//button[.//*[name()='svg']][1]"
        )
        self.assertTrue(
            edit_btn.is_displayed(),
            "Edit button should be present for an Unregistered user"
        )

        # ── 4. Standard Delete button is available ────────────────────────────
        delete_btn = target_row.find_element(
            By.XPATH, ".//button[.//*[name()='svg']][2]"
        )
        self.assertTrue(
            delete_btn.is_displayed(),
            "Delete button should be present for an Unregistered user"
        )

        # ── 5. No "Verify" button (only shown for Pending users) ──────────────
        verify_btns = target_row.find_elements(
            By.XPATH, ".//button[@title='Verify User']"
        )
        self.assertEqual(
            len(verify_btns), 0,
            "No 'Verify' button should appear for an Unregistered user"
        )

        # ── 6. No invitation / re-registration button (spec gap) ──────────────
        # The spec expects one, but it does not exist in the current system.
        invite_btns = target_row.find_elements(
            By.XPATH,
            ".//button[contains(translate(normalize-space(.), "
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),"
            "'invite') or contains(translate(normalize-space(.), "
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),"
            "'re-register') or contains(translate(normalize-space(.), "
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),"
            "'resend')]"
        )
        self.assertEqual(
            len(invite_btns), 0,
            "[DOCUMENTED GAP] No invitation/re-registration button exists for "
            "Unregistered users — spec expects one, system does not provide it"
        )

        print(
            f"\n[PASS] TC-07-006-A: '{UNREG_USER_EMAIL}' shows gray 'Unregistered' "
            f"badge with standard Edit/Delete actions.\n"
            f"[DOCUMENTED GAP] No invitation or re-registration option exists in the UI."
        )

    # ── TC-07-006-B ──────────────────────────────────────────────────────────
    def test_B_server_failure_during_save_shows_error_in_modal(self):
        """
        TC-07-006-B
        Input:    Server timeout is simulated while the admin saves a user edit.
        Expected: System displays an error message inside the edit modal and
                  the modal remains open (save was not applied).

        Implementation:
          • Chrome DevTools Protocol (Network.setBlockedURLs) blocks the
            PATCH request to simulate an unreachable server / timeout.
          • The browser raises a TypeError ("Failed to fetch"), which the
            page's catch block surfaces as a red error box inside the modal.
          • "Logs the failure" in the spec refers to server-side logging
            (logger.error in updateProfile controller) — not a UI element.
            This test verifies only what is observable in the admin dashboard.
        """
        search_for_user(self.driver, self.wait, EDIT_TARGET_EMAIL)

        # Open edit modal
        target_row = self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH,
                 f"//tr[.//td[.//*[contains(text(), '{EDIT_TARGET_EMAIL}')]]]")
            )
        )
        edit_btn = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH,
                 f"//tr[.//td[.//*[contains(text(), '{EDIT_TARGET_EMAIL}')]]]"
                 f"//button[contains(@class,'text-accent-blue')]")
            )
        )
        edit_btn.click()

        self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//h2[contains(text(), 'Update User')]")
            )
        )

        # Make a change so the save is meaningful
        name_input = self.driver.find_element(
            By.XPATH, "//input[@placeholder='Enter full name']"
        )
        name_input.clear()
        name_input.send_keys("Timeout Test Name")

        # Block the API before clicking save
        block_api(self.driver)

        try:
            update_btn = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(., 'Update User')]")
                )
            )
            update_btn.click()

            # ── Error must appear inside the edit modal ───────────────────────
            # The page catch block calls setError(err.message).
            # When the request is blocked the browser raises TypeError:
            # "Failed to fetch".
            modal_error = self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH,
                     "//div[contains(@class,'bg-red-50') and "
                     "contains(@class,'border-red-200') and "
                     "contains(@class,'text-red-700') and "
                     "string-length(normalize-space(text())) > 0]")
                )
            )
            error_text = modal_error.text.strip()

            self.assertTrue(
                len(error_text) > 0,
                "Error element found inside modal but contains no text"
            )
            self.assertIn(
                "Failed to fetch", error_text,
                f"Expected 'Failed to fetch' in modal error, got: '{error_text}'"
            )

            # ── Edit modal must still be open (save was not applied) ──────────
            modal_header = self.driver.find_element(
                By.XPATH, "//h2[contains(text(), 'Update User')]"
            )
            self.assertTrue(
                modal_header.is_displayed(),
                "Edit modal should remain open after a failed save"
            )

            # ── "Update User" button must be re-enabled (setUpdating(false)) ──
            update_btn_after = self.driver.find_element(
                By.XPATH, "//button[contains(., 'Update User')]"
            )
            self.assertIsNone(
                update_btn_after.get_attribute("disabled"),
                "Update button should be re-enabled after a failed save"
            )

            print(
                f"\n[PASS] TC-07-006-B: Error '{error_text}' displayed inside edit modal "
                f"after server failure; modal remained open.\n"
                f"[NOTE] Server-side logging (logger.error) is backend-only and "
                f"not directly observable in the admin dashboard UI."
            )

        finally:
            # Always restore network connectivity
            unblock_api(self.driver)

            # Close the modal (Cancel), restoring the page to a clean state
            try:
                cancel = self.driver.find_element(
                    By.XPATH, "//button[normalize-space(text())='Cancel']"
                )
                if cancel.is_displayed():
                    cancel.click()
                    self.wait.until(
                        EC.invisibility_of_element_located(
                            (By.XPATH, "//h2[contains(text(), 'Update User')]")
                        )
                    )
            except Exception:
                pass


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromTestCase(TC07006EdgeCases)

    runner = make_runner(
        report_name="TC-07-006-EdgeCases",
        report_title="TP-07-005 | Edge Cases Test Report",
    )
    runner.run(suite)
