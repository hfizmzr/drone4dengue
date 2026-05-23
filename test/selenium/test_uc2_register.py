"""UC-2 Register Account tests for the admin web application."""

from __future__ import annotations

import time

import pytest
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from conftest import ADMIN_EMAIL, BASE_URL, DEFAULT_WAIT, HEADLESS


VALID_PASSWORD = "TestPass1!"
TIMESTAMP = lambda: str(int(time.time() * 1000))


def unique_email() -> str:
    return f"uc2.selenium.{TIMESTAMP()}@example.com"


def navigate_to_signup(driver):
    driver.get(f"{BASE_URL}/signup")
    WebDriverWait(driver, DEFAULT_WAIT).until(
        EC.visibility_of_element_located(
            (By.XPATH, "//h2[contains(normalize-space(.), 'Create Account')]")
        )
    )
    time.sleep(0.5)


def fill_text_field(driver, field_id: str, value: str):
    field = WebDriverWait(driver, DEFAULT_WAIT).until(
        EC.presence_of_element_located((By.ID, field_id))
    )
    field.clear()
    field.send_keys(value)
    return field


def select_company(driver, value: str | None = None):
    select_element = WebDriverWait(driver, DEFAULT_WAIT).until(
        EC.presence_of_element_located((By.ID, "company"))
    )
    select = Select(select_element)
    if value:
        select.select_by_value(value)
    else:
        options = [o.get_attribute("value") for o in select.options if o.get_attribute("value")]
        if options:
            select.select_by_value(options[0])


def accept_terms(driver):
    button = WebDriverWait(driver, DEFAULT_WAIT).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Accept Terms and Privacy Policy']"))
    )
    button.click()
    time.sleep(0.2)


def click_submit(driver):
    button = WebDriverWait(driver, DEFAULT_WAIT).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
    )
    button.click()


def fill_register_form(
    driver,
    email: str,
    name: str = "Test User",
    username: str = None,
    phone: str | None = None,
    password: str = VALID_PASSWORD,
    confirm_password: str | None = None,
    select_company_option: bool = True,
):
    fill_text_field(driver, "email", email)
    fill_text_field(driver, "name", name)
    fill_text_field(driver, "username", username or f"testuser{TIMESTAMP()}")
    if phone is None:
        phone = f"0123{int(time.time() * 1000) % 10000000}"
    fill_text_field(driver, "phone", phone)
    fill_text_field(driver, "password", password)
    fill_text_field(driver, "confirmPassword", confirm_password or password)
    if select_company_option:
        select_company(driver)
    accept_terms(driver)


@pytest.fixture(scope="class")
def register_driver():
    """Dedicated unauthenticated Chrome for UC2 registration tests."""
    chrome_options = Options()
    if HEADLESS:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    service = Service()
    browser = webdriver.Chrome(service=service, options=chrome_options)
    browser.implicitly_wait(5)
    yield browser
    browser.quit()


@pytest.mark.uc2
@pytest.mark.selenium
class TestUC2Register:
    """Test suite for Use Case 2: Register Account."""

    def test_tc02_01_open_register_from_login(self, register_driver):
        """TC-02-001: Verify user can open Register screen from Login screen."""
        register_driver.get(BASE_URL)
        sign_up_link = WebDriverWait(register_driver, DEFAULT_WAIT).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/signup']"))
        )
        sign_up_link.click()

        WebDriverWait(register_driver, DEFAULT_WAIT).until(EC.url_contains("/signup"))
        heading = WebDriverWait(register_driver, DEFAULT_WAIT).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//h2[contains(normalize-space(.), 'Create Account')]")
            )
        )
        assert heading.is_displayed()

    def test_tc02_02_register_form_shows_all_controls(self, register_driver):
        """TC-02-002: Verify the Register screen displays all required controls."""
        navigate_to_signup(register_driver)

        expected_labels = ["Email Address", "Full Name", "Username", "Phone Number", "Password", "Confirm Password"]
        for label_text in expected_labels:
            label = register_driver.find_element(
                By.XPATH, f"//label[contains(normalize-space(.), '{label_text}')]"
            )
            assert label.is_displayed()

        expected_inputs = ["email", "name", "username", "phone", "password", "confirmPassword"]
        for field_id in expected_inputs:
            assert register_driver.find_element(By.ID, field_id).is_displayed()

        select_element = register_driver.find_element(By.ID, "company")
        assert select_element.is_displayed()
        assert select_element.tag_name == "select"

        terms_button = register_driver.find_element(
            By.CSS_SELECTOR, "button[aria-label='Accept Terms and Privacy Policy']"
        )
        assert terms_button.is_displayed()

        terms_link = register_driver.find_element(By.XPATH, "//a[contains(@href, '/terms')]")
        assert terms_link.is_displayed()
        assert "Terms and Privacy Policy" in terms_link.text

        login_link = register_driver.find_element(
            By.XPATH, "//a[contains(@href, '/') and contains(., 'Login')]"
        )
        assert login_link.is_displayed()

        assert len(register_driver.find_elements(By.CSS_SELECTOR, "input, select")) >= 3

    def test_tc02_03_empty_fields_validation(self, register_driver):
        """TC-02-003: Verify registration cannot proceed when required fields are empty."""
        navigate_to_signup(register_driver)
        accept_terms(register_driver)
        click_submit(register_driver)
        time.sleep(0.5)

        error_selectors = [
            "#email:invalid",
            "#name:invalid",
            "#username:invalid",
            "#phone:invalid",
            "#password:invalid",
            "#confirmPassword:invalid",
            "#company:invalid",
        ]
        invalid_found = False
        for selector in error_selectors:
            try:
                element = register_driver.find_element(By.CSS_SELECTOR, selector)
                if element.get_attribute("required"):
                    invalid_found = True
                    break
            except Exception:
                pass

        field_errors_found = len(register_driver.find_elements(
            By.XPATH, "//p[contains(@class, 'text-xs') and contains(text(), 'required')]"
        )) > 0

        assert invalid_found or field_errors_found

    def test_tc02_04_invalid_email_rejected(self, register_driver):
        """TC-02-004: Verify registration rejects an invalid email format."""
        navigate_to_signup(register_driver)
        fill_text_field(register_driver, "email", "not-an-email")
        fill_text_field(register_driver, "name", "Test User")
        fill_text_field(register_driver, "username", f"testuser{TIMESTAMP()}")
        fill_text_field(register_driver, "phone", "0123456789")
        fill_text_field(register_driver, "password", VALID_PASSWORD)
        fill_text_field(register_driver, "confirmPassword", VALID_PASSWORD)
        select_company(register_driver)
        accept_terms(register_driver)
        click_submit(register_driver)

        try:
            error = WebDriverWait(register_driver, 5).until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//p[contains(@class, 'text-xs') and contains(text(), 'valid email')]")
                )
            )
            assert error.is_displayed()
        except TimeoutException:
            vtooltip = register_driver.find_element(By.CSS_SELECTOR, "#email:invalid")
            assert vtooltip

    def test_tc02_05_password_mismatch_rejected(self, register_driver):
        """TC-02-005: Verify registration rejects mismatched passwords."""
        navigate_to_signup(register_driver)
        fill_text_field(register_driver, "email", unique_email())
        fill_text_field(register_driver, "name", "Test User")
        fill_text_field(register_driver, "username", f"testuser{TIMESTAMP()}")
        fill_text_field(register_driver, "phone", "0123456789")
        fill_text_field(register_driver, "password", VALID_PASSWORD)
        fill_text_field(register_driver, "confirmPassword", "Different1!")
        select_company(register_driver)
        accept_terms(register_driver)
        click_submit(register_driver)

        error = WebDriverWait(register_driver, 5).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//p[contains(@class, 'text-xs') and contains(text(), 'do not match')]")
            )
        )
        assert error.is_displayed()

    def test_tc02_06_terms_link_opens_terms_page(self, register_driver):
        """TC-02-006: Verify Terms & Conditions link opens the terms page."""
        navigate_to_signup(register_driver)

        original_window = register_driver.current_window_handle

        terms_link = WebDriverWait(register_driver, DEFAULT_WAIT).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/terms')]"))
        )
        terms_link.click()

        WebDriverWait(register_driver, DEFAULT_WAIT).until(
            lambda d: len(d.window_handles) > 1
        )
        new_window = [w for w in register_driver.window_handles if w != original_window][0]
        register_driver.switch_to.window(new_window)

        WebDriverWait(register_driver, DEFAULT_WAIT).until(
            EC.url_contains("/terms")
        )

        page_text = register_driver.find_element(By.TAG_NAME, "body").text
        assert "Terms of Service" in page_text or "Privacy Policy" in page_text

        register_driver.close()
        register_driver.switch_to.window(original_window)

    def test_tc02_07_valid_registration_success(self, register_driver):
        """TC-02-007: Verify successful registration with valid details."""
        email = unique_email()
        navigate_to_signup(register_driver)

        fill_register_form(register_driver, email=email)
        click_submit(register_driver)

        WebDriverWait(register_driver, DEFAULT_WAIT).until(
            lambda d: "/" in d.current_url and "signup" not in d.current_url
        )

        assert "/" in register_driver.current_url

    def test_tc02_08_duplicate_email_rejected(self, register_driver):
        """TC-02-008: Verify duplicate registration is blocked."""
        navigate_to_signup(register_driver)

        fill_register_form(register_driver, email=ADMIN_EMAIL)
        click_submit(register_driver)

        error = WebDriverWait(register_driver, 10).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "[role='alert'] li")
            )
        )
        assert "already registered" in error.text.lower()
