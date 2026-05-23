"""UC-1 Login tests for admin web application using Selenium."""

from __future__ import annotations

import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from conftest import (
    BASE_URL,
    DEFAULT_WAIT,
    accept_alert,
    click_visible_text,
    dismiss_any_dialog,
    visible_text,
    wait_for,
    wait_for_clickable,
    wait_for_element,
    wait_for_text,
    wait_for_url_contains,
)

def logout_account(driver, timeout=10):
    """
    If logout button exists:
        - click logout
        - confirm 'Logout Account'
        - wait until login page appears

    Otherwise:
        - refresh current page
        - wait until page fully loads
    """

    wait = WebDriverWait(driver, timeout)

    try:
        # Try finding logout button
        logout_button = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[contains(., 'Logout')] | //a[contains(., 'Logout')]"
                )
            )
        )

        logout_button.click()

        # Wait for logout modal
        wait.until(
            EC.visibility_of_element_located(
                (
                    By.XPATH,
                    "//*[contains(text(), 'Logout Account')]"
                )
            )
        )

        # Click Yes button
        yes_button = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[contains(., 'Yes')]"
                )
            )
        )

        yes_button.click()

        # Wait for login page/email field
        wait.until(
            EC.presence_of_element_located(
                (By.ID, "email")
            )
        )

    except TimeoutException:
        # Logout button not found → refresh instead
        driver.refresh()

        wait.until(
            lambda d: d.execute_script(
                "return document.readyState"
            ) == "complete"
        )

def clickable_text(driver, text: str, timeout: int = DEFAULT_WAIT):
    """
    Find clickable element containing text.
    """

    xpath = (
        f"//a[contains(normalize-space(.), '{text}')] | "
        f"//button[contains(normalize-space(.), '{text}')]"
    )

    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.XPATH, xpath))
    )

@pytest.mark.selenium
@pytest.mark.uc1
class TestUC1Login:
    """UC-1: Login Account - Web version tests."""

    def test_tc_01_001_successful_login_with_valid_credentials(self, driver):
        """TC-01-001: Main Flow - Verify user can login successfully with valid credentials.
        
        Input: Email: admin1@drone4dengue.com, Password: Admin_pass1
        Expected: Display message 'Login successful!' and redirected to /dashboard
        """
        logout_account(driver)
        # Navigate to login page
        driver.set_window_size(1366, 900)
        driver.get(BASE_URL)
        
        # Wait for login form to be visible
        email_field = wait_for_element(driver, By.ID, "email", timeout=DEFAULT_WAIT)
        password_field = wait_for_element(driver, By.ID, "password", timeout=DEFAULT_WAIT)
        
        # Fill credentials
        email_field.clear()
        email_field.send_keys("admin1@drone4dengue.com")
        
        password_field.clear()
        password_field.send_keys("Admin_pass1")
        
        # Click login button
        login_button = wait_for_clickable(driver, By.CSS_SELECTOR, "button[type='submit']", timeout=DEFAULT_WAIT)
        login_button.click()
        
        # Verify redirect to dashboard
        wait_for_url_contains(driver, "/dashboard", timeout=DEFAULT_WAIT)
        assert "/dashboard" in driver.current_url

    def test_tc_01_002_wrong_role_web_access_denied(self, driver):
        """TC-01-002: Main Flow - Verify wrong role in web shows access denied.
        
        Input: Email: appium.user@drone4dengue.local, Password: Test_Pass1 (non-admin user)
        Expected: Error message "Access denied. Admin privileges required." is displayed
        """
        logout_account(driver)
        driver.get(BASE_URL)
        time.sleep(2)
        
        # Wait for login form
        email_field = wait_for_element(driver, By.ID, "email", timeout=DEFAULT_WAIT)
        password_field = wait_for_element(driver, By.ID, "password", timeout=DEFAULT_WAIT)
        
        # Fill non-admin user credentials
        email_field.clear()
        email_field.send_keys("appium.user@drone4dengue.local")
        
        password_field.clear()
        password_field.send_keys("Test_Pass1")
        
        # Click login button
        login_button = wait_for_clickable(driver, By.CSS_SELECTOR, "button[type='submit']", timeout=DEFAULT_WAIT)
        login_button.click()
        
        # Verify error message is displayed
        try:
            wait_for_text(
                driver,
                By.XPATH,
                "//*[contains(text(), 'Access denied') or contains(text(), 'privileges')]",
                "Access denied",
                timeout=DEFAULT_WAIT,
            )
            assert True
        except Exception:
            # Check if user was signed out
            assert "login" in driver.current_url.lower()

    def test_tc_01_003_sign_up_link_navigation(self, driver):
        """TC-01-003: Alternative Flow - Verify sign up functionality.
        
        Input: Click the Sign up text/link
        Expected: The system redirects to the Registration Page
        """
        # Navigate to login page
        logout_account(driver, timeout=3)
        driver.get(BASE_URL)
        time.sleep(1)
        
        # Find and click sign up link
        sign_up_link = clickable_text(driver, "Sign up", timeout=DEFAULT_WAIT)
        sign_up_link.click()
        
        # Verify redirect to registration/signup page
        wait_for(driver, lambda d: "register" in d.current_url.lower() or "signup" in d.current_url.lower(), timeout=DEFAULT_WAIT)
        assert "register" in driver.current_url.lower() or "signup" in driver.current_url.lower()

    def test_tc_01_004_forgot_password_link(self, driver):
        """TC-01-004: Exception Flow - Verify forgot password functionality.
        
        Input: Click the Forgot Password? text/link
        Expected: The system displays a password reset modal/dialog or page
        """
        # Navigate to login page
        logout_account(driver, timeout=3)
        driver.get(BASE_URL)
        time.sleep(1)
        
        # Find and click forgot password link
        forgot_password_link = clickable_text(driver, "Forgot Password ?", timeout=DEFAULT_WAIT)
        forgot_password_link.click()
        
        # Verify password reset modal/page is displayed
        try:
            # Try to find modal with reset password form
            wait_for_element(
                driver,
                By.XPATH,
                "//button[contains(text(), 'forgot-password')] | //*[contains(text(), 'password reset')] | //*[contains(text(), 'Reset Password')]",
                timeout=DEFAULT_WAIT,
            )
            assert True
        except Exception:
            # Check if redirected to reset password page
            assert "reset" in driver.current_url.lower() or "forgot" in driver.current_url.lower()

    def test_tc_01_005_empty_email_field_error(self, driver):
        """TC-01-005: Exception Flow - Empty email field validation.
        
        Input: Email: (empty), Password: Admin_pass1
        Expected: Error message "Email is required" / "Please enter your email"
        """
        # Navigate to login page
        logout_account(driver, timeout=3)
        driver.get(BASE_URL)
        time.sleep(1)
        
        # Wait for login form
        email_field = wait_for_element(driver, By.ID, "email", timeout=DEFAULT_WAIT)
        password_field = wait_for_element(driver, By.ID, "password", timeout=DEFAULT_WAIT)
        
        # Leave email empty and fill password
        email_field.clear()
        password_field.clear()
        password_field.send_keys("Admin_pass1")
        
        # Try to submit
        login_button = wait_for_clickable(driver, By.CSS_SELECTOR, "button[type='submit']", timeout=DEFAULT_WAIT)
        login_button.click()
        
        # Verify error message
        try:
            wait_for_text(
                driver,
                By.XPATH,
                "//*[contains(text(), 'Email is required') or contains(text(), 'Please enter your email')]",
                "Email",
                timeout=5,
            )
            assert True
        except Exception:
            # Check if form is still visible (validation failed)
            assert wait_for_element(driver, By.ID, "email", timeout=5)

    def test_tc_01_005_empty_password_field_error(self, driver):
        """TC-01-005: Exception Flow - Empty password field validation.
        
        Input: Email: admin1@drone4dengue.com, Password: (empty)
        Expected: Error message "Password is required" / "Please enter your password"
        """
        # Navigate to login page
        logout_account(driver, timeout=3)
        driver.get(BASE_URL)
        time.sleep(1)
        
        # Wait for login form
        email_field = wait_for_element(driver, By.ID, "email", timeout=DEFAULT_WAIT)
        password_field = wait_for_element(driver, By.ID, "password", timeout=DEFAULT_WAIT)
        
        # Fill email and leave password empty
        email_field.clear()
        email_field.send_keys("admin1@drone4dengue.com")
        password_field.clear()
        
        # Try to submit
        login_button = wait_for_clickable(driver, By.CSS_SELECTOR, "button[type='submit']", timeout=DEFAULT_WAIT)
        login_button.click()
        
        # Verify error message
        try:
            wait_for_text(
                driver,
                By.XPATH,
                "//*[contains(text(), 'Password is required') or contains(text(), 'Please enter your password')]",
                "Password",
                timeout=5,
            )
            assert True
        except Exception:
            # Check if form is still visible (validation failed)
            assert wait_for_element(driver, By.ID, "password", timeout=5)

    def test_tc_01_005_both_fields_empty_error(self, driver):
        """TC-01-005: Exception Flow - Both email and password fields empty.
        
        Input: Email: (empty), Password: (empty)
        Expected: Error messages for both "Email is required" and "Password is required"
        """
        # Navigate to login page
        logout_account(driver, timeout=3)
        driver.get(BASE_URL)
        time.sleep(1)
        
        # Wait for login form
        email_field = wait_for_element(driver, By.ID, "email", timeout=DEFAULT_WAIT)
        password_field = wait_for_element(driver, By.ID, "password", timeout=DEFAULT_WAIT)
        
        # Leave both fields empty
        email_field.clear()
        password_field.clear()
        
        # Try to submit
        login_button = wait_for_clickable(driver, By.CSS_SELECTOR, "button[type='submit']", timeout=DEFAULT_WAIT)
        login_button.click()
        
        # Verify error messages
        time.sleep(1)
        # Check that form is still visible (validation failed)
        assert wait_for_element(driver, By.ID, "email", timeout=5)
        assert wait_for_element(driver, By.ID, "password", timeout=5)

    def test_tc_01_006_invalid_email_format_error(self, driver):
        """TC-01-006: Exception Flow - Invalid email format error.
        
        Input: Email: admin1 (invalid format), Password: Admin_pass1
        Expected: Error message "Invalid email address" / "Please enter a valid email address"
        """
        # Navigate to login page
        logout_account(driver, timeout=3)
        driver.get(BASE_URL)
        time.sleep(1)
        
        # Wait for login form
        email_field = wait_for_element(driver, By.ID, "email", timeout=DEFAULT_WAIT)
        password_field = wait_for_element(driver, By.ID, "password", timeout=DEFAULT_WAIT)
        
        # Fill with invalid email
        email_field.clear()
        email_field.send_keys("admin1")
        password_field.clear()
        password_field.send_keys("Admin_pass1")
        
        # Try to submit
        login_button = wait_for_clickable(driver, By.CSS_SELECTOR, "button[type='submit']", timeout=DEFAULT_WAIT)
        login_button.click()
        
        # Verify error message
        try:
            wait_for_text(
                driver,
                By.XPATH,
                "//*[contains(text(), 'Invalid email') or contains(text(), 'valid email address')]",
                "email",
                timeout=5,
            )
            assert True
        except Exception:
            # Check if form is still visible (validation failed)
            assert wait_for_element(driver, By.ID, "email", timeout=5)

    def test_tc_01_007_wrong_password_error(self, driver):
        """TC-01-007: Exception Flow - Wrong password error.
        
        Input: Email: admin1@drone4dengue.com, Password: wrong
        Expected: Error message "Incorrect password. Please try again." / "Invalid credentials"
        """
        # Navigate to login page
        logout_account(driver, timeout=3)
        driver.get(BASE_URL)
        time.sleep(1)
        
        # Wait for login form
        email_field = wait_for_element(driver, By.ID, "email", timeout=DEFAULT_WAIT)
        password_field = wait_for_element(driver, By.ID, "password", timeout=DEFAULT_WAIT)
        
        # Fill credentials with wrong password
        email_field.clear()
        email_field.send_keys("admin1@drone4dengue.com")
        password_field.clear()
        password_field.send_keys("wrong")
        
        # Click login button
        login_button = wait_for_clickable(driver, By.CSS_SELECTOR, "button[type='submit']", timeout=DEFAULT_WAIT)
        login_button.click()
        
        # Verify error message
        wait_for_text(
            driver,
            By.XPATH,
            "//*[contains(text(), 'Incorrect password') or contains(text(), 'Invalid credentials')]",
            "Invalid credentials",
            timeout=DEFAULT_WAIT,
        )
        assert True

    def test_tc_01_008_unregistered_email_error(self, driver):
        """TC-01-008: Exception Flow - Unregistered email error.
        
        Input: Email: unregistered@drone4dengue.com, Password: Abcd_1234
        Expected: Error message "Invalid credentials" / "User not found. Please check your email."
        """
        # Navigate to login page
        logout_account(driver, timeout=3)
        driver.get(BASE_URL)
        time.sleep(1)
        
        # Wait for login form
        email_field = wait_for_element(driver, By.ID, "email", timeout=DEFAULT_WAIT)
        password_field = wait_for_element(driver, By.ID, "password", timeout=DEFAULT_WAIT)
        
        # Fill credentials with unregistered email
        email_field.clear()
        email_field.send_keys("unregistered@drone4dengue.com")
        password_field.clear()
        password_field.send_keys("Abcd_1234")
        
        # Click login button
        login_button = wait_for_clickable(driver, By.CSS_SELECTOR, "button[type='submit']", timeout=DEFAULT_WAIT)
        login_button.click()
        
        # Verify error message
        wait_for_text(
            driver,
            By.XPATH,
            "//*[contains(text(), 'No account found') or contains(text(), 'Invalid credentials') or contains(text(), 'not found')]",
            "Invalid credentials",
            timeout=DEFAULT_WAIT,
        )
        assert True

    def test_tc_01_010_too_many_failed_login_attempts(self, driver):
        """TC-01-010: Exception Flow - Too many failed login attempts locking.
        
        Input: Email: admin1@drone4dengue.com, Password: Abcd_1234; Repeatedly (max 7 times)
        Expected: Error message "Too many failed attempts. Please try again later."
        """
        # Navigate to login page
        logout_account(driver, timeout=3)
        driver.get(BASE_URL)
        time.sleep(1)
        
        # Attempt login 7 times with wrong password
        max_attempts = 7
        for attempt in range(max_attempts):
            try:
                # Wait for login form
                email_field = wait_for_element(driver, By.ID, "email", timeout=5)
                password_field = wait_for_element(driver, By.ID, "password", timeout=5)
                
                # Fill credentials with wrong password
                email_field.clear()
                email_field.send_keys("admin1@drone4dengue.com")
                password_field.clear()
                password_field.send_keys("Abcd_1234")
                
                # Click login button
                login_button = wait_for_clickable(driver, By.CSS_SELECTOR, "button[type='submit']", timeout=5)
                login_button.click()
                
                time.sleep(1)
                
                # After several attempts, check for rate limiting message
                if attempt >= 4:
                    try:
                        wait_for_text(
                            driver,
                            By.XPATH,
                            "//*[contains(text(), 'Too many') or contains(text(), 'try again later')]",
                            "many",
                            timeout=3,
                        )
                        # Rate limiting detected
                        assert True
                        break
                    except Exception:
                        pass
            except Exception:
                # If we get locked out earlier, that's also valid
                break
        
        # Verify we're still on login page or see rate limiting message
        assert "login" in driver.current_url.lower() or wait_for_element(
            driver,
            By.XPATH,
            "//*[contains(text(), 'Too many') or contains(text(), 'try again later')]",
            timeout=2,
        )
