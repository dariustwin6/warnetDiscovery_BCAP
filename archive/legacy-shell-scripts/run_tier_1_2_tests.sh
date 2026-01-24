#!/bin/bash

###############################################################################
# Master Test Runner - Tier 1 & 2 Sequential Execution
# Runs 17 partition tests with automatic cleanup between each
# Duration: ~30 minutes per test = ~8.5 hours total
###############################################################################

# Note: Removed 'set -e' to allow cleanup to continue even if kubectl has non-zero exit

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="$SCRIPT_DIR/../results"
LOG_DIR="/tmp/tier-1-2-test-logs"
DURATION=1800  # 30 minutes

# Create log directory
mkdir -p "$LOG_DIR"

# Test configurations: test_id v27_economic v27_hashrate
declare -a TESTS=(
    # TIER 1: Edge Case Validation (3 tests)
    "test-1.1-E95-H10-dynamic 95 10"
    "test-1.2-E10-H95-dynamic 10 95"
    "test-1.3-E90-H90-dynamic 90 90"

    # TIER 2 - Series A: Economic Override Threshold (5 tests)
    "test-2.1-E50-H40-dynamic 50 40"
    "test-2.2-E60-H40-dynamic 60 40"
    "test-2.3-E70-H40-dynamic 70 40"
    "test-2.4-E80-H40-dynamic 80 40"
    "test-2.5-E90-H40-dynamic 90 40"

    # TIER 2 - Series B: Hashrate Resistance Threshold (4 tests, skipping 2.7)
    "test-2.6-E70-H20-dynamic 70 20"
    "test-2.8-E70-H40-dynamic 70 40"
    "test-2.9-E70-H45-dynamic 70 45"
    "test-2.10-E70-H49-dynamic 70 49"

    # TIER 2 - Series C: Critical Balance Zone (5 tests)
    "test-2.11-E50-H50-dynamic 50 50"
    "test-2.12-E52-H48-dynamic 52 48"
    "test-2.13-E48-H52-dynamic 48 52"
    "test-2.14-E55-H55-dynamic 55 55"
    "test-2.15-E45-H45-dynamic 45 45"
)

# Initialize counters (must be numeric to avoid arithmetic errors)
SUCCESS_COUNT=0
FAIL_COUNT=0
START_TIME=$(date +%s)

echo "=========================================="
echo "TIER 1 & 2 TEST SUITE EXECUTION"
echo "=========================================="
echo "Total tests: ${#TESTS[@]}"
echo "Duration per test: ${DURATION}s (30 minutes)"
echo "Estimated total time: ~8.5 hours"
echo "Started: $(date)"
echo "=========================================="
echo ""

for i in "${!TESTS[@]}"; do
    # Parse configuration
    read -r test_id economic hashrate <<< "${TESTS[$i]}"

    TEST_NUM=$((i + 1))
    LOG_FILE="$LOG_DIR/${test_id}.log"

    echo "=========================================="
    echo "Test $TEST_NUM/${#TESTS[@]}: $test_id"
    echo "=========================================="
    echo "Configuration:"
    echo "  v27: ${economic}% economic, ${hashrate}% hashrate"
    echo "  v26: $((100-economic))% economic, $((100-hashrate))% hashrate"
    echo "  Duration: ${DURATION}s (30 min)"
    echo "  Log: $LOG_FILE"
    echo ""
    echo "Starting test at $(date)..."
    echo "=========================================="

    # Run test
    if cd "$SCRIPT_DIR" && ./run_partition_test.sh \
        "$test_id" \
        "$economic" \
        "$hashrate" \
        --partition-mode dynamic \
        --duration "$DURATION" 2>&1 | tee "$LOG_FILE"; then

        echo ""
        echo "✓ Test $TEST_NUM complete: $test_id"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        echo "  (Success count: $SUCCESS_COUNT)"
    else
        echo ""
        echo "✗ Test $TEST_NUM FAILED: $test_id"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        echo "  (Failure count: $FAIL_COUNT)"
    fi

    echo ""

    # Cleanup before next test
    if [ $TEST_NUM -lt ${#TESTS[@]} ]; then
        echo "Cleaning up network..."
        echo "  Deleting all pods using kubectl..."
        kubectl delete pods --all -n default --wait=true --timeout=120s
        echo "  Waiting for cleanup to complete..."
        sleep 5
        echo "✓ Cleanup complete"
        echo ""
        echo "Waiting 30 seconds before next test..."
        sleep 30
        echo ""
    fi
done

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
HOURS=$((DURATION / 3600))
MINUTES=$(((DURATION % 3600) / 60))

echo "=========================================="
echo "TEST SUITE COMPLETE"
echo "=========================================="
echo "Completed: $(date)"
echo "Total time: ${HOURS}h ${MINUTES}m"
echo ""
echo "Results:"
echo "  Success: $SUCCESS_COUNT"
echo "  Failed:  $FAIL_COUNT"
echo "  Total:   ${#TESTS[@]}"
echo ""
echo "Test logs: $LOG_DIR"
echo "Results:   $RESULTS_DIR"
echo "=========================================="

# Summary of results files
echo ""
echo "Generated results files:"
find "$RESULTS_DIR" -name "*.json" -o -name "*.csv" | grep -E "test-(1|2)\." | sort

exit $FAIL_COUNT
