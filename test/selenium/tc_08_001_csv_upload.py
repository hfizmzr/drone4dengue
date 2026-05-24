import os
import tempfile
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

TIMEOUT = 25

VALID_CSV_CONTENT = (
    "date,location,activeCases,totalCases,coverageArea,status,latitude,longitude\n"
    "2024-03-10,Chow Kit Kuala Lumpur,5,12,Chow Kit,Active Cases,3.1621,101.6965\n"
    "2024-03-11,Damansara Petaling Jaya,3,8,Damansara,Hotspot,3.1332,101.6261\n"
    "2024-03-12,Seksyen 7 Shah Alam,7,15,Seksyen 7,Active Cases,3.0849,101.5329\n"
)


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


def create_temp_csv() -> str:
    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".csv",
        prefix="dengue_records_",
        delete=False,
        encoding="utf-8",
    )
    tmp.write(VALID_CSV_CONTENT)
    tmp.close()
    return tmp.name


class TC08001CSVUpload(unittest.TestCase):

    _csv_path: str = ""

    @classmethod
    def setUpClass(cls):
        cls.driver = build_driver()
        cls.wait   = WebDriverWait(cls.driver, TIMEOUT)
        cls._csv_path = create_temp_csv()
        login(cls.driver, cls.wait)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        if cls._csv_path and os.path.exists(cls._csv_path):
            try:
                os.unlink(cls._csv_path)
            except OSError:
                pass

    def setUp(self):
        go_to_data_management(self.driver, self.wait)

    def test_A_upload_valid_csv_shows_success_confirmation(self):
        import re

        file_input = self.wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[type='file'][accept='.csv']")
            )
        )
        self.driver.execute_script(
            "arguments[0].style.cssText = 'display:block; visibility:visible;';",
            file_input,
        )
        file_input.send_keys(self._csv_path)

        def upload_message_present(driver):
            for xpath in [
                "//*[contains(text(), 'Successfully imported')]",
                "//*[contains(text(), 'Upload failed')]",
                "//*[starts-with(normalize-space(text()), '✗')]",
            ]:
                els = driver.find_elements(By.XPATH, xpath)
                if els and els[0].is_displayed():
                    return els[0]
            return False

        msg_el = self.wait.until(
            upload_message_present,
            message=(
                "No upload-response message appeared within the timeout. "
                "Ensure the API server is running at " + API_URL
            ),
        )

        banner_text = msg_el.text.strip()

        self.assertIn(
            "Successfully imported",
            banner_text,
            (
                f"Expected a success confirmation but got: '{banner_text}'. "
                f"Check that the API at {API_URL} is running and accepting uploads."
            ),
        )

        banner_container = self.driver.find_element(
            By.XPATH,
            "//*[contains(text(), 'Successfully imported')]/.."
        )
        container_classes = banner_container.get_attribute("class") or ""
        self.assertIn(
            "green",
            container_classes,
            (
                f"Success banner container should have green styling. "
                f"Classes found: '{container_classes}'"
            ),
        )

        match = re.search(r"imported:\s*(\d+)", banner_text)
        if match is None:
            self.fail(
                f"Could not parse imported count from banner: '{banner_text}'"
            )
        imported_count = int(match.group(1))
        self.assertGreater(
            imported_count,
            0,
            f"Expected at least 1 imported record, got {imported_count}",
        )

        print(
            f"\n[PASS] TC-08-001-A: CSV accepted. "
            f"Confirmation: '{banner_text}' (imported={imported_count})"
        )

    def test_B_dashboard_statistics_update_after_search(self):
        search_btn = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Search Data')]")
            )
        )
        search_btn.click()

        time.sleep(0.8)

        def table_has_resolved(driver):
            rows_with_text = [
                r for r in driver.find_elements(By.CSS_SELECTOR, "tbody tr td")
                if r.text.strip()
            ]
            if rows_with_text:
                return True
            for msg in ["No Records Found", "No Data Displayed"]:
                els = driver.find_elements(
                    By.XPATH, f"//*[contains(text(), '{msg}')]"
                )
                if els and els[0].is_displayed():
                    return True
            return False

        self.wait.until(
            table_has_resolved,
            message=(
                "Data table did not resolve after clicking 'Search Data'. "
                "Ensure the API server is running at " + API_URL
            ),
        )

        expected_labels = [
            "Total Records",
            "Active Cases",
            "Dengue Hotspots",
            "Locations Covered",
        ]
        for label in expected_labels:
            card_label = self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, f"//*[contains(text(), '{label}')]")
                )
            )
            self.assertTrue(
                card_label.is_displayed(),
                f"Stat card label '{label}' is not visible after search",
            )

        stat_value_elements = self.driver.find_elements(
            By.XPATH,
            "//div[contains(@class,'text-3xl') and contains(@class,'font-bold')]",
        )
        self.assertGreaterEqual(
            len(stat_value_elements),
            4,
            (
                f"Expected at least 4 stat-value elements, "
                f"found {len(stat_value_elements)}"
            ),
        )

        import re as _re
        for el in stat_value_elements[:4]:
            raw = el.text.strip()
            numeric = _re.sub(r"[,\s]", "", raw)
            self.assertTrue(
                numeric.isdigit(),
                f"Stat value '{raw}' is not a non-negative integer",
            )

        self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tbody tr"))
        )
        rows = self.driver.find_elements(By.CSS_SELECTOR, "tbody tr")
        self.assertGreater(
            len(rows),
            0,
            "Data records table is empty after search — expected at least one row",
        )

        expected_headers = [
            "Date",
            "Location",
            "Active/Total Cases",
            "Type",
            "State",
            "Actions",
        ]
        for header in expected_headers:
            col = self.driver.find_element(
                By.XPATH, f"//th[contains(text(), '{header}')]"
            )
            self.assertTrue(
                col.is_displayed(),
                f"Table column header '{header}' not found",
            )

        print(
            f"\n[PASS] TC-08-001-B: Stats visible. "
            f"Data table shows {len(rows)} row(s). "
            f"Headers: {expected_headers}"
        )


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromTestCase(TC08001CSVUpload)

    runner = make_runner(
        report_name="TC-08-001-CSVUpload",
        report_title="TP-08-001 | CSV Upload & Dashboard Statistics Test Report",
    )
    runner.run(suite)
