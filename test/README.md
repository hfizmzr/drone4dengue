# Drone4Dengue – Selenium Test Suite

## Overview

Automated Selenium WebDriver tests for **UC5** (Manage Drone and Location) and **UC6** (Manage Images Captured by Drone) on the **Admin Web** (`http://localhost:3000`).

---

## Directory Structure

```
test/
├── pytest.ini                         ← pytest configuration
├── run_tests.sh                       ← convenience runner script
├── selenium/
│   ├── conftest.py                    ← shared fixtures & helpers
│   ├── requirements.txt               ← Python dependencies
│   ├── test_uc5_drone_management.py   ← TC5-01 through TC5-15
│   ├── test_uc6_drone_images.py       ← TC6-01 through TC6-10
│   └── assets/
│       ├── test_image.jpg             ← JPEG for upload tests
│       ├── test_video.mp4             ← MP4 for TC6-05 (place manually)
│       └── test_document.pdf          ← PDF for TC6-06 (auto-generated)
└── reports/                           ← HTML report output (auto-created)
    └── test_report.html
```

---

## Setup

```bash
# 1. Activate virtual environment (already created by user)
source venv/bin/activate

# 2. Install dependencies
pip install -r selenium/requirements.txt

# 3. Ensure both servers are running (in separate terminals):
#    cd ../server-api && npm run dev      → http://localhost:4000
#    cd ../client-admin && npm run dev    → http://localhost:3000

# 4. (Optional) Place a short MP4 video for TC6-05:
#    cp /path/to/video.mp4 selenium/assets/test_video.mp4
```

---

## Running Tests

### UC2, UC4, UC5, UC6, UC10, UC12 — pytest suite (`run_tests.sh`)

```bash
# All tests (headless Chrome)
./run_tests.sh

# With visible browser window
HEADLESS=false ./run_tests.sh

# Run only UC5 tests
./run_tests.sh -k "uc5"

# Run only UC6 tests
./run_tests.sh -k "uc6"

# Run specific test class
./run_tests.sh -k "TestTC507"

# Run with custom credentials
ADMIN_EMAIL=myadmin@example.com ADMIN_PASSWORD=mypass ./run_tests.sh
```

---

### TC-07 User Management — (`run_tc07.sh`)

```bash
# Run all TC-07 tests
./run_tc07.sh

# Run a single file by partial name
./run_tc07.sh tc_07_001
./run_tc07.sh tc_07_004

# Run against a different environment
ADMIN_URL=http://staging:3000 API_URL=http://staging:4000 ./run_tc07.sh

# Run with custom credentials
ADMIN_EMAIL=myadmin@example.com ADMIN_PASSWORD=mypass ./run_tc07.sh
```

HTML reports are saved to `test-reports/TC-07-*.html`.

---

### TC-08 Data Management — (`run_tc08.sh`)

```bash
# Run all TC-08 tests
./run_tc08.sh

# Run a single file by partial name
./run_tc08.sh tc_08_001
./run_tc08.sh tc_08_003

# Run against a different environment
ADMIN_URL=http://staging:3000 API_URL=http://staging:4000 ./run_tc08.sh

# Run with custom credentials
ADMIN_EMAIL=myadmin@example.com ADMIN_PASSWORD=mypass ./run_tc08.sh
```

HTML reports are saved to `test-reports/TC-08-*.html`.

---
