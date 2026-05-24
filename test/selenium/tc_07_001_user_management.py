import time
import unittest

from html_runner import make_runner

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL   = "http://localhost:3000"
API_URL    = "http://localhost:4000"

ADMIN_EMAIL    = "admin1@drone4dengue.com"
ADMIN_PASSWORD = "adminpass1"

TIMEOUT = 15


def build_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1440,900")
    return webdriver.Chrome(options=opts)


def login(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    driver.get(BASE_URL)

    email_field = wait.until(
        EC.presence_of_element_located((By.ID, "email"))
    )
    password_field = driver.find_element(By.ID, "password")

    email_field.clear()
    email_field.send_keys(ADMIN_EMAIL)
    password_field.clear()
    password_field.send_keys(ADMIN_PASSWORD)

    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    wait.until(EC.url_contains("/dashboard"))


def go_to_user_management(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    driver.get(f"{BASE_URL}/user-management")
    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//h1[contains(text(), 'User Management')]")
        )
    )


def block_api_requests(driver: webdriver.Chrome) -> None:
    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd(
        "Network.setBlockedURLs",
        {"urls": [f"{API_URL}/*"]}
    )


def unblock_api_requests(driver: webdriver.Chrome) -> None:
    driver.execute_cdp_cmd(
        "Network.setBlockedURLs",
        {"urls": []}
    )


class TC07001UserManagement(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.driver = build_driver()
        cls.wait   = WebDriverWait(cls.driver, TIMEOUT)
        login(cls.driver, cls.wait)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_A_user_list_loads_under_normal_conditions(self):
        go_to_user_management(self.driver, self.wait)

        heading = self.wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//h1[contains(text(), 'User Management')]")
            )
        )
        self.assertTrue(heading.is_displayed(), "Page heading 'User Management' not visible")

        stat_labels = ["Total Users", "Active Users", "Pending Users", "Admin Users"]
        for label in stat_labels:
            card = self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, f"//*[contains(text(), '{label}')]")
                )
            )
            self.assertTrue(card.is_displayed(), f"Stat card '{label}' not visible")

        self.wait.until(
            EC.invisibility_of_element_located(
                (By.XPATH, "//*[contains(text(), 'Loading users...')]")
            )
        )

        error_elements = self.driver.find_elements(
            By.XPATH, "//*[contains(@class, 'text-red-600')]"
        )
        visible_errors = [el for el in error_elements if el.is_displayed() and el.text.strip()]
        self.assertEqual(
            len(visible_errors), 0,
            f"Unexpected error message(s) displayed: {[e.text for e in visible_errors]}"
        )

        expected_headers = ["User ID", "User", "Address", "Role", "Status", "Actions"]
        for header in expected_headers:
            col = self.driver.find_element(
                By.XPATH, f"//th[contains(text(), '{header}')]"
            )
            self.assertTrue(col.is_displayed(), f"Table column '{header}' not found")

        self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tbody tr"))
        )
        rows = self.driver.find_elements(By.CSS_SELECTOR, "tbody tr")
        self.assertGreater(len(rows), 0, "User list table contains no rows")

        search_input = self.driver.find_element(
            By.XPATH, "//input[@placeholder='Search users...']"
        )
        self.assertTrue(search_input.is_displayed(), "Search input not visible")

        toolbar_buttons = self.driver.find_elements(
            By.CSS_SELECTOR, ".bg-accent-blue.rounded-t-xl button"
        )
        self.assertGreaterEqual(
            len(toolbar_buttons), 2,
            "Expected at least Add (+) and Filter buttons in the toolbar"
        )

        print("\n[PASS] TC-07-001-A: User list loaded with table, stats, search and filter.")

    def test_B_error_message_shown_when_api_unavailable(self):
        block_api_requests(self.driver)

        try:
            self.driver.get(f"{BASE_URL}/user-management")

            self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//h1[contains(text(), 'User Management')]")
                )
            )

            self.wait.until(
                EC.invisibility_of_element_located(
                    (By.XPATH, "//*[contains(text(), 'Loading users...')]")
                )
            )

            error_element = self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//*[contains(@class, 'text-red-600') and string-length(normalize-space(text())) > 0]")
                )
            )
            error_text = error_element.text.strip()

            self.assertTrue(
                len(error_text) > 0,
                "Error element found but contains no visible text"
            )

            self.assertIn(
                "Failed to fetch",
                error_text,
                f"Expected 'Failed to fetch' in error message, got: '{error_text}'"
            )

            rows = self.driver.find_elements(By.CSS_SELECTOR, "tbody tr")
            self.assertEqual(
                len(rows), 0,
                f"Expected empty table on error, but found {len(rows)} row(s)"
            )

            print(f"\n[PASS] TC-07-001-B: Error message displayed: '{error_text}'")

        finally:
            unblock_api_requests(self.driver)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromTestCase(TC07001UserManagement)

    runner = make_runner(
        report_name="TC-07-001-UserManagement",
        report_title="TP-07-001 | User Management Test Report",
    )
    runner.run(suite)
