#!/bin/bash
#
# Continuous Mining Test with Automatic Economic Fork Analysis
#
# This script:
# 1. Starts continuous mining on the deployed Warnet network
# 2. Monitors for fork events
# 3. When fork detected, automatically runs economic analysis
# 4. Logs both technical fork data AND economic impact
#
# Usage:
#   ./continuous_mining_test.sh [OPTIONS]
#
# Options:
#   --interval N      Mining interval in seconds (default: 5)
#   --duration N      Test duration in seconds (default: 3600 = 1 hour)
#   --nodes MODE      Mining mode: allnodes, random, or specific node names (default: random)
#   --network PATH    Path to network config directory (default: auto-detect from warnet)
#   --logdir PATH     Log directory (default: ../test_results/continuous_mining_$(date +%Y%m%d_%H%M%S))
#
# Examples:
#   # Mine on all nodes, 5 second intervals, 1 hour
#   ./continuous_mining_test.sh --interval 5 --duration 3600 --nodes allnodes
#
#   # Mine on random nodes, 10 second intervals
#   ./continuous_mining_test.sh --interval 10 --nodes random
#
#   # Mine on specific nodes
#   ./continuous_mining_test.sh --nodes "exchange-high-custody exchange-high-volume"

set -e

# Default configuration
MINING_INTERVAL=5
TEST_DURATION=3600
MINING_NODES="random"
NETWORK_CONFIG=""
LOGDIR=""
FORK_CHECK_INTERVAL=2
MINER_SCENARIO="$HOME/bitcoinTools/warnet/warnet/scenarios/miner_std.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --interval)
            MINING_INTERVAL="$2"
            shift 2
            ;;
        --duration)
            TEST_DURATION="$2"
            shift 2
            ;;
        --nodes)
            MINING_NODES="$2"
            shift 2
            ;;
        --network)
            NETWORK_CONFIG="$2"
            shift 2
            ;;
        --logdir)
            LOGDIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--interval N] [--duration N] [--nodes MODE] [--network PATH] [--logdir PATH]"
            exit 1
            ;;
    esac
done

# Setup log directory
if [ -z "$LOGDIR" ]; then
    LOGDIR="../test_results/continuous_mining_$(date +%Y%m%d_%H%M%S)"
fi
mkdir -p "$LOGDIR"

MAIN_LOG="$LOGDIR/continuous_mining.log"
FORK_LOG="$LOGDIR/forks_detected.log"
ECONOMIC_LOG="$LOGDIR/economic_analysis.log"
MINING_LOG="$LOGDIR/mining_output.log"

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$MAIN_LOG"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$MAIN_LOG"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$MAIN_LOG"
}

log_fork() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] FORK DETECTED:${NC} $1" | tee -a "$FORK_LOG" | tee -a "$MAIN_LOG"
}

# Cleanup function
cleanup() {
    log "Cleaning up..."

    # Stop mining scenario if running
    if [ ! -z "$MINING_PID" ]; then
        log "Stopping mining process (PID: $MINING_PID)..."
        kill $MINING_PID 2>/dev/null || true
    fi

    # Stop fork monitor if running
    if [ ! -z "$MONITOR_PID" ]; then
        log "Stopping fork monitor (PID: $MONITOR_PID)..."
        kill $MONITOR_PID 2>/dev/null || true
    fi

    log "Test completed. Logs saved to: $LOGDIR"
    log "Summary:"
    log "  - Main log: $MAIN_LOG"
    log "  - Fork log: $FORK_LOG"
    log "  - Economic analysis log: $ECONOMIC_LOG"

    # Print fork summary
    if [ -f "$FORK_LOG" ]; then
        FORK_COUNT=$(grep -c "FORK DETECTED" "$FORK_LOG" || echo "0")
        log "  - Total forks detected: $FORK_COUNT"
    fi
}

trap cleanup EXIT INT TERM

# Print test configuration
log "=========================================================================="
log "CONTINUOUS MINING TEST - Economic Fork Analysis"
log "=========================================================================="
log "Configuration:"
log "  Mining interval: ${MINING_INTERVAL}s"
log "  Test duration: ${TEST_DURATION}s ($(($TEST_DURATION / 60)) minutes)"
log "  Mining nodes: $MINING_NODES"
log "  Log directory: $LOGDIR"
log "=========================================================================="

# Auto-detect network config if not provided
if [ -z "$NETWORK_CONFIG" ]; then
    log "Auto-detecting network configuration..."

    # Try to get network info from warnet
    NETWORK_NAME=$(warnet status 2>/dev/null | grep "Network:" | awk '{print $2}' || echo "")

    if [ -z "$NETWORK_NAME" ]; then
        log_error "No active Warnet network detected. Deploy a network first with 'warnet deploy'"
        exit 1
    fi

    log "Detected network: $NETWORK_NAME"

    # Try common network config locations
    for candidate in \
        "../../test-networks/$NETWORK_NAME/network.yaml" \
        "../test-networks/$NETWORK_NAME/network.yaml" \
        "test-networks/$NETWORK_NAME/network.yaml"; do

        if [ -f "$candidate" ]; then
            NETWORK_CONFIG="$(dirname "$candidate")"
            log "Found network config: $NETWORK_CONFIG"
            break
        fi
    done

    if [ -z "$NETWORK_CONFIG" ]; then
        log_warning "Could not auto-detect network config location"
        log_warning "Economic analysis will use live RPC queries instead of config file"
    fi
fi

# Check if warnet is available
if ! command -v warnet &> /dev/null; then
    log_error "warnet command not found. Is Warnet installed?"
    exit 1
fi

# Check if network is running
if ! warnet status &> /dev/null; then
    log_error "No Warnet network is running. Deploy a network first."
    exit 1
fi

# Get list of nodes
log "Querying network nodes..."
NODES=$(warnet status 2>&1 | grep "Tank" | awk '{print $5}' | grep "^node-" | tr '\n' ' ')

if [ -z "$NODES" ]; then
    log_error "No nodes found in Warnet deployment"
    exit 1
fi

log "Available nodes: $NODES"

# Function to check for forks
check_for_forks() {
    local fork_detected=0

    # Query each node for its chain tip
    local -A tips
    local -A heights

    for node in $NODES; do
        tip=$(warnet bitcoin rpc "$node" getbestblockhash 2>/dev/null || echo "")
        height=$(warnet bitcoin rpc "$node" getblockcount 2>/dev/null || echo "0")

        if [ ! -z "$tip" ]; then
            tips["$node"]="$tip"
            heights["$node"]="$height"
        fi
    done

    # Check if all nodes are on same tip
    local unique_tips=$(printf '%s\n' "${tips[@]}" | sort -u | wc -l)

    if [ "$unique_tips" -gt 1 ]; then
        fork_detected=1

        # Log fork details
        log_fork "Fork detected! $unique_tips different chain tips"
        echo "=========================================================================="  | tee -a "$FORK_LOG"
        echo "FORK EVENT: $(date +'%Y-%m-%d %H:%M:%S')" | tee -a "$FORK_LOG"
        echo "=========================================================================="  | tee -a "$FORK_LOG"

        for node in "${!tips[@]}"; do
            echo "  $node: height ${heights[$node]}, tip ${tips[$node]}" | tee -a "$FORK_LOG"
        done

        echo "" | tee -a "$FORK_LOG"

        # Run economic analysis
        run_economic_analysis
    fi

    return $fork_detected
}

# Function to run economic analysis
run_economic_analysis() {
    log "Running economic fork analysis..."

    echo "=========================================================================="  | tee -a "$ECONOMIC_LOG"
    echo "ECONOMIC FORK ANALYSIS: $(date +'%Y-%m-%d %H:%M:%S')" | tee -a "$ECONOMIC_LOG"
    echo "=========================================================================="  | tee -a "$ECONOMIC_LOG"

    # Check if auto_economic_analysis.py exists
    if [ -f "../monitoring/auto_economic_analysis.py" ]; then
        log "Using automated economic analysis script..."

        if [ ! -z "$NETWORK_CONFIG" ]; then
            python3 ../monitoring/auto_economic_analysis.py \
                --network-config "$NETWORK_CONFIG" \
                --live-query \
                >> "$ECONOMIC_LOG" 2>&1
        else
            python3 ../monitoring/auto_economic_analysis.py \
                --live-query \
                >> "$ECONOMIC_LOG" 2>&1
        fi
    else
        log_warning "auto_economic_analysis.py not found. Manual analysis required."
        echo "To enable automatic economic analysis, create:" | tee -a "$ECONOMIC_LOG"
        echo "  warnetScenarioDiscovery/monitoring/auto_economic_analysis.py" | tee -a "$ECONOMIC_LOG"
        echo "" | tee -a "$ECONOMIC_LOG"

        # Fallback: just log chain tips per node
        echo "Chain state at fork:" | tee -a "$ECONOMIC_LOG"
        for node in $NODES; do
            height=$(warnet bitcoin rpc "$node" getblockcount 2>/dev/null || echo "unknown")
            tip=$(warnet bitcoin rpc "$node" getbestblockhash 2>/dev/null || echo "unknown")
            echo "  $node: height $height" | tee -a "$ECONOMIC_LOG"
        done
    fi

    echo "" | tee -a "$ECONOMIC_LOG"
}

# Start continuous mining
log "Starting continuous mining..."

if [ "$MINING_NODES" = "allnodes" ]; then
    log "Mining on all nodes with ${MINING_INTERVAL}s interval..."
    warnet run "$MINER_SCENARIO" --interval "$MINING_INTERVAL" --allnodes >> "$MINING_LOG" 2>&1 &
    MINING_PID=$!
elif [ "$MINING_NODES" = "random" ]; then
    log "Mining on random nodes with ${MINING_INTERVAL}s interval..."
    warnet run "$MINER_SCENARIO" --interval "$MINING_INTERVAL" --random >> "$MINING_LOG" 2>&1 &
    MINING_PID=$!
else
    log "Mining on specified nodes: $MINING_NODES"
    # For specific nodes, we'd need to modify the command
    # This is a placeholder - actual implementation depends on warnet capabilities
    log_warning "Specific node mining not yet implemented. Falling back to random."
    warnet run "$MINER_SCENARIO" --interval "$MINING_INTERVAL" --random >> "$MINING_LOG" 2>&1 &
    MINING_PID=$!
fi

log "Mining process started (PID: $MINING_PID)"
sleep 2  # Give mining time to start

# Monitor for forks
log "Starting fork monitor (checking every ${FORK_CHECK_INTERVAL}s)..."

START_TIME=$(date +%s)
FORK_COUNT=0

while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))

    # Check if test duration exceeded
    if [ $ELAPSED -ge $TEST_DURATION ]; then
        log "Test duration reached (${ELAPSED}s / ${TEST_DURATION}s). Stopping..."
        break
    fi

    # Check for forks
    if check_for_forks; then
        FORK_COUNT=$((FORK_COUNT + 1))
        log "Fork #${FORK_COUNT} detected and analyzed"
    fi

    # Progress update every minute
    if [ $((ELAPSED % 60)) -eq 0 ] && [ $ELAPSED -gt 0 ]; then
        log "Progress: ${ELAPSED}s / ${TEST_DURATION}s ($(($ELAPSED / 60)) / $(($TEST_DURATION / 60)) minutes)"
        log "Forks detected so far: $FORK_COUNT"
    fi

    sleep $FORK_CHECK_INTERVAL
done

log "Fork monitoring complete"
log "Total forks detected: $FORK_COUNT"

# Cleanup is handled by trap
exit 0
