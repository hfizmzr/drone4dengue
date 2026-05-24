
import pytest
import time
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from appium.options.android import UiAutomator2Options
# ─── CONFIGURATION ───────────────────────────────────────────────────
APPIUM_SERVER = "http://127.0.0.1:4723"
CAPS = {
    "platformName": "Android",
    "appium:deviceName": "Android Emulator",
    "appium:automationName": "UiAutomator2",
    "appium:appPackage": "com.adamarbain.dengueeyemobileapp",
    "appium:appActivity": ".MainActivity",
    "appium:noReset": True,
}
options = UiAutomator2Options().load_capabilities(CAPS)

REGISTERED_EMAIL = "siu72655@gmail.com"
UNREGISTERED_EMAIL = "notexist99999@test.com"
INVALID_EMAIL = "john"

# ─── HELPERS ─────────────────────────────────────────────────────────

def is_text_visible(driver, text, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (AppiumBy.ANDROID_UIAUTOMATOR,
                 f'new UiSelector().textContains("{text}")')
            )
        )
        return True
    except Exception:
        return False

def tap_text(driver, text, timeout=10):
    el = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located(
            (AppiumBy.ANDROID_UIAUTOMATOR,
             f'new UiSelector().textContains("{text}")')
        )
    )
    el.click()

def open_reset_modal(driver):
    """Tap Forgot Password? to open the reset modal."""
    tap_text(driver, "Forgot Password?")
    time.sleep(1)
    assert is_text_visible(driver, "Reset Password", timeout=10), \
        "Reset Password modal did not open"

def fill_reset_email(driver, email):
    """Fill in the email field in Step 1 of the reset modal."""
    email_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (AppiumBy.ANDROID_UIAUTOMATOR,
             'new UiSelector().textContains("Enter your email address")')
        )
    )
    email_field.clear()
    email_field.send_keys(email)

def email_send_success(driver):
    """Returns True if Step 2 (Enter Code) is visible, meaning code was sent."""
    return is_text_visible(driver, "Enter Code", timeout=5) or \
           is_text_visible(driver, "Check your email", timeout=5) or \
           is_text_visible(driver, "Verify Code", timeout=5)

def close_modal(driver):
    """Tap Cancel to close the reset modal."""
    try:
        tap_text(driver, "Cancel")
        time.sleep(1)
    except Exception:
        pass

# ─── FIXTURE ─────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def driver():
    d = webdriver.Remote(
        command_executor=APPIUM_SERVER,
        options=options
    )
    d.implicitly_wait(5)
    # Make sure we are on the login screen
    assert is_text_visible(d, "Welcome Back", timeout=15), \
        "Login screen not visible on app launch"
    yield d
    d.quit()

# ─── TC-0401: Valid registered email → reset code sent ───────────────

def test_valid_registered_email(driver):
    open_reset_modal(driver)
    fill_reset_email(driver, REGISTERED_EMAIL)
    tap_text(driver, "Send Reset Code")
    time.sleep(3)
    try:
        assert email_send_success(driver), \
            "Email send failed — backend returned error or no success confirmation"
    except AssertionError:
        # Check if error message appeared
        error_visible = is_text_visible(driver, "Failed to send", timeout=3) or \
                        is_text_visible(driver, "Email configuration", timeout=3) or \
                        is_text_visible(driver, "something went wrong", timeout=3)
        assert not error_visible, \
            "Backend returned email configuration error — SENDER_EMAIL not configured"
        raise
    finally:
        close_modal(driver)

# ─── TC-0402: Sign in / Cancel → modal closes ────────────────────────

def test_cancel_closes_modal(driver):
    open_reset_modal(driver)
    tap_text(driver, "Cancel")
    time.sleep(1)
    assert is_text_visible(driver, "Welcome Back", timeout=5), \
        "Modal did not close after tapping Cancel"

# ─── TC-0403: Resend code visible after successful send ──────────────

def test_resend_code(driver):
    open_reset_modal(driver)
    fill_reset_email(driver, REGISTERED_EMAIL)
    tap_text(driver, "Send Reset Code")
    time.sleep(3)
    try:
        assert email_send_success(driver), \
            "Email send failed — resend step unreachable"
        # On Step 2, the subtitle says "Check your email for the verification code"
        assert is_text_visible(driver, "Check your email", timeout=5), \
            "Resend hint not visible after code sent"
    except AssertionError:
        raise
    finally:
        close_modal(driver)

# ─── TC-0404: Unregistered email → error shown ───────────────────────

def test_unregistered_email(driver):
    open_reset_modal(driver)
    fill_reset_email(driver, UNREGISTERED_EMAIL)
    tap_text(driver, "Send Reset Code")
    time.sleep(3)
    try:
        assert is_text_visible(driver, "not found", timeout=5) or \
               is_text_visible(driver, "No account", timeout=5) or \
               is_text_visible(driver, "invalid", timeout=5) or \
               is_text_visible(driver, "Failed", timeout=5), \
            "No error shown for unregistered email"
    finally:
        close_modal(driver)

# ─── TC-0405: Password mismatch → error shown ────────────────────────

def test_password_mismatch(driver):
    open_reset_modal(driver)
    fill_reset_email(driver, REGISTERED_EMAIL)
    tap_text(driver, "Send Reset Code")
    time.sleep(3)

    if not email_send_success(driver):
        close_modal(driver)
        pytest.skip("SEND CODE failed — password mismatch step unreachable")

    # Step 2 — enter any 6-digit code
    code_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (AppiumBy.ANDROID_UIAUTOMATOR,
             'new UiSelector().textContains("Enter 6-digit code")')
        )
    )
    code_field.send_keys("123456")
    tap_text(driver, "Verify Code")
    time.sleep(3)

    # If code is wrong, error shown — skip to avoid false fail
    if not is_text_visible(driver, "New Password", timeout=5):
        close_modal(driver)
        pytest.skip("Code verification failed — cannot reach password mismatch step")

    # Step 3 — enter mismatching passwords
    fields = driver.find_elements(
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().className("android.widget.EditText")'
    )
    assert len(fields) >= 2, "Password fields not found in Step 3"
    fields[0].send_keys("NewPass123")
    fields[1].send_keys("DifferentPass999")
    tap_text(driver, "Reset Password")
    time.sleep(2)

    try:
        assert is_text_visible(driver, "do not match", timeout=5) or \
               is_text_visible(driver, "Passwords do not match", timeout=5), \
            "Password mismatch error not shown"
    finally:
        close_modal(driver)

# ─── TC-0406: Invalid email format → error shown ─────────────────────

def test_invalid_email_format(driver):
    open_reset_modal(driver)
    fill_reset_email(driver, INVALID_EMAIL)
    tap_text(driver, "Send Reset Code")
    time.sleep(2)
    try:
        assert is_text_visible(driver, "valid email", timeout=5) or \
               is_text_visible(driver, "invalid", timeout=5) or \
               is_text_visible(driver, "Failed", timeout=5), \
            "No error shown for invalid email format"
    finally:
        close_modal(driver)