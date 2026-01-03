#!/bin/bash
# Automated test script for automation-tester agent
# This script runs all tests and reports results

set -e  # Exit on error (but we'll handle errors)

echo "=================================="
echo "Life Optimization AI - Test Suite"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"

    TESTS_TOTAL=$((TESTS_TOTAL + 1))

    echo "----------------------------------------"
    echo "Test $TESTS_TOTAL: $test_name"
    echo "----------------------------------------"

    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate || {
    echo -e "${RED}❌ Failed to activate venv${NC}"
    exit 1
}

echo -e "${GREEN}✅ Virtual environment activated${NC}"
echo ""

# Test 1: Check Python version
run_test "Python Version Check" "python --version"
echo ""

# Test 2: Check dependencies
run_test "Dependencies Installed" "pip list | grep -E 'anthropic|openai|psycopg2|pydantic' > /dev/null"
echo ""

# Test 3: Database connection
run_test "PostgreSQL Connection" "python -c 'from database.connection import Database; Database.execute_one(\"SELECT 1\")' 2>/dev/null"
echo ""

# Test 4: Configuration loading
run_test "Configuration Loading" "python -c 'from config.settings import Settings; s=Settings(); print(s.llm_provider)' 2>/dev/null"
echo ""

# Test 5: Import agents
run_test "Import BaseAgent" "python -c 'from agents.base_agent import BaseAgent' 2>/dev/null"
echo ""

run_test "Import HealthMonitorAgent" "python -c 'from agents.health_monitor_agent import create_health_monitor' 2>/dev/null"
echo ""

# Test 6: Import integrations
run_test "Import GarminConnector" "python -c 'from integrations.garmin_connector import GarminConnector' 2>/dev/null"
echo ""

# Test 7: Garmin connector with mock data
run_test "Garmin Mock Data" "python -c '
from integrations.garmin_connector import GarminConnector
g = GarminConnector()
sleep = g.get_sleep_data()
assert sleep[\"sleep_duration_hours\"] > 0
assert \"sleep_quality_score\" in sleep
print(f\"Sleep: {sleep[\"sleep_duration_hours\"]}h, Quality: {sleep[\"sleep_quality_score\"]}/100\")
' 2>/dev/null"
echo ""

# Test 8: Recovery score calculation
run_test "Recovery Score Calculation" "python -c '
from integrations.garmin_connector import GarminConnector
g = GarminConnector()
score = g.get_recovery_score()
assert 0 <= score <= 100
print(f\"Recovery score: {score}/100\")
' 2>/dev/null"
echo ""

# Test 9: Database health metric insertion
run_test "Database Insert Health Metric" "python -c '
from database.connection import insert_health_metric
from datetime import datetime
data = {
    \"timestamp\": datetime.now(),
    \"source\": \"test\",
    \"sleep_duration_hours\": 7.5,
    \"sleep_quality_score\": 85,
    \"resting_heart_rate\": 60,
    \"stress_level\": 30,
    \"recovery_score\": 75.5,
    \"steps\": 10000,
    \"raw_data\": \"{\\\"test\\\": true}\"
}
health_id = insert_health_metric(data)
print(f\"Inserted health metric ID: {health_id}\")
assert health_id > 0
' 2>/dev/null"
echo ""

# Test 10: Health Monitor Agent creation (no LLM call)
run_test "Create HealthMonitorAgent" "python -c '
from agents.health_monitor_agent import create_health_monitor
agent = create_health_monitor()
print(f\"Agent created with {len(agent.tools)} tools\")
assert len(agent.tools) == 4
' 2>/dev/null"
echo ""

# Summary
echo "=================================="
echo "Test Summary"
echo "=================================="
echo "Total Tests: $TESTS_TOTAL"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Add ANTHROPIC_API_KEY or OPENAI_API_KEY to .env"
    echo "  2. Run: python test_agents.py"
    echo "  3. Test full agent with LLM integration"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo ""
    echo "Please check the errors above and fix before proceeding."
    exit 1
fi
