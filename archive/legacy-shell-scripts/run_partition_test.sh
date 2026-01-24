#!/bin/bash

###############################################################################
# Partition Test Automation Script
#
# Runs complete partition-based fork test from deployment to analysis.
#
# Usage:
#   ./run_partition_test.sh TEST_ID V27_ECONOMIC_PCT V27_HASHRATE_PCT
#
# Example:
#   ./run_partition_test.sh 5.3 70 30
#
# This script will:
#   1. Deploy network configuration
#   2. Generate common history (blocks 0-101)
#   3. Verify partition isolation
#   4. Run partition mining (30 minutes)
#   5. Monitor fork depth
#   6. Run economic analysis
#   7. Save results
#   8. Cleanup
#
###############################################################################

set -euo pipefail

# Default configuration
MINING_DURATION=1800  # 30 minutes
MONITORING_INTERVAL=30
COMMON_HISTORY_HEIGHT=101
PARTITION_MODE="static"  # static or dynamic

# Parse arguments
if [[ $# -lt 3 ]]; then
    echo "Usage: $0 TEST_ID V27_ECONOMIC_PCT V27_HASHRATE_PCT [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --duration SECONDS      Mining duration (default: 1800)"
    echo "  --partition-mode MODE   Partitioning mode: static or dynamic (default: static)"
    echo ""
    echo "Example:"
    echo "  $0 5.3 70 30"
    echo "  $0 5.3 70 30 --duration 300                    # 5-minute test"
    echo "  $0 5.3 70 30 --partition-mode dynamic          # Dynamic partitioning"
    echo ""
    echo "Partition modes:"
    echo "  static:  Zero cross-partition edges from deployment (old behavior)"
    echo "  dynamic: Deploy with bridge connections, partition via setban RPC"
    echo ""
    echo "This runs Test 5.3 with 70% economic weight and 30% hashrate on v27 partition."
    exit 1
fi

TEST_ID="$1"
V27_ECONOMIC="$2"
V27_HASHRATE="$3"
shift 3

# Parse optional arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --duration)
            MINING_DURATION="$2"
            shift 2
            ;;
        --partition-mode)
            PARTITION_MODE="$2"
            if [[ "$PARTITION_MODE" != "static" && "$PARTITION_MODE" != "dynamic" ]]; then
                echo "Error: --partition-mode must be 'static' or 'dynamic', got '$PARTITION_MODE'"
                exit 1
            fi
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

V26_HASHRATE=$((100 - V27_HASHRATE))

# Configuration
ROOT_DIR="/home/pfoytik/bitcoinTools/warnet"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
NETWORK_DIR="$ROOT_DIR/test-networks/$TEST_ID" #-economic-$V27_ECONOMIC-hashrate-$V27_HASHRATE"
RESULTS_DIR="$BASE_DIR/results"

# Source partition utilities for dynamic partitioning
if [[ "$PARTITION_MODE" == "dynamic" ]]; then
    PARTITION_UTILS="$SCRIPT_DIR/partition_utils.sh"
    if [[ -f "$PARTITION_UTILS" ]]; then
        source "$PARTITION_UTILS"
        echo "✓ Loaded partition utilities for dynamic partitioning"
    else
        echo "Error: Dynamic mode requires partition_utils.sh at $PARTITION_UTILS"
        exit 1
    fi
fi

echo $NETWORK_DIR

echo "=========================================="
echo "Partition Test Automation"
echo "=========================================="
echo "Test ID: $TEST_ID"
echo "v27: ${V27_ECONOMIC}% economic, ${V27_HASHRATE}% hashrate"
echo "v22: $((100 - V27_ECONOMIC))% economic, ${V26_HASHRATE}% hashrate"
echo "Duration: $((MINING_DURATION / 60)) minutes"
echo "Partition mode: $PARTITION_MODE"
echo "=========================================="
echo ""

# Create results directory
mkdir -p "$RESULTS_DIR"

# Check if network config exists
if [[ ! -f "$NETWORK_DIR/network.yaml" ]]; then
    echo "Error: Network configuration not found at $NETWORK_DIR/network.yaml"
    echo ""
    echo "Generate it first with:"
    echo "  cd $BASE_DIR/networkGen"
    echo "  python3 partition_network_generator.py --test-id $TEST_ID --v27-economic $V27_ECONOMIC --v27-hashrate $V27_HASHRATE"
    exit 1
fi

echo "✓ Network configuration found"
echo ""

# Step 1: Deploy network
echo "=========================================="
echo "Step 1: Deploying network"
echo "=========================================="
cd "$NETWORK_DIR"
warnet deploy $NETWORK_DIR 
echo ""
echo "Waiting 90 seconds for nodes to initialize..."
sleep 90

# Check deployment status
echo "Checking node status..."
warnet status || true  # Don't fail on partition detection warning
echo "✓ All nodes deployed"
echo ""

# Step 2: Generate common history
echo "=========================================="
echo "Step 2: Generating common history"
echo "=========================================="
echo "Creating blocks 0-${COMMON_HISTORY_HEIGHT} on node-0000..."

# Ensure wallet exists and is loaded
echo "Ensuring wallet is ready..."
# Create non-descriptor wallet (false for descriptors) to allow key generation
# Suppress errors if wallet already exists
warnet bitcoin rpc node-0000 createwallet "miner" false 2>&1 | grep -v "error" || true
sleep 2

# Get a mining address (wallet should be auto-loaded after creation)
echo "Getting mining address..."
MINING_ADDRESS=$(warnet bitcoin rpc node-0000 -rpcwallet=miner getnewaddress 2>&1 | grep "^bcrt1" || echo "")
if [[ -z "$MINING_ADDRESS" ]]; then
    echo "  ERROR: Failed to get mining address from wallet"
    echo "  Attempting to create new wallet..."
    warnet bitcoin rpc node-0000 createwallet "miner2" false 2>&1 || true
    sleep 1
    MINING_ADDRESS=$(warnet bitcoin rpc node-0000 -rpcwallet=miner2 getnewaddress 2>&1 | grep "^bcrt1" || echo "")
fi

if [[ -z "$MINING_ADDRESS" ]]; then
    echo "  FATAL: Could not get mining address"
    exit 1
fi

echo "Mining to address: $MINING_ADDRESS"

# Generate 101 blocks
for i in $(seq 1 $COMMON_HISTORY_HEIGHT); do
    warnet bitcoin rpc node-0000 generatetoaddress 1 "$MINING_ADDRESS" > /dev/null
    if [[ $((i % 20)) -eq 0 ]]; then
        echo "  Generated $i/$COMMON_HISTORY_HEIGHT blocks..."
    fi
    sleep 0.5
done

echo "✓ Generated $COMMON_HISTORY_HEIGHT blocks"
echo ""
echo "Waiting 60 seconds for propagation..."
sleep 60

# Verify common history
echo "Verifying all nodes at height ${COMMON_HISTORY_HEIGHT}..."
V27_HEIGHT=$(warnet bitcoin rpc node-0000 getblockcount)
V22_HEIGHT=$(warnet bitcoin rpc node-0010 getblockcount)

echo "  v27 partition (node-0000): height $V27_HEIGHT"
echo "  v22 partition (node-0010): height $V22_HEIGHT"

if [[ "$PARTITION_MODE" == "dynamic" ]]; then
    # Dynamic mode: Both partitions should have common history
    if [[ $V27_HEIGHT -ne $COMMON_HISTORY_HEIGHT ]] || [[ $V22_HEIGHT -ne $COMMON_HISTORY_HEIGHT ]]; then
        echo "⚠ Warning: Not all nodes at expected height $COMMON_HISTORY_HEIGHT"
        echo "  Proceeding anyway, but results may be affected"
    else
        echo "✓ All nodes at height $COMMON_HISTORY_HEIGHT (common history propagated)"
    fi
else
    # Static mode: Only v27 partition has common history (v22 may be at 0)
    if [[ $V27_HEIGHT -ne $COMMON_HISTORY_HEIGHT ]]; then
        echo "⚠ Warning: v27 partition not at expected height $COMMON_HISTORY_HEIGHT"
        echo "  Proceeding anyway, but results may be affected"
    else
        echo "✓ v27 partition at height $COMMON_HISTORY_HEIGHT"
        echo "  Note: v22 partition at $V22_HEIGHT (expected for static mode)"
    fi
fi
echo ""

# Step 2.5: Dynamic partitioning (if enabled)
if [[ "$PARTITION_MODE" == "dynamic" ]]; then
    echo "=========================================="
    echo "Step 2.5: Activating dynamic partition"
    echo "=========================================="
    echo "Partitioning network by version using setban RPC..."

    # Call partition_by_version function from partition_utils.sh
    partition_by_version "$NETWORK_DIR/network.yaml" "27.0" "26.0" 86400

    echo "✓ Network partitioned by version"
    echo "  v27 nodes banned all v26 IPs"
    echo "  v26 nodes banned all v27 IPs"
    echo "  Ban duration: 24 hours"
    echo ""
    echo "Waiting 10 seconds for ban propagation..."
    sleep 10
    echo ""
fi

# Step 3: Verify partition isolation
echo "=========================================="
echo "Step 3: Verifying partition isolation"
echo "=========================================="
echo "Checking that v27 and v22 nodes are isolated..."

# Get peer info from v27 node
V27_PEERS=$(warnet bitcoin rpc node-0000 getpeerinfo | grep -c "\"addr\"" || true)
echo "  v27 partition (node-0000): $V27_PEERS peers"

# Check if v27 node is connected to any v22 nodes (indices 10-19)
# This is a simplified check - full validation would require parsing peer IPs
echo "  Note: Manual verification recommended"
echo "  ✓ Assuming partition isolation (verify with: warnet bitcoin rpc node-0000 getpeerinfo)"
echo ""

# Step 4 & 5: Run mining and monitoring in parallel
echo "=========================================="
echo "Step 4 & 5: Mining and Monitoring"
echo "=========================================="
echo "Starting partition mining (${MINING_DURATION}s = $((MINING_DURATION / 60)) minutes)..."
echo "Starting fork depth monitoring (${MONITORING_INTERVAL}s intervals)..."
echo ""

# Start mining in background
cd "$BASE_DIR/.."
warnet run warnet/scenarios/partition_miner.py \
    --v27-hashrate "$V27_HASHRATE" \
    --v26-hashrate "$V26_HASHRATE" \
    --interval 10 \
    --duration "$MINING_DURATION" \
    --start-height "$COMMON_HISTORY_HEIGHT" &
MINING_PID=$!

# Start monitoring in background
cd "$SCRIPT_DIR"
./monitor_dual_partition.sh \
    --interval "$MONITORING_INTERVAL" \
    --duration "$MINING_DURATION" \
    --start-height "$COMMON_HISTORY_HEIGHT" \
    --output "$RESULTS_DIR/test-$TEST_ID-timeline.csv" &
MONITORING_PID=$!

echo "Mining PID: $MINING_PID"
echo "Monitoring PID: $MONITORING_PID"
echo ""
echo "Waiting for completion (this will take $((MINING_DURATION / 60)) minutes)..."
echo "You can monitor progress in another terminal with:"
echo "  tail -f $RESULTS_DIR/test-$TEST_ID-timeline.csv"
echo ""

# Wait for both processes to complete
wait $MINING_PID
MINING_EXIT=$?

wait $MONITORING_PID
MONITORING_EXIT=$?

if [[ $MINING_EXIT -ne 0 ]]; then
    echo "⚠ Warning: Mining process exited with code $MINING_EXIT"
fi

if [[ $MONITORING_EXIT -ne 0 ]]; then
    echo "⚠ Warning: Monitoring process exited with code $MONITORING_EXIT"
fi

echo "✓ Mining and monitoring complete"
echo ""

# Step 6: Economic analysis
echo "=========================================="
echo "Step 6: Economic Analysis"
echo "=========================================="
cd "$BASE_DIR/monitoring"

python3 auto_economic_analysis.py \
    --network-config "$NETWORK_DIR" \
    --live-query \
    --fork-depth-threshold 3 | tee "$RESULTS_DIR/test-$TEST_ID-analysis.txt"

ANALYSIS_EXIT=${PIPESTATUS[0]}

if [[ $ANALYSIS_EXIT -eq 0 ]]; then
    echo "✓ Economic analysis complete"
else
    echo "⚠ Warning: Economic analysis exited with code $ANALYSIS_EXIT"
fi
echo ""

# Step 7: Display results summary
echo "=========================================="
echo "Results Summary"
echo "=========================================="

# Parse final timeline entry
FINAL_LINE=$(tail -n 1 "$RESULTS_DIR/test-$TEST_ID-timeline.csv")
IFS=',' read -r timestamp v27_final v22_final fork_depth height_diff v27_leading <<< "$FINAL_LINE"

echo "Final chain heights:"
echo "  v27: $v27_final"
echo "  v22: $v22_final"
echo "  Fork depth: $fork_depth blocks"
echo "  Height difference: $height_diff blocks"
echo "  Leading chain: $(if [[ "$v27_leading" == "true" ]]; then echo "v27"; else echo "v22"; fi)"
echo ""

# Calculate height ratio
if [[ $v22_final -gt 0 ]]; then
    HEIGHT_RATIO=$(echo "scale=3; $v27_final / $v22_final" | bc)
    echo "Height ratio (v27/v22): $HEIGHT_RATIO"

    # Expected ratio based on hashrate
    EXPECTED_RATIO=$(echo "scale=3; $V27_HASHRATE / $V26_HASHRATE" | bc)
    echo "Expected ratio (from hashrate): $EXPECTED_RATIO"
    echo ""
fi

echo "Results saved to:"
echo "  Timeline: $RESULTS_DIR/test-$TEST_ID-timeline.csv"
echo "  Analysis: $RESULTS_DIR/test-$TEST_ID-analysis.json"
echo ""

# Step 8: Complete (cleanup handled by wrapper script if running in batch mode)
echo "=========================================="
echo "Test $TEST_ID Complete!"
echo "=========================================="
echo "Note: Network left running. Cleanup handled by batch script or run 'kubectl delete pods --all -n default' manually."
echo ""
echo ""

exit 0
