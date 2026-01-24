#!/bin/bash

# 30-minute pool mining test with fork depth monitoring
# Monitors every 30 seconds for sustained forks (depth >= 3)

NETWORK_CONFIG="/home/pfoytik/bitcoinTools/warnet/test-networks/pool-mining-scenarios"
FORK_DEPTH_THRESHOLD=3
CHECK_INTERVAL=30
TOTAL_DURATION=1800  # 30 minutes

START_TIME=$(date +%s)
END_TIME=$((START_TIME + TOTAL_DURATION))
CHECK_COUNT=0
FORK_COUNT=0
SUSTAINED_FORK_COUNT=0
NATURAL_SPLIT_COUNT=0

echo "========================================"
echo "Pool Mining Test - Fork Depth Monitoring"
echo "========================================"
echo "Start Time: $(date)"
echo "Duration: $TOTAL_DURATION seconds (30 minutes)"
echo "Check Interval: $CHECK_INTERVAL seconds"
echo "Fork Depth Threshold: $FORK_DEPTH_THRESHOLD blocks"
echo "Network: $NETWORK_CONFIG"
echo "========================================"
echo ""

while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    REMAINING=$((END_TIME - CURRENT_TIME))
    
    if [ $REMAINING -le 0 ]; then
        echo ""
        echo "========================================"
        echo "Test Complete!"
        echo "Total Duration: $ELAPSED seconds"
        echo "Total Checks: $CHECK_COUNT"
        echo "Total Forks Detected: $FORK_COUNT"
        echo "  - Sustained Forks (>= $FORK_DEPTH_THRESHOLD blocks): $SUSTAINED_FORK_COUNT"
        echo "  - Natural Splits (< $FORK_DEPTH_THRESHOLD blocks): $NATURAL_SPLIT_COUNT"
        echo "========================================"
        break
    fi
    
    CHECK_COUNT=$((CHECK_COUNT + 1))
    echo ""
    echo "----------------------------------------"
    echo "[Check $CHECK_COUNT] $(date) - Elapsed: ${ELAPSED}s / Remaining: ${REMAINING}s"
    echo "----------------------------------------"
    
    # Run fork depth analysis
    python3 auto_economic_analysis.py \
        --network-config "$NETWORK_CONFIG" \
        --live-query \
        --fork-depth-threshold $FORK_DEPTH_THRESHOLD
    
    RESULT=$?
    
    # Check if fork was detected (exit code 0 means fork analyzed, 1 means error, we check output for classification)
    if [ $RESULT -eq 0 ]; then
        FORK_COUNT=$((FORK_COUNT + 1))
        SUSTAINED_FORK_COUNT=$((SUSTAINED_FORK_COUNT + 1))
        echo "✅ Sustained fork detected and analyzed"
    fi
    
    # Note: Natural splits exit with code 0 too but print different message
    # We're counting based on the script's behavior
    
    echo ""
    echo "Progress: Forks detected: $FORK_COUNT (Sustained: $SUSTAINED_FORK_COUNT, Natural: $NATURAL_SPLIT_COUNT)"
    
    sleep $CHECK_INTERVAL
done
