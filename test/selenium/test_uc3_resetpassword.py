import pytest
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "http://localhost:3000/forgot-password"
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "..", "screenshots")


@pytest.fixture
def driver():
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install())
    )
    driver.maximize_window()
    yield driver
    driver.quit()


def save_screenshot(driver, name):
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    driver.save_screenshot(
        os.path.join(SCREENSHOT_DIR, name + ".png")
    )


def open_page(driver):
    driver.get(BASE_URL)

    wait = WebDriverWait(driver, 10)

    wait.until(
        EC.presence_of_element_located(
            (By.ID, "email")
        )
    )

    return wait


def submit_email(driver, email):
    driver.find_element(
        By.ID,
        "email"
    ).clear()

    driver.find_element(
        By.ID,
        "email"
    ).send_keys(email)

    driver.find_element(
        By.XPATH,
        "//button[contains(text(),'SEND CODE')]"
    ).click()

    time.sleep(3)

    return driver.find_element(
        By.TAG_NAME,
        "body"
    ).text.lower()


def email_send_success(body_text):
    # First check if backend returned any known error
    backend_errors = [
        "email configuration error",
        "missing credentials",
        "failed to send",
        "eauth",
        "contact support"
    ]
    for err in backend_errors:
        if err in body_text:
            return False
    # Then check if real success markers exist
    success_markers = [
        "enter code",
        "verification code",
        "check your email",
        "resend code"
    ]
    return any(marker in body_text for marker in success_markers)


# TC-0301: Valid registered email → reset code sent
def test_valid_registered_email(driver):
    driver.get(BASE_URL)
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.ID, "email")))
    driver.find_element(By.ID, "email").send_keys("boonzgame808@gmail.com")
    driver.find_element(By.XPATH, "//button[contains(text(),'SEND CODE')]").click()
    try:
        time.sleep(3)
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        assert email_send_success(body_text), "Email send failed — backend returned error or no success confirmation"
        save_screenshot(driver, "pass_valid_reset_email")
    except Exception:
        save_screenshot(driver, "fail_valid_reset_email")
        raise


# TC-0303: Resend code option available after submitting valid email
def test_resend_code(driver):
    driver.get(BASE_URL)
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.ID, "email")))
    driver.find_element(By.ID, "email").send_keys("boonzgame808@gmail.com")
    driver.find_element(By.XPATH, "//button[contains(text(),'SEND CODE')]").click()
    try:
        time.sleep(3)
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        assert email_send_success(body_text), "Email send failed — resend option unreachable"
        assert "resend" in body_text, "Resend option not visible after successful code send"
        save_screenshot(driver, "pass_resend_code")
    except Exception:
        save_screenshot(driver, "fail_resend_code")
        raise


# TC-0305: Mismatching passwords → re-entry prompted
def test_password_mismatch(driver):
    driver.get(BASE_URL)
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.ID, "email")))
    driver.find_element(By.ID, "email").send_keys("boonzgame808@gmail.com")
    driver.find_element(By.XPATH, "//button[contains(text(),'SEND CODE')]").click()
    time.sleep(3)
    body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
    if not email_send_success(body_text):
        pytest.skip("SEND CODE failed — password mismatch step unreachable")
    try:
        new_pass_fields = driver.find_elements(By.XPATH, "//input[@type='password']")
        assert len(new_pass_fields) >= 2, "Password fields not found after code send"
        new_pass_fields[0].send_keys("NewPass123")
        new_pass_fields[1].send_keys("DifferentPass999")
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(2)
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        assert "match" in body_text or "mismatch" in body_text or "same" in body_text
        save_screenshot(driver, "pass_password_mismatch")
    except Exception:
        save_screenshot(driver, "fail_password_mismatch")
        raise


# TC0302
# TC-0304: Unregistered email → error shown
def test_unregistered_email(driver):
    driver.get(BASE_URL)
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.ID, "email")))
    driver.find_element(By.ID, "email").send_keys("notexist99999@test.com")
    driver.find_element(By.XPATH, "//button[contains(text(),'SEND CODE')]").click()
    try:
        time.sleep(2)
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        assert "not found" in body_text or "invalid" in body_text or "error" in body_text or "wrong" in body_text
        save_screenshot(driver, "pass_unregistered_reset_email")
    except Exception:
        save_screenshot(driver, "fail_unregistered_reset_email")
        raise

# TC-0306: Invalid email format → error shown
def test_invalid_email_format(driver):
    driver.get(BASE_URL)
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.ID, "email")))
    driver.find_element(By.ID, "email").send_keys("john")
    driver.find_element(By.XPATH, "//button[contains(text(),'SEND CODE')]").click()
    try:
        time.sleep(2)
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        assert "valid" in body_text or "invalid" in body_text or "format" in body_text or "email" in body_text
        save_screenshot(driver, "pass_invalid_email_format")
    except Exception:
        save_screenshot(driver, "fail_invalid_email_format")
        raise

# TC-0302: Sign in link → redirected back to Login
def test_signin_redirect(driver):
    driver.get(BASE_URL)
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Sign in')]")))
    driver.find_element(By.XPATH, "//*[contains(text(),'Sign in')]").click()
    try:
        time.sleep(2)
        assert driver.current_url != "http://localhost:3000/forgot-password"
        save_screenshot(driver, "pass_signin_redirect")
    except Exception:
        save_screenshot(driver, "fail_signin_redirect")
        raise