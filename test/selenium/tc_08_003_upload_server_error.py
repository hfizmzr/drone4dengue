import os
import time
import unittest

from html_runner import make_runner
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = "http://localhost:3000"
API_URL  = "http://localhost:4000"

ADMIN_EMAIL    = "admin1@drone4dengue.com"
ADMIN_PASSWORD = "adminpass1"

TIMEOUT = 20

_DIR      = os.path.dirname(os.path.abspath(__file__))
CSV_PATH  = os.path.join(_DIR, "fixtures", "dengue_records.csv")

UPLOAD_ENDPOINT = f"{API_URL}/dengue-data/upload"


def build_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1440,900")
    return webdriver.Chrome(options=opts)


def login(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    driver.get(BASE_URL)
    email_field = wait.until(EC.presence_of_element_located((By.ID, "email")))
    password_field = driver.find_element(By.ID, "password")
    email_field.clear()
    email_field.send_keys(ADMIN_EMAIL)
    password_field.clear()
    password_field.send_keys(ADMIN_PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    wait.until(EC.url_contains("/dashboard"))


def go_to_data_management(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    driver.get(f"{BASE_URL}/data-management")
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//h1[contains(text(), 'Data Management')]")
        )
    )


def block_upload_endpoint(driver: webdriver.Chrome) -> None:
    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd(
        "Network.setBlockedURLs",
        {"urls": [UPLOAD_ENDPOINT]}
    )


def unblock_upload_endpoint(driver: webdriver.Chrome) -> None:
    driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": []})


class TC08003UploadServerError(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.driver = build_driver()
        cls.wait   = WebDriverWait(cls.driver, TIMEOUT)
        login(cls.driver, cls.wait)

    @classmethod
    def tearDownClass(cls):
        try:
            unblock_upload_endpoint(cls.driver)
        except Exception:
            pass
        cls.driver.quit()

    def _upload_with_blocked_api(self) -> None:
        go_to_data_management(self.driver, self.wait)

        block_upload_endpoint(self.driver)

        self.assertTrue(
            os.path.isfile(CSV_PATH),
            f"Test fixture not found: {CSV_PATH}"
        )

        file_input = self.wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[type='file'][accept='.csv']")
            )
        )
        self.driver.execute_script(
            "arguments[0].style.display = 'block'; "
            "arguments[0].style.opacity = '1';",
            file_input
        )
        file_input.send_keys(CSV_PATH)

    def test_A_server_error_shows_red_error_banner(self):
        try:
            self._upload_with_blocked_api()

            self.wait.until(
                EC.text_to_be_present_in_element(
                    (By.XPATH, "//button[contains(., 'Upload Data') or "
                               "contains(., 'Uploading...')]"),
                    "Upload Data"
                )
            )

            error_banner = self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH,
                     "//*[contains(@class,'text-red-700') and "
                     "contains(@class,'bg-red-50')]")
                )
            )
            banner_text = error_banner.text.strip()

            self.assertTrue(
                banner_text.startswith("✗"),
                f"Error banner does not start with '✗'. Got: '{banner_text}'"
            )

            classes = error_banner.get_attribute("class") or ""
            self.assertIn(
                "text-red-700", classes,
                f"Error banner missing 'text-red-700' class. Classes: '{classes}'"
            )
            self.assertIn(
                "bg-red-50", classes,
                f"Error banner missing 'bg-red-50' class. Classes: '{classes}'"
            )
            self.assertIn(
                "border-red-200", classes,
                f"Error banner missing 'border-red-200' class. Classes: '{classes}'"
            )

            print(
                f"\n[PASS] TC-08-003-A: Red error banner displayed. "
                f"Message: '{banner_text}'"
            )

        finally:
            unblock_upload_endpoint(self.driver)

    def test_B_upload_button_re_enabled_after_error(self):
        try:
            self._upload_with_blocked_api()

            upload_btn = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(., 'Upload Data')]")
                )
            )

            btn_text = upload_btn.text.strip()
            self.assertIn(
                "Upload Data", btn_text,
                f"Button text should be 'Upload Data' after error, got: '{btn_text}'"
            )

            self.assertTrue(
                upload_btn.is_enabled(),
                "Upload Data button is still disabled after the upload error"
            )

            btn_classes = upload_btn.get_attribute("class") or ""
            self.assertNotIn(
                "cursor-not-allowed", btn_classes,
                f"Button still has 'cursor-not-allowed' class after error: '{btn_classes}'"
            )

            print(
                "\n[PASS] TC-08-003-B: 'Upload Data' button is re-enabled and "
                "interactive after the server error."
            )

        finally:
            unblock_upload_endpoint(self.driver)

    def test_C_no_success_banner_on_server_error(self):
        try:
            self._upload_with_blocked_api()

            self.wait.until(
                EC.text_to_be_present_in_element(
                    (By.XPATH, "//button[contains(., 'Upload Data') or "
                               "contains(., 'Uploading...')]"),
                    "Upload Data"
                )
            )

            success_banners = self.driver.find_elements(
                By.XPATH,
                "//*[contains(@class,'text-green-700') and "
                "contains(@class,'bg-green-50') and "
                "contains(., 'Successfully imported')]"
            )
            visible_success = [el for el in success_banners if el.is_displayed()]
            self.assertEqual(
                len(visible_success), 0,
                f"A green success banner appeared despite the server error: "
                f"{[el.text for el in visible_success]}"
            )

            error_banners = self.driver.find_elements(
                By.XPATH,
                "//*[contains(@class,'text-red-700') and "
                "contains(@class,'bg-red-50')]"
            )
            visible_errors = [el for el in error_banners if el.is_displayed()]
            self.assertGreater(
                len(visible_errors), 0,
                "Expected a red error banner to be present, but none was found"
            )

            print(
                "\n[PASS] TC-08-003-C: No false-positive success banner shown. "
                f"Error banner present: '{visible_errors[0].text.strip()}'"
            )

        finally:
            unblock_upload_endpoint(self.driver)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromTestCase(TC08003UploadServerError)

    runner = make_runner(
        report_name="TC-08-003-UploadServerError",
        report_title="TP-08-003 | CSV Upload Server Error Test Report",
    )
    runner.run(suite)
