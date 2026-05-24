import unittest

from html_runner import make_runner
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = "http://localhost:3000"

ADMIN_EMAIL    = "admin1@drone4dengue.com"
ADMIN_PASSWORD = "adminpass1"

TIMEOUT = 20

FILTER_LOCATION   = "England"
FILTER_START_DATE = "2023-01-01"
FILTER_END_DATE   = "2023-01-02"


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


def set_date_input(driver: webdriver.Chrome, element, date_value: str) -> None:
    driver.execute_script(
        """
        var nativeSetter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value'
        ).set;
        nativeSetter.call(arguments[0], arguments[1]);
        arguments[0].dispatchEvent(new Event('input',  { bubbles: true }));
        arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
        """,
        element,
        date_value,
    )


class TC08004NoMatchingRecords(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.driver = build_driver()
        cls.wait   = WebDriverWait(cls.driver, TIMEOUT)
        login(cls.driver, cls.wait)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_A_initial_state_shows_no_data_displayed(self):
        go_to_data_management(self.driver, self.wait)

        no_data_el = self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//*[contains(text(), 'No Data Displayed')]")
            )
        )
        self.assertTrue(
            no_data_el.is_displayed(),
            "Expected 'No Data Displayed' placeholder before any search is applied",
        )

        filter_heading = self.driver.find_element(
            By.XPATH, "//*[contains(text(), 'Data Filters')]"
        )
        self.assertTrue(filter_heading.is_displayed(), "'Data Filters' section not visible")

        date_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='date']")
        self.assertGreaterEqual(
            len(date_inputs), 2,
            f"Expected at least 2 date inputs, found {len(date_inputs)}",
        )

        location_input = self.driver.find_element(
            By.XPATH, "//input[@placeholder[contains(., 'Enter Country')]]"
        )
        self.assertTrue(location_input.is_displayed(), "Location text input not visible")

        search_btn = self.driver.find_element(
            By.XPATH, "//button[contains(., 'Search Data')]"
        )
        self.assertTrue(search_btn.is_enabled(), "'Search Data' button not enabled")

        print("\n[PASS] TC-08-004-A: Page loads in 'No Data Displayed' state.")

    def test_B_search_transitions_away_from_initial_placeholder(self):
        go_to_data_management(self.driver, self.wait)

        date_inputs = self.wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[type='date']"))
        )
        start_input = date_inputs[0]
        end_input   = date_inputs[1]

        set_date_input(self.driver, start_input, FILTER_START_DATE)
        set_date_input(self.driver, end_input,   FILTER_END_DATE)

        self.assertEqual(
            start_input.get_attribute("value"), FILTER_START_DATE,
            f"Date Start input did not accept '{FILTER_START_DATE}'",
        )
        self.assertEqual(
            end_input.get_attribute("value"), FILTER_END_DATE,
            f"Date End input did not accept '{FILTER_END_DATE}'",
        )

        location_input = self.driver.find_element(
            By.XPATH, "//input[@placeholder[contains(., 'Enter Country')]]"
        )
        location_input.clear()
        location_input.send_keys(FILTER_LOCATION)
        self.assertEqual(
            location_input.get_attribute("value"), FILTER_LOCATION,
            f"Location input did not accept '{FILTER_LOCATION}'",
        )

        self.driver.find_element(
            By.XPATH, "//button[contains(., 'Search Data')]"
        ).click()

        self.wait.until(
            EC.invisibility_of_element_located(
                (By.XPATH, "//*[contains(text(), 'No Data Displayed')]")
            )
        )

        still_visible = [
            el for el in self.driver.find_elements(
                By.XPATH, "//*[contains(text(), 'No Data Displayed')]"
            )
            if el.is_displayed()
        ]
        self.assertEqual(
            len(still_visible), 0,
            "'No Data Displayed' placeholder is still visible after clicking 'Search Data'",
        )

        print(
            "\n[PASS] TC-08-004-B: 'No Data Displayed' placeholder correctly "
            "removed after filter submission."
        )

    def test_C_no_matching_records_message_displayed(self):
        go_to_data_management(self.driver, self.wait)

        location_input = self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//input[@placeholder[contains(., 'Enter Country')]]")
            )
        )
        location_input.clear()
        location_input.send_keys(FILTER_LOCATION)

        search_btn = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Search Data')]")
            )
        )
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", search_btn)
        search_btn.click()

        self.wait.until(
            EC.invisibility_of_element_located(
                (By.XPATH, "//*[contains(text(), 'No Data Displayed')]")
            )
        )

        def table_resolved(driver):
            rows_with_text = [
                td for td in driver.find_elements(By.CSS_SELECTOR, "tbody tr td")
                if td.text.strip()
            ]
            if rows_with_text:
                return True
            for msg in ("No Records Found", "No Data Displayed"):
                els = driver.find_elements(
                    By.XPATH, f"//*[contains(text(), '{msg}')]"
                )
                if els and els[0].is_displayed():
                    return True
            return False

        self.wait.until(
            table_resolved,
            message=(
                "Table did not resolve after clicking 'Search Data'. "
                "Ensure the API server is running."
            ),
        )

        no_records_elements = self.driver.find_elements(
            By.XPATH, "//*[contains(text(), 'No Records Found')]"
        )
        visible_no_records = [el for el in no_records_elements if el.is_displayed()]

        self.assertGreater(
            len(visible_no_records), 0,
            (
                f"Expected 'No Records Found' message for "
                f"Location='{FILTER_LOCATION}', but it was not displayed."
            ),
        )

        subtitle_elements = self.driver.find_elements(
            By.XPATH,
            "//*[contains(text(), 'No dengue data matches your current filters')]"
        )
        visible_subtitle = [el for el in subtitle_elements if el.is_displayed()]
        self.assertGreater(
            len(visible_subtitle), 0,
            "Expected the subtitle 'No dengue data matches your current filters.' "
            "to be visible alongside 'No Records Found', but it was not found.",
        )

        data_rows = [
            row for row in self.driver.find_elements(By.CSS_SELECTOR, "tbody tr")
            if row.is_displayed() and len(row.find_elements(By.TAG_NAME, "td")) > 1
            and row.find_elements(By.TAG_NAME, "td")[0].text.strip()
        ]
        self.assertEqual(
            len(data_rows), 0,
            f"Expected 0 data rows but found {len(data_rows)} — the database "
            f"may contain 'England' records.",
        )

        print(
            "\n[PASS] TC-08-004-C: 'No Records Found' displayed correctly for "
            f"Location='{FILTER_LOCATION}' (no date filter)."
        )


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromTestCase(TC08004NoMatchingRecords)

    runner = make_runner(
        report_name="TC-08-004-NoMatchingRecords",
        report_title="TP-08-004 | Filter Returns No Matching Records Test Report",
    )
    runner.run(suite)
