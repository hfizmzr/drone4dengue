#!/usr/bin/env bash
# run_tests.sh — Convenience script to execute the Selenium test suite
# Usage:
#   ./run_tests.sh                   # run all tests (headless)
#   HEADLESS=false ./run_tests.sh    # run with visible browser
#   ./run_tests.sh -k TC5-07        # run a specific test
#
# Prerequisites:
#   source venv/bin/activate
#   pip install -r selenium/requirements.txt
#
# Environment overrides (export before running):
#   ADMIN_URL       default: http://localhost:3000
#   API_URL         default: http://localhost:4000
#   ADMIN_EMAIL     default: admin@drone4dengue.com
#   ADMIN_PASSWORD  default: admin123
#   HEADLESS        default: true  (set to false for visible browser)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure reports directory exists
mkdir -p reports

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Detect custom label from -k argument
REPORT_NAME="selenium_suite"

if [[ "$*" == *"uc2"* ]]; then
    REPORT_NAME="uc2"
elif [[ "$*" == *"uc4"* ]]; then
    REPORT_NAME="uc4"
elif [[ "$*" == *"uc5"* ]]; then
    REPORT_NAME="uc5"
elif [[ "$*" == *"uc6"* ]]; then
    REPORT_NAME="uc6"
elif [[ "$*" == *"uc10"* ]]; then
    REPORT_NAME="uc10"
elif [[ "$*" == *"uc12"* ]]; then
    REPORT_NAME="uc12"
fi

REPORT_FILE="reports/${REPORT_NAME}_${TIMESTAMP}.html"

echo "========================================"
echo " Drone4Dengue Selenium Test Suite"
echo " Selenium Web Tests (UC2, UC4, UC5, UC6, UC10, UC12)"
echo " Admin Web: ${ADMIN_URL:-http://localhost:3000}"
echo " Headless:  ${HEADLESS:-true}"
echo "========================================"
echo ""

# Run pytest – forward any extra arguments (e.g., -k, --lf)
python3 -m pytest \
    --html="$REPORT_FILE" \
    --self-contained-html \
    selenium/ \
    "$@"

echo ""
echo "Test report saved to: $REPORT_FILE"
