#!/bin/bash

echo "🧪 RCA-GPT Final Test Suite"
echo "============================"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Test counter
TESTS=0
PASSED=0

run_test() {
    TESTS=$((TESTS + 1))
    echo -n "Test $TESTS: $1... "
    if eval "$2" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗${NC}"
    fi
}

# Run tests
run_test "CLI version" "python -m rca_gpt.cli --version"
run_test "Database exists" "test -f data/incidents.db"
run_test "Model exists" "test -f models/classifier.pkl"
run_test "History command" "python -m rca_gpt.cli history --limit 5"
run_test "Stats command" "python -m rca_gpt.cli stats"
run_test "Similar command" "python -m rca_gpt.cli similar 'timeout'"
run_test "Patterns command" "python -m rca_gpt.cli patterns"
run_test "Timeline command" "python -m rca_gpt.cli timeline 1"
run_test "Unit tests" "python -m unittest discover tests/ -v"

echo ""
echo "============================"
echo -e "Results: ${GREEN}$PASSED${NC}/$TESTS passed"

if [ $PASSED -eq $TESTS ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi