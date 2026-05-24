import os
import time
import unittest
from datetime import datetime

from html_runner import make_runner
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = "http://localhost:3000"
API_URL  = "http://localhost:4000"

ADMIN_EMAIL    = "admin1@drone4dengue.com"
ADMIN_PASSWORD = "adminpass1"

TIMEOUT = 20

FILTER_LOCATION   = "Kuala Lumpur"
FILTER_START_DATE = "2024-01-01"
FILTER_END_DATE   = "2024-06-30"


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


class TC08002FilterData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.driver = build_driver()
        cls.wait   = WebDriverWait(cls.driver, TIMEOUT)
        login(cls.driver, cls.wait)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_A_filter_panel_elements_present(self):
        go_to_data_management(self.driver, self.wait)

        filter_heading = self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//*[contains(text(), 'Data Filters')]")
            )
        )
        self.assertTrue(filter_heading.is_displayed(), "'Data Filters' heading not visible")

        date_start_label = self.driver.find_element(
            By.XPATH, "//label[contains(text(), 'Date Start')]"
        )
        self.assertTrue(date_start_label.is_displayed(), "'Date Start' label not visible")

        date_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='date']")
        self.assertGreaterEqual(
            len(date_inputs), 2,
            f"Expected at least 2 date inputs, found {len(date_inputs)}"
        )
        for inp in date_inputs[:2]:
            self.assertTrue(inp.is_displayed(), "A date input is not visible")

        date_end_label = self.driver.find_element(
            By.XPATH, "//label[contains(text(), 'Date End')]"
        )
        self.assertTrue(date_end_label.is_displayed(), "'Date End' label not visible")

        cases_type_select = self.driver.find_element(
            By.XPATH,
            "//label[contains(text(), 'Cases Type')]"
            "/following-sibling::select | "
            "//label[contains(text(), 'Cases Type')]"
            "/..//select"
        )
        self.assertTrue(cases_type_select.is_displayed(), "'Cases Type' select not visible")

        location_input = self.driver.find_element(
            By.XPATH,
            "//input[@placeholder[contains(., 'Enter Country')]]"
        )
        self.assertTrue(location_input.is_displayed(), "Location text input not visible")

        search_btn = self.driver.find_element(
            By.XPATH, "//button[contains(., 'Search Data')]"
        )
        self.assertTrue(search_btn.is_displayed(), "'Search Data' button not visible")
        self.assertTrue(search_btn.is_enabled(),   "'Search Data' button not enabled")

        clear_btn = self.driver.find_element(
            By.XPATH, "//button[contains(., 'Clear Filters')]"
        )
        self.assertTrue(clear_btn.is_displayed(), "'Clear Filters' button not visible")

        no_data_msg = self.driver.find_element(
            By.XPATH, "//*[contains(text(), 'No Data Displayed')]"
        )
        self.assertTrue(
            no_data_msg.is_displayed(),
            "Expected 'No Data Displayed' placeholder before first search"
        )

        print("\n[PASS] TC-08-002-A: Filter panel has all required elements in initial state.")

    def test_B_filter_search_transitions_table_state(self):
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
            f"Date Start input did not accept '{FILTER_START_DATE}'"
        )
        self.assertEqual(
            end_input.get_attribute("value"), FILTER_END_DATE,
            f"Date End input did not accept '{FILTER_END_DATE}'"
        )

        location_input = self.driver.find_element(
            By.XPATH,
            "//input[@placeholder[contains(., 'Enter Country')]]"
        )
        location_input.clear()
        location_input.send_keys(FILTER_LOCATION)
        self.assertEqual(
            location_input.get_attribute("value"), FILTER_LOCATION,
            f"Location input did not accept '{FILTER_LOCATION}'"
        )

        search_btn = self.driver.find_element(
            By.XPATH, "//button[contains(., 'Search Data')]"
        )
        search_btn.click()

        self.wait.until(
            EC.invisibility_of_element_located(
                (By.XPATH, "//*[contains(text(), 'No Data Displayed')]")
            )
        )

        self.wait.until(
            lambda d: (
                len(d.find_elements(By.CSS_SELECTOR, "tbody tr td[colspan]")) > 0 or
                len(d.find_elements(By.CSS_SELECTOR, "tbody tr:not([class*='animate'])")) > 0
            )
        )

        initial_placeholder = self.driver.find_elements(
            By.XPATH, "//*[contains(text(), 'No Data Displayed')]"
        )
        visible_initial = [el for el in initial_placeholder if el.is_displayed()]
        self.assertEqual(
            len(visible_initial), 0,
            "'No Data Displayed' is still visible after clicking Search Data"
        )

        no_records_msgs = self.driver.find_elements(
            By.XPATH, "//*[contains(text(), 'No Records Found')]"
        )
        data_rows = self.driver.find_elements(By.CSS_SELECTOR, "tbody tr")

        has_no_records_msg = any(el.is_displayed() for el in no_records_msgs)
        has_data_rows      = any(
            row.is_displayed() and not row.get_attribute("class", ) and
            len(row.find_elements(By.TAG_NAME, "td")) > 1
            for row in data_rows
        )

        self.assertTrue(
            has_no_records_msg or has_data_rows,
            "After Search Data the table shows neither records nor a 'No Records Found' message"
        )

        outcome = "records found" if has_data_rows else "'No Records Found' message shown"
        print(
            f"\n[PASS] TC-08-002-B: Filter applied — table transitioned correctly "
            f"({outcome})."
        )

    def test_C_returned_rows_match_date_range_and_clear_resets(self):
        go_to_data_management(self.driver, self.wait)

        date_inputs = self.wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[type='date']"))
        )
        set_date_input(self.driver, date_inputs[0], FILTER_START_DATE)
        set_date_input(self.driver, date_inputs[1], FILTER_END_DATE)

        location_input = self.driver.find_element(
            By.XPATH, "//input[@placeholder[contains(., 'Enter Country')]]"
        )
        location_input.clear()
        location_input.send_keys(FILTER_LOCATION)

        self.driver.find_element(
            By.XPATH, "//button[contains(., 'Search Data')]"
        ).click()

        self.wait.until(
            EC.invisibility_of_element_located(
                (By.XPATH, "//*[contains(text(), 'No Data Displayed')]")
            )
        )
        self.wait.until(
            lambda d: (
                len(d.find_elements(By.CSS_SELECTOR, "tbody tr td[colspan]")) > 0 or
                len(d.find_elements(By.CSS_SELECTOR, "tbody tr:not([class*='animate'])")) > 0
            )
        )

        start_dt = datetime.strptime(FILTER_START_DATE, "%Y-%m-%d")
        end_dt   = datetime.strptime(FILTER_END_DATE,   "%Y-%m-%d")

        data_rows = self.driver.find_elements(By.CSS_SELECTOR, "tbody tr")
        record_rows = [
            row for row in data_rows
            if row.is_displayed() and len(row.find_elements(By.TAG_NAME, "td")) > 1
        ]

        if record_rows:
            out_of_range = []
            for row in record_rows:
                date_cell = row.find_elements(By.TAG_NAME, "td")
                if not date_cell:
                    continue
                raw_date = date_cell[0].text.strip()
                for part in raw_date.split():
                    try:
                        row_dt = datetime.strptime(part, "%d/%m/%Y")
                        if not (start_dt <= row_dt <= end_dt):
                            out_of_range.append(part)
                        break
                    except ValueError:
                        continue

            self.assertEqual(
                len(out_of_range), 0,
                f"Row(s) with dates outside {FILTER_START_DATE} – {FILTER_END_DATE}: "
                f"{out_of_range}"
            )
            print(
                f"\n[PASS] TC-08-002-C (part 1): {len(record_rows)} record(s) returned, "
                f"all within the specified date range."
            )
        else:
            print(
                "\n[INFO] TC-08-002-C (part 1): No matching records for "
                f"Location='{FILTER_LOCATION}' / {FILTER_START_DATE} – {FILTER_END_DATE}; "
                "date-range validation skipped."
            )

        clear_btn = self.driver.find_element(
            By.XPATH, "//button[contains(., 'Clear Filters')]"
        )
        clear_btn.click()

        date_inputs_after = self.driver.find_elements(
            By.CSS_SELECTOR, "input[type='date']"
        )
        for inp in date_inputs_after:
            self.assertEqual(
                inp.get_attribute("value"), "",
                f"Date input was not cleared after 'Clear Filters'; still has '{inp.get_attribute('value')}'"
            )

        location_after = self.driver.find_element(
            By.XPATH, "//input[@placeholder[contains(., 'Enter Country')]]"
        )
        self.assertEqual(
            location_after.get_attribute("value"), "",
            f"Location input was not cleared; still has '{location_after.get_attribute('value')}'"
        )

        no_data_msg = self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//*[contains(text(), 'No Data Displayed')]")
            )
        )
        self.assertTrue(
            no_data_msg.is_displayed(),
            "'No Data Displayed' placeholder did not reappear after Clear Filters"
        )

        print(
            "\n[PASS] TC-08-002-C (part 2): Clear Filters reset all inputs and "
            "returned the table to 'No Data Displayed' state."
        )


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromTestCase(TC08002FilterData)

    runner = make_runner(
        report_name="TC-08-002-FilterData",
        report_title="TP-08-002 | Filter by Location & Date Range Test Report",
    )
    runner.run(suite)
