#!/usr/bin/env bash
# run_tc07.sh — Run all TC-07 (User Management) Selenium tests
#
# Usage:
#   ./run_tc07.sh             # run all TC-07 tests
#   ./run_tc07.sh tc_07_001   # run a single file by partial name
#
# Prerequisites:
#   source venv/bin/activate
#   pip install -r requirements.txt
#
# Environment overrides (export before running, or prefix the command):
#   ADMIN_URL       default: http://localhost:3000
#   API_URL         default: http://localhost:4000
#   ADMIN_EMAIL     default: admin1@drone4dengue.com
#   ADMIN_PASSWORD  default: adminpass1
#
# HTML reports are written to:  test/test-reports/TC-07-*.html

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SELENIUM_DIR="$SCRIPT_DIR/selenium"
REPORTS_DIR="$SCRIPT_DIR/test-reports"

# Inject env overrides so the test files can optionally read them
export ADMIN_URL="${ADMIN_URL:-http://localhost:3000}"
export API_URL="${API_URL:-http://localhost:4000}"
export ADMIN_EMAIL="${ADMIN_EMAIL:-admin1@drone4dengue.com}"
export ADMIN_PASSWORD="${ADMIN_PASSWORD:-adminpass1}"

mkdir -p "$REPORTS_DIR"

echo "========================================"
echo " Drone4Dengue — TC-07 User Management"
echo " Admin Web : $ADMIN_URL"
echo " API       : $API_URL"
echo "========================================"
echo ""

PASS=0
FAIL=0
FAILED_TESTS=()

run_test() {
    local file="$SELENIUM_DIR/$1"
    local name="$1"

    # If a filter argument was supplied, skip non-matching files
    if [[ -n "$FILTER" && "$name" != *"$FILTER"* ]]; then
        return
    fi

    echo "▶  $name"
    if python3 "$file"; then
        echo "   ✓  PASSED"
        ((PASS++)) || true
    else
        echo "   ✗  FAILED"
        ((FAIL++)) || true
        FAILED_TESTS+=("$name")
    fi
    echo ""
}

# Optional single-test filter from first CLI argument
FILTER="${1:-}"

run_test "tc_07_001_user_management.py"
run_test "tc_07_002_003_user_add_edit.py"
run_test "tc_07_004_user_role_management.py"
run_test "tc_07_005_user_status_delete.py"
run_test "tc_07_006_edge_cases.py"

echo "========================================"
echo " TC-07 Results: ${PASS} passed, ${FAIL} failed"
if [[ ${#FAILED_TESTS[@]} -gt 0 ]]; then
    echo " Failed:"
    for t in "${FAILED_TESTS[@]}"; do
        echo "   ✗  $t"
    done
fi
echo " Reports : $REPORTS_DIR/TC-07-*.html"
echo "========================================"

[[ $FAIL -eq 0 ]]
