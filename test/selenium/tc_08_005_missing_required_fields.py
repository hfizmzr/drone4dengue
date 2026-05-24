import os
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

TIMEOUT = 25

_DIR           = os.path.dirname(os.path.abspath(__file__))
INCOMPLETE_CSV = os.path.join(_DIR, "fixtures", "incomplete_data.csv")

FIXTURE_ROW_COUNT = 3


def build_driver() -> webdriver.Chrome:
    opts = Options()
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


def go_to_data_management(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    driver.get(f"{BASE_URL}/data-management")
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//h1[contains(text(), 'Data Management')]")
        )
    )


def upload_incomplete_csv(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    file_input = wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type='file'][accept='.csv']")
        )
    )
    driver.execute_script(
        "arguments[0].style.cssText = 'display:block; visibility:visible;';",
        file_input,
    )
    file_input.send_keys(INCOMPLETE_CSV)

    def upload_banner_present(d):
        for xpath in [
            "//*[contains(text(), 'Successfully imported')]",
            "//*[contains(text(), 'Upload failed')]",
            "//*[starts-with(normalize-space(text()), '✗')]",
        ]:
            els = d.find_elements(By.XPATH, xpath)
            if els and els[0].is_displayed():
                return els[0]
        return False

    wait.until(
        upload_banner_present,
        message=(
            "No upload-response banner appeared within the timeout. "
            f"Ensure the API server is running at {API_URL}."
        ),
    )


class TC08005MissingRequiredFields(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.driver = build_driver()
        cls.wait   = WebDriverWait(cls.driver, TIMEOUT)
        login(cls.driver, cls.wait)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def setUp(self):
        self.assertTrue(
            os.path.isfile(INCOMPLETE_CSV),
            f"Test fixture not found: {INCOMPLETE_CSV}",
        )
        go_to_data_management(self.driver, self.wait)

    def test_A_upload_shows_zero_imported_with_errors(self):
        import re

        upload_incomplete_csv(self.driver, self.wait)

        banner = self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//*[contains(text(), 'Successfully imported')]")
            )
        )
        banner_text = banner.text.strip()

        match_imported = re.search(r"imported:\s*(\d+)", banner_text)
        self.assertIsNotNone(
            match_imported,
            f"Could not parse imported count from banner: '{banner_text}'",
        )
        imported_count = int(match_imported.group(1))
        self.assertEqual(
            imported_count, 0,
            f"Expected 0 imported records for the incomplete CSV, "
            f"got {imported_count}. Banner: '{banner_text}'",
        )

        match_errors = re.search(r"\((\d+)\s+error", banner_text)
        self.assertIsNotNone(
            match_errors,
            f"Expected '(N errors encountered)' in banner but got: '{banner_text}'. "
            f"The missing 'location' field should cause per-row Prisma errors.",
        )
        error_count = int(match_errors.group(1))
        self.assertGreaterEqual(
            error_count, 1,
            f"Expected at least 1 error reported, got {error_count}. "
            f"Banner: '{banner_text}'",
        )

        print(
            f"\n[PASS] TC-08-005-A: Banner correctly reports "
            f"imported=0, errors={error_count}. "
            f"Full message: '{banner_text}'"
        )

    def test_B_banner_has_green_styling(self):
        upload_incomplete_csv(self.driver, self.wait)

        banner_container = self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH,
                 "//*[contains(text(), 'Successfully imported')]/..")
            )
        )
        container_classes = banner_container.get_attribute("class") or ""

        self.assertIn(
            "green", container_classes,
            f"Expected green styling on the upload banner container. "
            f"Classes found: '{container_classes}'",
        )
        self.assertNotIn(
            "red", container_classes,
            f"Banner should not have red styling for this scenario. "
            f"Classes found: '{container_classes}'",
        )

        print(
            f"\n[PASS] TC-08-005-B: Banner has green styling as expected. "
            f"Classes: '{container_classes}'"
        )

    def test_C_upload_button_re_enabled_after_upload(self):
        upload_incomplete_csv(self.driver, self.wait)

        upload_btn = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Upload Data')]")
            )
        )

        btn_text = upload_btn.text.strip()
        self.assertIn(
            "Upload Data", btn_text,
            f"Expected button text 'Upload Data' after upload, got: '{btn_text}'",
        )

        self.assertTrue(
            upload_btn.is_enabled(),
            "Upload Data button is still disabled after the incomplete-CSV upload",
        )

        btn_classes = upload_btn.get_attribute("class") or ""
        self.assertNotIn(
            "cursor-not-allowed", btn_classes,
            f"Button still has 'cursor-not-allowed' after upload. "
            f"Classes: '{btn_classes}'",
        )

        print(
            "\n[PASS] TC-08-005-C: 'Upload Data' button is re-enabled after "
            "the incomplete CSV upload — admin can correct and re-upload."
        )


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromTestCase(TC08005MissingRequiredFields)

    runner = make_runner(
        report_name="TC-08-005-MissingRequiredFields",
        report_title="TP-08-005 | CSV Upload Missing Required Fields Test Report",
    )
    runner.run(suite)
