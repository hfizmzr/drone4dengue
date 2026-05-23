"""UC-1 Login Account tests for the Android mobile app via Appium."""

from __future__ import annotations

import pytest

from conftest import (
    TEST_ADMIN_EMAIL,
    TEST_ADMIN_PASSWORD,
    TEST_MOBILE_EMAIL,
    TEST_MOBILE_PASSWORD,
    edit_texts,
    fill_edit_texts,
    is_text_visible,
    login_with_credentials,
    tap_text,
    wait_for_text,
)


# @pytest.mark.uc1
# @pytest.mark.appium
# def test_tc01_01_login_screen_shows_required_controls(login_screen):
#     """UC-1 precondition: login page exposes email, password, and Sign In."""
#     driver = login_screen

#     assert is_text_visible(driver, "Welcome Back", timeout=10)
#     assert is_text_visible(driver, "Email Address", timeout=10)
#     assert is_text_visible(driver, "Password", timeout=10)
#     assert is_text_visible(driver, "Forgot Password?", timeout=10)
#     assert is_text_visible(driver, "Sign In", timeout=10)
#     assert len(edit_texts(driver, minimum=2)) >= 2

@pytest.mark.uc1
@pytest.mark.appium
def test_tc01_01_valid_mobile_user_logs_in_to_dashboard(login_screen):
    """UC-1 main flow: a valid mobile user should be redirected to Dashboard."""
    driver = login_screen

    login_with_credentials(driver, TEST_MOBILE_EMAIL, TEST_MOBILE_PASSWORD)

    wait_for_text(driver, "Dashboard", timeout=35)
    assert is_text_visible(driver, "Dashboard", timeout=10)

@pytest.mark.uc1
@pytest.mark.appium
def test_tc01_02_admin_account_is_rejected_in_mobile_app(login_screen):
    """UC-1 role validation: admin users cannot log in through the mobile app."""
    driver = login_screen

    login_with_credentials(driver, TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD)

    assert is_text_visible(driver, "Admin users cannot log in through the mobile app", timeout=15)
    assert is_text_visible(driver, "Welcome Back", timeout=5)

@pytest.mark.uc1
@pytest.mark.appium
def test_tc01_03_sign_up_redirects_to_registration_page(login_screen):
    """UC-1 alternative flow: sign up should navigate to registration page."""
    driver = login_screen

    tap_text(driver, "Sign Up", timeout=10)

    assert is_text_visible(driver, "Create Account", timeout=20) or is_text_visible(
        driver, "Register", timeout=20
    )

@pytest.mark.uc1
@pytest.mark.appium
def test_tc01_04_forgot_password_navigates_to_reset_page(login_screen):
    """UC-1 exception flow: forgot password should open reset password page."""
    driver = login_screen

    tap_text(driver, "Forgot Password?", timeout=10)

    assert is_text_visible(driver, "Reset Password", timeout=15) or is_text_visible(
        driver, "Password reset", timeout=15
    )

@pytest.mark.uc1
@pytest.mark.appium
def test_tc01_05_empty_email_shows_required_error(login_screen):
    """UC-1 exception flow: empty email should show an email required message."""
    driver = login_screen

    fill_edit_texts(driver, ["", TEST_MOBILE_PASSWORD])
    tap_text(driver, "Sign In")

    assert is_text_visible(driver, "Email and password are required", timeout=10) or is_text_visible(
        driver, "Please enter your email", timeout=10
    )
    assert is_text_visible(driver, "Welcome Back", timeout=5)


@pytest.mark.uc1
@pytest.mark.appium
def test_tc01_05_empty_password_shows_required_error(login_screen):
    """UC-1 exception flow: empty password should show a password required message."""
    driver = login_screen

    fill_edit_texts(driver, [TEST_MOBILE_EMAIL, ""])
    tap_text(driver, "Sign In")

    assert is_text_visible(driver, "Email and password are required", timeout=10) or is_text_visible(
        driver, "Please enter your password", timeout=10
    )
    assert is_text_visible(driver, "Welcome Back", timeout=5)


@pytest.mark.uc1
@pytest.mark.appium
def test_tc01_05_both_fields_empty_show_required_errors(login_screen):
    """UC-1 exception flow: both fields empty should show required-field messages."""
    driver = login_screen

    tap_text(driver, "Sign In")

    assert (
        is_text_visible(driver, "Email and password are required", timeout=10)
        or is_text_visible(driver, "Please enter your email", timeout=10)
    )
    assert (
        is_text_visible(driver, "Email and password are required", timeout=10)
        or is_text_visible(driver, "Please enter your password", timeout=10)
    )
    assert is_text_visible(driver, "Welcome Back", timeout=5)


@pytest.mark.uc1
@pytest.mark.appium
def test_tc01_06_invalid_email_format_shows_validation_error(login_screen):
    """UC-1 exception flow: invalid email format should show a validation error."""
    driver = login_screen

    fill_edit_texts(driver, ["admin1", TEST_MOBILE_PASSWORD])
    tap_text(driver, "Sign In")

    assert is_text_visible(driver, "Invalid email address", timeout=10) or is_text_visible(
        driver, "Please enter a valid email address", timeout=10
    )
    assert is_text_visible(driver, "Welcome Back", timeout=5)


@pytest.mark.uc1
@pytest.mark.appium
def test_tc01_07_wrong_password_shows_incorrect_password_error(login_screen):
    """UC-1 exception flow: wrong password should show incorrect password message."""
    driver = login_screen

    login_with_credentials(driver, TEST_MOBILE_EMAIL, "wrong")

    assert is_text_visible(driver, "Invalid credentials", timeout=10) or is_text_visible(
        driver, "Wrong password. Please try again.", timeout=10
    )
    assert is_text_visible(driver, "Welcome Back", timeout=5)


@pytest.mark.uc1
@pytest.mark.appium
def test_tc01_08_unregistered_email_shows_user_not_found_error(login_screen):
    """UC-1 exception flow: unregistered email should show user not found message."""
    driver = login_screen

    login_with_credentials(driver, "unregistered@drone4dengue.local", "Abcd_1234")

    assert is_text_visible(driver, "Invalid credentials", timeout=10) or is_text_visible(
        driver, "User not found. Please check your email.", timeout=10
    )
    assert is_text_visible(driver, "Welcome Back", timeout=5)


@pytest.mark.uc1
@pytest.mark.appium
def test_tc01_09_too_many_failed_login_attempts_show_lockout_message(login_screen):
    """UC-1 exception flow: too many failed attempts should show a lockout message."""
    driver = login_screen

    for _ in range(7):
        login_with_credentials(driver, TEST_MOBILE_EMAIL, "Abcd_1234")

    assert is_text_visible(driver, "Too many failed attempts", timeout=15) or is_text_visible(
        driver, "Please try again later", timeout=15
    )
