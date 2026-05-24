"""
Test Procedure: TP-07-002
Test Cases:     TC-07-002, TC-07-003
Feature:        F007 – User Management
Title:          Verify admin can add a new user with valid input, system rejects
                submissions with missing/invalid required fields, and an existing
                user's information can be edited successfully.

Intercase Dependency: TC-07-001 (admin must be logged in)

Test Steps Covered:
    TC-07-002-A  Valid input (email + role) → new user appears in the user list
    TC-07-002-B  Empty email → "Create User" button is disabled (cannot submit)
    TC-07-002-C  Invalid email format → inline error "Please enter a valid email address"
    TC-07-003    Edit existing user (name, phone, address) → updated values in table

Implementation Notes:
    • The Add User modal has no Name field. The system auto-generates the display
      name from the email prefix (e.g. "ali@test.com" → name "ali").
      The test case document lists Name as an input; the actual form does not.
    • A timestamp suffix is appended to the test email so the test can be re-run
      without hitting the "Email already registered" conflict.
    • TC-07-003 targets a seeded user to remain independent of TC-07-002.
"""

import time
import unittest
from datetime import datetime

from html_runner import make_runner
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ── Configuration ─────────────────────────────────────────────────────────────
BASE_URL = "http://localhost:3000"
API_URL  = "http://localhost:4000"

ADMIN_EMAIL    = "admin1@drone4dengue.com"
ADMIN_PASSWORD = "adminpass1"

# Unique email per run to avoid "Email already registered" on repeat runs
TS         = datetime.now().strftime("%H%M%S")
TEST_EMAIL = f"ali.test.{TS}@test.com"
# Name the system will auto-assign (email prefix)
EXPECTED_NAME = TEST_EMAIL.split("@")[0]

# Seeded user to edit in TC-07-003
EDIT_TARGET_EMAIL = "user1@drone4dengue.com"

TIMEOUT = 15


# ── Driver / helpers ──────────────────────────────────────────────────────────
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
    # Wait for any initial loading spinner to clear
    wait.until(
        EC.invisibility_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Loading users...')]")
        )
    )


def open_add_user_modal(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    """Click 'Add New User' and wait for the modal to appear."""
    driver.find_element(
        By.XPATH, "//button[contains(., 'Add New User')]"
    ).click()
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//h2[contains(text(), 'Add New User')]")
        )
    )


def close_modal_if_open(driver: webdriver.Chrome) -> None:
    """Dismiss any open modal by clicking its Cancel button (best-effort)."""
    try:
        cancel = driver.find_element(
            By.XPATH, "//button[normalize-space(text())='Cancel']"
        )
        if cancel.is_displayed():
            cancel.click()
            time.sleep(0.5)
    except Exception:
        pass


# ── Test Class ────────────────────────────────────────────────────────────────
class TC07002003UserAddEdit(unittest.TestCase):
    """TC-07-002 / TC-07-003 – Add user (valid & invalid) and edit user."""

    @classmethod
    def setUpClass(cls):
        cls.driver = build_driver()
        cls.wait   = WebDriverWait(cls.driver, TIMEOUT)
        login(cls.driver, cls.wait)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def setUp(self):
        """Navigate to User Management before each sub-test."""
        go_to_user_management(self.driver, self.wait)

    # ── TC-07-002-A ──────────────────────────────────────────────────────────
    def test_A_add_user_valid_input_appears_in_list(self):
        """
        TC-07-002-A
        Input:    Email: TEST_EMAIL, Role: "user" (Normal User)
        Expected: New user appears in the user list after creation.
        Note:     The Add User form has no Name field; the system derives the
                  display name from the email prefix automatically.
        """
        open_add_user_modal(self.driver, self.wait)

        # Fill email
        email_input = self.driver.find_element(
            By.XPATH, "//input[@placeholder='Enter email address']"
        )
        email_input.clear()
        email_input.send_keys(TEST_EMAIL)

        # Role defaults to "user"; verify it is selected
        role_select = self.driver.find_element(
            By.XPATH, "//select[option[@value='user'] and option[@value='admin']]"
        )
        self.assertEqual(
            role_select.get_attribute("value"), "user",
            "Role dropdown should default to 'user'"
        )

        # Submit
        submit_btn = self.driver.find_element(
            By.XPATH, "//button[contains(., 'Create User & Send Invite')]"
        )
        self.assertFalse(
            submit_btn.get_attribute("disabled"),
            "Submit button should be enabled when a valid email is entered"
        )
        submit_btn.click()

        # Success dialog: "User created successfully! ..."
        success_msg = self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//*[contains(text(), 'User created successfully')]")
            )
        )
        self.assertTrue(success_msg.is_displayed(), "Success dialog not shown after creation")

        # Grab a reference to the dialog backdrop BEFORE dismissing it.
        # We wait for staleness (DOM removal) rather than invisibility because
        # Framer Motion's exit animation keeps opacity > 0 for ~0.2 s, during
        # which Selenium's is_displayed() still returns True, causing
        # invisibility_of_element_located to time out.
        dialog_backdrop = self.driver.find_element(
            By.XPATH, "//div[contains(@class,'fixed') and contains(@class,'inset-0') and contains(@class,'z-[100]')]"
        )

        # Dismiss dialog — wait for it to be clickable first to avoid
        # clicking before the entrance animation has settled.
        great_btn = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[normalize-space(text())='Great!']")
            )
        )
        great_btn.click()

        # Wait for the dialog element to be removed from the DOM entirely.
        self.wait.until(EC.staleness_of(dialog_backdrop))

        # Search for the new user by email
        search = self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//input[@placeholder='Search users...']")
            )
        )
        search.clear()
        search.send_keys(TEST_EMAIL)

        # Wait for table to update
        time.sleep(1)

        # New user row must appear (matched by email in the User column)
        new_user_cell = self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, f"//td[.//*[contains(text(), '{TEST_EMAIL}')]]")
            )
        )
        self.assertTrue(
            new_user_cell.is_displayed(),
            f"Newly created user '{TEST_EMAIL}' not found in the user list"
        )

        print(f"\n[PASS] TC-07-002-A: User '{TEST_EMAIL}' created and appears in list.")

    # ── TC-07-002-B ──────────────────────────────────────────────────────────
    def test_B_add_user_empty_email_button_disabled(self):
        """
        TC-07-002-B
        Input:    Email: "" (empty), Role: "" (default)
        Expected: System rejects submission — 'Create User & Send Invite'
                  button is disabled; form cannot be submitted.
        """
        open_add_user_modal(self.driver, self.wait)

        # Ensure email field is empty
        email_input = self.driver.find_element(
            By.XPATH, "//input[@placeholder='Enter email address']"
        )
        email_input.clear()

        submit_btn = self.driver.find_element(
            By.XPATH, "//button[contains(., 'Create User & Send Invite')]"
        )

        # Button must be disabled (not clickable) when email is blank
        is_disabled = submit_btn.get_attribute("disabled") is not None
        self.assertTrue(
            is_disabled,
            "Submit button should be disabled when email field is empty"
        )

        close_modal_if_open(self.driver)
        print("\n[PASS] TC-07-002-B: Submit button disabled with empty email.")

    # ── TC-07-002-C ──────────────────────────────────────────────────────────
    def test_C_add_user_invalid_email_shows_inline_error(self):
        """
        TC-07-002-C
        Input:    Email: "notanemail" (invalid format)
        Expected: Inline error "Please enter a valid email address" is shown;
                  user is not created.
        """
        open_add_user_modal(self.driver, self.wait)

        email_input = self.driver.find_element(
            By.XPATH, "//input[@placeholder='Enter email address']"
        )
        email_input.clear()
        email_input.send_keys("notanemail")

        submit_btn = self.driver.find_element(
            By.XPATH, "//button[contains(., 'Create User & Send Invite')]"
        )
        submit_btn.click()

        # Inline error must appear
        error_msg = self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH,
                 "//*[contains(text(), 'Please enter a valid email address')]")
            )
        )
        self.assertTrue(
            error_msg.is_displayed(),
            "Expected inline error for invalid email, but it was not shown"
        )

        # Modal must still be open (user not created)
        modal_header = self.driver.find_element(
            By.XPATH, "//h2[contains(text(), 'Add New User')]"
        )
        self.assertTrue(
            modal_header.is_displayed(),
            "Modal should remain open after validation failure"
        )

        close_modal_if_open(self.driver)
        print("\n[PASS] TC-07-002-C: Inline validation error shown for invalid email.")

    # ── TC-07-003 ─────────────────────────────────────────────────────────────
    def test_D_edit_existing_user_updates_reflected_in_list(self):
        """
        TC-07-003
        Input:    Click edit on seeded user 'user1@drone4dengue.com';
                  update Name, Phone, and Address fields.
        Expected: Modal closes successfully; updated values are visible in the
                  user list table row.
        Note:     No success dialog is shown on edit — the modal closes and the
                  list silently refreshes.
        """
        # Search for the target user to ensure they're visible on the current page
        search = self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//input[@placeholder='Search users...']")
            )
        )
        search.clear()
        search.send_keys(EDIT_TARGET_EMAIL)
        time.sleep(1)  # allow debounce / re-render

        # Find the row containing the target email and click its edit button
        target_row = self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH,
                 f"//tr[.//td[.//*[contains(text(), '{EDIT_TARGET_EMAIL}')]]]")
            )
        )
        edit_btn = target_row.find_element(
            By.XPATH, ".//button[.//*[name()='svg']][1]"
        )
        edit_btn.click()

        # Edit modal must open
        self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//h2[contains(text(), 'Update User')]")
            )
        )

        # Updated values (timestamp suffix makes each run unique)
        new_name    = f"Edited User {TS}"
        new_phone   = f"601{TS}"
        new_address = f"Test Address {TS}"

        # Edit Name
        name_input = self.driver.find_element(
            By.XPATH, "//input[@placeholder='Enter full name']"
        )
        name_input.clear()
        name_input.send_keys(new_name)

        # Edit Phone
        phone_input = self.driver.find_element(
            By.XPATH, "//input[@placeholder='Enter phone number']"
        )
        phone_input.clear()
        phone_input.send_keys(new_phone)

        # Edit Address
        address_input = self.driver.find_element(
            By.XPATH, "//input[@placeholder='Enter address']"
        )
        address_input.clear()
        address_input.send_keys(new_address)

        # Confirm email field is read-only (cannot be edited)
        email_display = self.driver.find_element(
            By.XPATH,
            f"//div[contains(@class,'bg-gray-100') and contains(text(), '{EDIT_TARGET_EMAIL}')]"
        )
        self.assertTrue(
            email_display.is_displayed(),
            "Email should be shown as a read-only field in the edit modal"
        )

        # Submit update
        update_btn = self.driver.find_element(
            By.XPATH, "//button[contains(., 'Update User')]"
        )
        self.assertFalse(
            update_btn.get_attribute("disabled"),
            "Update button should be enabled when name is filled"
        )
        update_btn.click()

        # Modal must close (no success dialog — modal just disappears)
        self.wait.until(
            EC.invisibility_of_element_located(
                (By.XPATH, "//h2[contains(text(), 'Update User')]")
            )
        )

        # Wait for list to refresh
        time.sleep(1)

        # Updated name must appear in the table row for this user
        updated_name_cell = self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH,
                 f"//tr[.//td[.//*[contains(text(), '{EDIT_TARGET_EMAIL}')]]]"
                 f"//td[.//*[contains(text(), '{new_name}')]]")
            )
        )
        self.assertTrue(
            updated_name_cell.is_displayed(),
            f"Updated name '{new_name}' not found in the user list after edit"
        )

        print(f"\n[PASS] TC-07-003: User '{EDIT_TARGET_EMAIL}' updated to name '{new_name}'.")


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromTestCase(TC07002003UserAddEdit)

    runner = make_runner(
        report_name="TC-07-002-003-UserAddEdit",
        report_title="TP-07-002 | Add & Edit User Test Report",
    )
    runner.run(suite)
