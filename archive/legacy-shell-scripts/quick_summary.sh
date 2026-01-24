#!/bin/bash

echo "=========================================="
echo "FORK TEST SUMMARY"
echo "=========================================="
echo ""

# Count total iterations
ITER_COUNT=$(ls -d test_results/live_monitoring/iter_* 2>/dev/null | wc -l)
echo "Total monitoring iterations: $ITER_COUNT"

# Count fork events
if [ -f test_results/live_monitoring/fork_events.log ]; then
    FORK_COUNT=$(wc -l < test_results/live_monitoring/fork_events.log)
    echo "Fork detection events: $FORK_COUNT"
    
    if [ $FORK_COUNT -gt 0 ]; then
        FORK_PERCENT=$(echo "scale=1; ($FORK_COUNT / $ITER_COUNT) * 100" | bc)
        echo "Fork percentage: ${FORK_PERCENT}%"
    fi
fi

echo ""
echo "Timeline:"
echo "  - Test duration: ~$((ITER_COUNT * 30 / 60)) minutes"

# Check for height progression
FIRST_ITER=$(ls -t test_results/live_monitoring/iter_* | tail -1)
LAST_ITER=$(ls -t test_results/live_monitoring/iter_* | head -1)

if [ -f "$FIRST_ITER/tank-0000_blockchain.json" ] && [ -f "$LAST_ITER/tank-0000_blockchain.json" ]; then
    START_HEIGHT=$(jq -r '.blocks' "$FIRST_ITER/tank-0000_blockchain.json" 2>/dev/null)
    END_HEIGHT=$(jq -r '.blocks' "$LAST_ITER/tank-0000_blockchain.json" 2>/dev/null)
    BLOCKS_MINED=$((END_HEIGHT - START_HEIGHT))
    echo "  - Blocks mined: $BLOCKS_MINED (height $START_HEIGHT → $END_HEIGHT)"
fi

echo ""
echo "✓ Test completed successfully!"
echo "=========================================="
