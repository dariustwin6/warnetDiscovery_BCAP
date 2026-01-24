#!/bin/bash

###############################################################################
# Dual-Partition Monitoring Script
#
# Monitors both v27 and v22 partitions during systematic fork testing.
# Outputs time series data of chain heights and fork depth.
#
# Usage:
#   ./monitor_dual_partition.sh [options]
#
# Options:
#   --interval SECONDS    Polling interval (default: 30)
#   --duration SECONDS    Total monitoring duration (default: 1800 = 30 min)
#   --start-height NUM    Common history height (default: 101)
#   --output FILE         Output CSV file (default: stdout)
#   --v27-node NODE       v27 partition node name (default: node-0000)
#   --v22-node NODE       v22 partition node name (default: node-0010)
#
# Example:
#   ./monitor_dual_partition.sh --interval 30 --duration 1800 --output test-5.3-timeline.csv
#
###############################################################################

set -euo pipefail

# Default values
INTERVAL=30
DURATION=1800
START_HEIGHT=101
OUTPUT_FILE=""
V27_NODE="node-0000"
V22_NODE="node-0010"

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --interval)
            INTERVAL="$2"
            shift 2
            ;;
        --duration)
            DURATION="$2"
            shift 2
            ;;
        --start-height)
            START_HEIGHT="$2"
            shift 2
            ;;
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --v27-node)
            V27_NODE="$2"
            shift 2
            ;;
        --v22-node)
            V22_NODE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --interval SECONDS    Polling interval (default: 30)"
            echo "  --duration SECONDS    Total monitoring duration (default: 1800)"
            echo "  --start-height NUM    Common history height (default: 101)"
            echo "  --output FILE         Output CSV file (default: stdout)"
            echo "  --v27-node NODE       v27 partition node name (default: node-0000)"
            echo "  --v22-node NODE       v22 partition node name (default: node-0010)"
            echo ""
            echo "Example:"
            echo "  $0 --interval 30 --duration 1800 --output test-5.3-timeline.csv"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate warnet is available
if ! command -v warnet &> /dev/null; then
    echo "Error: warnet command not found"
    exit 1
fi

# Setup output (file or stdout)
if [[ -n "$OUTPUT_FILE" ]]; then
    exec > "$OUTPUT_FILE"
    echo "Monitoring started at $(date -Iseconds)" >&2
    echo "Output file: $OUTPUT_FILE" >&2
    echo "Interval: ${INTERVAL}s | Duration: ${DURATION}s ($(($DURATION / 60)) minutes)" >&2
    echo "v27 node: $V27_NODE | v22 node: $V22_NODE" >&2
    echo "----------------------------------------" >&2
fi

# Print CSV header
echo "timestamp,v27_height,v22_height,fork_depth,height_diff,v27_leading"

# Initialize timing
start_time=$(date +%s)
end_time=$((start_time + DURATION))

# Monitoring loop
while true; do
    current_time=$(date +%s)

    # Check if duration exceeded
    if [[ $current_time -ge $end_time ]]; then
        if [[ -n "$OUTPUT_FILE" ]]; then
            echo "Monitoring complete at $(date -Iseconds)" >&2
        fi
        break
    fi

    # Query v27 partition height
    v27_height=$(warnet bitcoin rpc "$V27_NODE" getblockcount 2>/dev/null || echo "0")

    # Query v22 partition height
    v22_height=$(warnet bitcoin rpc "$V22_NODE" getblockcount 2>/dev/null || echo "0")

    # Calculate fork depth
    # fork_depth = v27_height + v22_height - (2 * common_history_height)
    fork_depth=$((v27_height + v22_height - (2 * START_HEIGHT)))

    # Calculate height difference
    height_diff=$((v27_height - v22_height))

    # Determine which chain is leading
    if [[ $v27_height -gt $v22_height ]]; then
        v27_leading="true"
    elif [[ $v27_height -lt $v22_height ]]; then
        v27_leading="false"
    else
        v27_leading="tie"
    fi

    # Get timestamp
    timestamp=$(date -Iseconds)

    # Output CSV row
    echo "$timestamp,$v27_height,$v22_height,$fork_depth,$height_diff,$v27_leading"

    # Progress logging to stderr if using file output
    if [[ -n "$OUTPUT_FILE" ]]; then
        elapsed=$((current_time - start_time))
        remaining=$((DURATION - elapsed))
        echo "[${elapsed}s/${DURATION}s] v27: $v27_height | v22: $v22_height | fork_depth: $fork_depth | remaining: ${remaining}s" >&2
    fi

    # Wait for next interval
    sleep "$INTERVAL"
done

if [[ -n "$OUTPUT_FILE" ]]; then
    echo "Final statistics:" >&2
    echo "  Total data points: $(wc -l < "$OUTPUT_FILE")" >&2
    echo "  Final fork depth: $fork_depth" >&2
    echo "----------------------------------------" >&2
fi

exit 0
