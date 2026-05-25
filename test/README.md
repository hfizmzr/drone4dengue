# Drone4Dengue Test Suite

## Overview

Automated black-box functional tests for the Drone4Dengue web and mobile applications. The suite uses:

- Selenium WebDriver + pytest for the admin web application.
- Appium + pytest for the Android mobile application.
- Standalone Selenium runners for UC7 and UC8.

The tested use cases match the software testing report:

| Use Case | Feature | Tooling | Test Cases | Result |
| --- | --- | --- | ---: | --- |
| UC1 | Login Account | Selenium + Appium | 9 | 7 passed, 2 failed |
| UC2 | Register Account | Selenium + Appium | 8 | 8 passed |
| UC3 | Reset Password | Selenium + Appium | 6 | 1 passed, 4 failed, 1 skipped |
| UC4 | Edit Profile | Selenium + Appium | 6 | 5 passed, 1 failed |
| UC5 | Manage Drone and Location | Selenium | 4 | 3 passed, 1 failed |
| UC6 | Manage Images Captured by Drone | Selenium | 5 | 5 passed |
| UC7 | Manage User | Selenium | 5 | 4 passed, 1 failed |
| UC8 | Manage Dengue Data | Selenium | 5 | 2 passed, 3 failed |
| UC9 | Manage Weather Data | Selenium | 7 | 3 passed, 4 failed |
| UC10 | Generate Report | Selenium | 7 | 5 passed, 2 failed |
| UC12 | Manage Settings | Selenium | 12 | 12 passed |
| UC14 | Get Recommendations | Appium | 6 | 6 passed |
| **Total** | 12 use cases | Selenium, Appium, pytest | **80** | **61 passed, 18 failed, 1 skipped (76.3%)** |

## Directory Structure

```text
test/
|-- README.md
|-- pytest.ini
|-- requirements.txt
|-- run_tests.sh
|-- run_tc07.sh
|-- run_tc08.sh
|-- appium/
|   |-- conftest.py
|   |-- helpers.py
|   |-- setup_test_account.py
|   |-- test_uc1_login_appium.py
|   |-- test_uc2_register_appium.py
|   |-- test_uc3_reset_password.py
|   |-- test_uc4_edit_profile_mobile.py
|   `-- test_uc14_get_recommendations_appium.py
|-- selenium/
|   |-- conftest.py
|   |-- html_runner.py
|   |-- setup_admin_account.js
|   |-- test_uc1_login.py
|   |-- test_uc2_register.py
|   |-- test_uc3_resetpassword.py
|   |-- test_uc4_edit_profile.py
|   |-- test_uc5_drone_management.py
|   |-- test_uc6_drone_images.py
|   |-- tc_07_001_user_management.py
|   |-- tc_07_002_003_user_add_edit.py
|   |-- tc_07_004_user_role_management.py
|   |-- tc_07_005_user_status_delete.py
|   |-- tc_07_006_edge_cases.py
|   |-- tc_08_001_csv_upload.py
|   |-- tc_08_002_filter_data.py
|   |-- tc_08_003_upload_server_error.py
|   |-- tc_08_004_no_matching_records.py
|   |-- tc_08_005_missing_required_fields.py
|   |-- test_uc09_weather.py
|   |-- test_uc10_generate_report.py
|   |-- test_uc12_manage_settings_web.py
|   |-- assets/
|   `-- fixtures/
|-- reports/
`-- test-reports/
```

## Tested Use Cases and Scripts

| Use Case | Web Selenium Script | Mobile Appium Script |
| --- | --- | --- |
| UC1 - Login Account | `selenium/test_uc1_login.py` | `appium/test_uc1_login_appium.py` |
| UC2 - Register Account | `selenium/test_uc2_register.py` | `appium/test_uc2_register_appium.py` |
| UC3 - Reset Password | `selenium/test_uc3_resetpassword.py` | `appium/test_uc3_reset_password.py` |
| UC4 - Edit Profile | `selenium/test_uc4_edit_profile.py` | `appium/test_uc4_edit_profile_mobile.py` |
| UC5 - Manage Drone and Location | `selenium/test_uc5_drone_management.py` | Not automated in this folder |
| UC6 - Manage Images Captured by Drone | `selenium/test_uc6_drone_images.py` | Not automated in this folder |
| UC7 - Manage User | `selenium/tc_07_*.py` | Not automated in this folder |
| UC8 - Manage Dengue Data | `selenium/tc_08_*.py` | Not automated in this folder |
| UC9 - Manage Weather Data | `selenium/test_uc09_weather.py` | Not automated in this folder |
| UC10 - Generate Report | `selenium/test_uc10_generate_report.py` | Not automated in this folder |
| UC12 - Manage Settings | `selenium/test_uc12_manage_settings_web.py` | Not automated in this folder |
| UC14 - Get Recommendations | Not automated in this folder | `appium/test_uc14_get_recommendations_appium.py` |

## Prerequisites

Start the application services before running tests:

```bash
# Backend API
cd ../server-api
npm install
npm run dev

# Admin web application
cd ../client-admin
npm install
npm run dev

# Mobile application
cd ../client-mobile
npm install
npx expo run:android
```

Default local URLs:

- Admin web: `http://localhost:3000`
- Backend API: `http://localhost:4000`

For Android emulators, `localhost` inside the emulator is not the host machine. Use the correct host mapping, such as `10.0.2.2`, when configuring the mobile app API URL.

## Python Environment

```bash
cd test
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
cd test
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Test Accounts

Create or seed test accounts before execution:

```bash
# Admin web test account
cd test/selenium
node setup_admin_account.js

# Mobile test account
cd ../appium
python setup_test_account.py --company-id comp-001
```

Common environment overrides:

```bash
export ADMIN_URL=http://localhost:3000
export API_URL=http://localhost:4000
export ADMIN_EMAIL=admin1@drone4dengue.com
export ADMIN_PASSWORD=adminpass1
export HEADLESS=true
```

## Running Selenium Web Tests

Run the main Selenium pytest suite:

```bash
cd test
./run_tests.sh
```

Run with a visible browser:

```bash
HEADLESS=false ./run_tests.sh
```

Run one Selenium use case directly:

```bash
python -m pytest selenium/test_uc1_login.py -v
python -m pytest selenium/test_uc2_register.py -v
python -m pytest selenium/test_uc3_resetpassword.py -v
python -m pytest selenium/test_uc4_edit_profile.py -v
python -m pytest selenium/test_uc5_drone_management.py -v
python -m pytest selenium/test_uc6_drone_images.py -v
python -m pytest selenium/test_uc09_weather.py -v
python -m pytest selenium/test_uc10_generate_report.py -v
python -m pytest selenium/test_uc12_manage_settings_web.py -v
```

HTML reports are written to `reports/`.

## Running UC7 User Management Tests

UC7 uses standalone Selenium runner files:

```bash
cd test
./run_tc07.sh
```

Run a single UC7 file by partial name:

```bash
./run_tc07.sh tc_07_001
./run_tc07.sh tc_07_004
```

HTML reports are written to `test-reports/TC-07-*.html`.

## Running UC8 Dengue Data Tests

UC8 uses standalone Selenium runner files:

```bash
cd test
./run_tc08.sh
```

Run a single UC8 file by partial name:

```bash
./run_tc08.sh tc_08_001
./run_tc08.sh tc_08_003
```

HTML reports are written to `test-reports/TC-08-*.html`.

## Running Appium Mobile Tests

Start Appium and make sure the Android emulator is running before executing mobile tests.

```bash
appium
```

Run all Appium tests:

```bash
cd test
python -m pytest -c pytest.ini appium -v --html=reports/appium_report.html --self-contained-html
```

Run one mobile use case:

```bash
python -m pytest -c pytest.ini appium/test_uc1_login_appium.py -v
python -m pytest -c pytest.ini appium/test_uc2_register_appium.py -v
python -m pytest -c pytest.ini appium/test_uc3_reset_password.py -v
python -m pytest -c pytest.ini appium/test_uc4_edit_profile_mobile.py -v
python -m pytest -c pytest.ini appium/test_uc14_get_recommendations_appium.py -v
```

Generate an HTML report for one Appium use case:

```bash
python -m pytest -c pytest.ini appium/test_uc14_get_recommendations_appium.py -v --html=reports/uc14_appium_report.html --self-contained-html
```

## Assets and Fixtures

The Selenium tests use files from:

- `selenium/assets/` for upload and media tests.
- `selenium/fixtures/` for dengue data CSV tests.

Important files include:

- `selenium/assets/test_image.jpg`
- `selenium/assets/test_image.png`
- `selenium/assets/test_video.mp4`
- `selenium/assets/test_document.pdf`
- `selenium/fixtures/dengue_records.csv`
- `selenium/fixtures/incomplete_data.csv`

## Notes

- UC3 reset-password failures are linked to email/reset-code backend configuration.
- UC7, UC8, UC9, and UC10 contain documented failing cases from the report and should be reviewed against the linked incident reports.
- UC6 and UC12 reached 100% pass rate in the report.
- UC14 is currently represented by Appium mobile tests in this folder.
