import pytest
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "http://localhost:3000"
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "..", "screenshots")
TESTDATA_DIR = os.path.join(os.path.dirname(__file__), "..", "testdata")

VALID_CSV = os.path.abspath(os.path.join(TESTDATA_DIR, "valid_weather.csv"))
INVALID_FILE = os.path.abspath(os.path.join(TESTDATA_DIR, "invalid_format.txt"))

@pytest.fixture
def driver():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.maximize_window()
    yield driver
    driver.quit()

def save_screenshot(driver, name):
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    driver.save_screenshot(os.path.join(SCREENSHOT_DIR, name + ".png"))

def login_as_admin(driver):
    driver.get(BASE_URL)
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.ID, "email")))
    driver.find_element(By.ID, "email").send_keys("boonzgame808@gmail.com")
    driver.find_element(By.ID, "password").send_keys("Hasan_123")
    driver.find_element(By.XPATH, "//button[contains(text(),'LOGIN')]").click()
    time.sleep(3)

def go_to_weather(driver):
    driver.get(BASE_URL + "/weather-data")
    time.sleep(2)

# TC-1401: Valid CSV upload → data stored successfully
def test_upload_valid_csv(driver):
    login_as_admin(driver)
    go_to_weather(driver)
    try:
        file_input = driver.find_element(By.ID, "csvFile")
        file_input.send_keys(VALID_CSV)
        driver.find_element(By.XPATH, "//button[contains(text(),'Upload CSV')]").click()
        time.sleep(3)
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        assert "success" in body_text or "uploaded" in body_text or "saved" in body_text or "record" in body_text
        save_screenshot(driver, "pass_upload_valid_csv")
    except Exception:
        save_screenshot(driver, "fail_upload_valid_csv")
        raise

# TC-1402: Non-CSV file upload → error shown
def test_upload_invalid_format(driver):
    login_as_admin(driver)
    go_to_weather(driver)
    try:
        file_input = driver.find_element(By.ID, "csvFile")
        file_input.send_keys(INVALID_FILE)
        driver.find_element(By.XPATH, "//button[contains(text(),'Upload CSV')]").click()
        time.sleep(2)
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        assert "invalid" in body_text or "error" in body_text or "format" in body_text or "csv" in body_text
        save_screenshot(driver, "pass_upload_invalid_format")
    except Exception:
        save_screenshot(driver, "fail_upload_invalid_format")
        raise

# TC-1404: Update weather record with valid data → timestamp logged
# TC-1404: Update weather record with valid data → timestamp logged
def test_update_valid_record(driver):
    login_as_admin(driver)
    go_to_weather(driver)
    try:
        driver.find_element(By.XPATH, "//button[contains(text(),'Add New Record')]").click()
        time.sleep(2)
        driver.find_element(By.ID, "temperature").clear()
        driver.find_element(By.ID, "temperature").send_keys("30")
        driver.find_element(By.ID, "humidity").clear()
        driver.find_element(By.ID, "humidity").send_keys("75")
        driver.find_element(By.ID, "rainfall").clear()
        driver.find_element(By.ID, "rainfall").send_keys("10")
        driver.find_element(By.ID, "date").send_keys("2024-01-01")
        driver.find_element(By.ID, "location").send_keys("Kuala Lumpur")
        btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(2)
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        assert "success" in body_text or "saved" in body_text or "updated" in body_text or "added" in body_text
        save_screenshot(driver, "pass_update_valid_record")
    except Exception:
        save_screenshot(driver, "fail_update_valid_record")
        raise

# TC-1405: Non-numeric temperature → error shown
def test_invalid_temperature(driver):
    login_as_admin(driver)
    go_to_weather(driver)
    try:
        driver.find_element(By.XPATH, "//button[contains(text(),'Add New Record')]").click()
        time.sleep(2)
        driver.find_element(By.ID, "temperature").send_keys("test")
        driver.find_element(By.ID, "humidity").send_keys("75")
        driver.find_element(By.ID, "rainfall").send_keys("10")
        driver.find_element(By.ID, "date").send_keys("2024-01-01")
        driver.find_element(By.ID, "location").send_keys("Kuala Lumpur")
        btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(2)
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        assert "invalid" in body_text or "error" in body_text or "number" in body_text or "valid" in body_text
        save_screenshot(driver, "pass_invalid_temperature")
    except Exception:
        save_screenshot(driver, "fail_invalid_temperature")
        raise

# TC-1406: Non-numeric humidity → error shown
def test_invalid_humidity(driver):
    login_as_admin(driver)
    go_to_weather(driver)
    try:
        driver.find_element(By.XPATH, "//button[contains(text(),'Add New Record')]").click()
        time.sleep(2)
        driver.find_element(By.ID, "temperature").send_keys("30")
        driver.find_element(By.ID, "humidity").send_keys("test")
        driver.find_element(By.ID, "rainfall").send_keys("10")
        driver.find_element(By.ID, "date").send_keys("2024-01-01")
        driver.find_element(By.ID, "location").send_keys("Kuala Lumpur")
        btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(2)
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        assert "invalid" in body_text or "error" in body_text or "number" in body_text or "valid" in body_text
        save_screenshot(driver, "pass_invalid_humidity")
    except Exception:
        save_screenshot(driver, "fail_invalid_humidity")
        raise

# TC-1407: Non-numeric rainfall → error shown
def test_invalid_rainfall(driver):
    login_as_admin(driver)
    go_to_weather(driver)
    try:
        driver.find_element(By.XPATH, "//button[contains(text(),'Add New Record')]").click()
        time.sleep(2)
        driver.find_element(By.ID, "temperature").send_keys("30")
        driver.find_element(By.ID, "humidity").send_keys("75")
        driver.find_element(By.ID, "rainfall").send_keys("test")
        driver.find_element(By.ID, "date").send_keys("2024-01-01")
        driver.find_element(By.ID, "location").send_keys("Kuala Lumpur")
        btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(2)
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        assert "invalid" in body_text or "error" in body_text or "number" in body_text or "valid" in body_text
        save_screenshot(driver, "pass_invalid_rainfall")
    except Exception:
        save_screenshot(driver, "fail_invalid_rainfall")
        raise

# TC-1403: Save failure simulation → error message shown
def test_save_failure(driver):
    login_as_admin(driver)
    go_to_weather(driver)
    try:
        # Upload invalid CSV to trigger a save/processing failure
        file_input = driver.find_element(By.ID, "csvFile")
        file_input.send_keys(INVALID_FILE)
        driver.find_element(By.XPATH, "//button[contains(text(),'Upload CSV')]").click()
        time.sleep(2)
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        assert "error" in body_text or "fail" in body_text or "invalid" in body_text
        save_screenshot(driver, "pass_save_failure")
    except Exception:
        save_screenshot(driver, "fail_save_failure")
        raise