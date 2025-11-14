#!/bin/bash
# ZenithEdge Test Suite Runner
# Quick access to all testing commands

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  ZenithEdge Testing Framework${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to run tests with formatting
run_test() {
    local description=$1
    local command=$2
    
    echo -e "${YELLOW}Running:${NC} $description"
    echo -e "${GREEN}Command:${NC} $command"
    echo ""
    
    eval $command
    
    local exit_code=$?
    echo ""
    echo "----------------------------------------"
    echo ""
    
    return $exit_code
}

# Parse command line arguments
case "$1" in
    "all")
        run_test "All Tests (excluding slow)" \
            "python3 -m pytest tests/ -v -m 'not slow'"
        ;;
    
    "all-slow")
        run_test "All Tests (including slow)" \
            "python3 -m pytest tests/ -v"
        ;;
    
    "unit")
        run_test "Unit Tests" \
            "python3 -m pytest tests/unit/ -v"
        ;;
    
    "integration")
        run_test "Integration Tests" \
            "python3 -m pytest tests/integration/ -v"
        ;;
    
    "system")
        run_test "System Tests (Historical Backtest)" \
            "python3 -m pytest tests/system/ -v"
        ;;
    
    "stress")
        run_test "Stress Tests (excluding slow)" \
            "python3 -m pytest tests/stress/ -v -m 'stress and not slow'"
        ;;
    
    "coverage")
        run_test "Full Test Suite with Coverage Report" \
            "python3 -m pytest tests/ --cov=zenbot --cov=signals --cov-report=html --cov-report=term-missing"
        echo -e "${GREEN}Coverage report generated at:${NC} tests/coverage_html/index.html"
        echo -e "${YELLOW}Open with:${NC} open tests/coverage_html/index.html"
        ;;
    
    "quick")
        run_test "Quick Test Suite (fast tests only)" \
            "python3 -m pytest tests/ -v -m 'unit and not slow' -x"
        ;;
    
    "validation")
        run_test "Validation Engine Tests Only" \
            "python3 -m pytest tests/unit/test_validation_engine.py -v"
        ;;
    
    "contextualizer")
        run_test "Contextualizer Tests Only" \
            "python3 -m pytest tests/unit/test_contextualizer.py -v"
        ;;
    
    "webhook")
        run_test "Webhook Pipeline Tests" \
            "python3 -m pytest tests/integration/test_webhook_pipeline.py -v"
        ;;
    
    "backtest")
        run_test "Historical Backtest Tests" \
            "python3 -m pytest tests/system/test_historical_backtest.py -v"
        ;;
    
    "resilience")
        run_test "Resilience and Load Tests" \
            "python3 -m pytest tests/stress/test_resilience.py -v -m 'not slow'"
        ;;
    
    "db")
        run_test "Database-dependent Tests Only" \
            "python3 -m pytest tests/ -v -m 'requires_db'"
        ;;
    
    "fast")
        run_test "All Fast Tests (no database, no slow)" \
            "python3 -m pytest tests/ -v -m 'not requires_db and not slow'"
        ;;
    
    "failed")
        run_test "Re-run Failed Tests from Last Run" \
            "python3 -m pytest --lf -v"
        ;;
    
    "verbose")
        run_test "All Tests with Maximum Verbosity" \
            "python3 -m pytest tests/ -vv -m 'not slow' --tb=long"
        ;;
    
    "parallel")
        echo -e "${YELLOW}Note:${NC} Install pytest-xdist first: pip install pytest-xdist"
        run_test "All Tests in Parallel (4 workers)" \
            "python3 -m pytest tests/ -v -m 'not slow' -n 4"
        ;;
    
    "markers")
        echo -e "${GREEN}Available Test Markers:${NC}"
        echo ""
        python3 -m pytest --markers
        ;;
    
    "list")
        echo -e "${GREEN}All Available Tests:${NC}"
        echo ""
        python3 -m pytest tests/ --collect-only -q
        ;;
    
    "help"|"")
        echo -e "${GREEN}Usage:${NC} ./run_tests.sh [command]"
        echo ""
        echo -e "${YELLOW}Quick Commands:${NC}"
        echo "  all           - Run all tests (excluding slow)"
        echo "  all-slow      - Run all tests (including slow)"
        echo "  unit          - Run unit tests only"
        echo "  integration   - Run integration tests only"
        echo "  system        - Run system/backtest tests"
        echo "  stress        - Run stress tests (excluding slow)"
        echo "  coverage      - Run all tests with coverage report"
        echo "  quick         - Run fast tests only"
        echo ""
        echo -e "${YELLOW}Specific Test Types:${NC}"
        echo "  validation    - Validation engine tests"
        echo "  contextualizer- Contextualizer tests"
        echo "  webhook       - Webhook pipeline tests"
        echo "  backtest      - Historical backtest tests"
        echo "  resilience    - Resilience/load tests"
        echo ""
        echo -e "${YELLOW}Advanced Options:${NC}"
        echo "  db            - Database-dependent tests only"
        echo "  fast          - All fast tests (no DB, no slow)"
        echo "  failed        - Re-run only failed tests"
        echo "  verbose       - Maximum verbosity"
        echo "  parallel      - Run tests in parallel"
        echo "  markers       - Show all available markers"
        echo "  list          - List all available tests"
        echo ""
        echo -e "${YELLOW}Examples:${NC}"
        echo "  ./run_tests.sh all"
        echo "  ./run_tests.sh unit"
        echo "  ./run_tests.sh coverage"
        echo "  ./run_tests.sh quick"
        echo ""
        echo -e "${GREEN}Documentation:${NC} See TESTING_EXECUTION_GUIDE.md"
        ;;
    
    *)
        echo -e "${YELLOW}Unknown command:${NC} $1"
        echo -e "Run ${GREEN}./run_tests.sh help${NC} for usage information"
        exit 1
        ;;
esac

exit $?
