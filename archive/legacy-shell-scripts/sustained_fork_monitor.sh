#!/bin/bash
#
# Sustained Fork Monitor
#
# Tracks fork DURATION - only reports forks that persist for a minimum time
# Distinguishes between temporary propagation delays and actual sustained forks
#
# Usage:
#   ./sustained_fork_monitor.sh [options]
#
# Options:
#   --min-duration SECONDS    Minimum fork duration to report (default: 30)
#   --check-interval SECONDS  How often to check (default: 10)
#   --namespace NAME          Kubernetes namespace (default: warnet)

set -e

# Default parameters
MIN_FORK_DURATION=30  # Only report forks lasting 30+ seconds
CHECK_INTERVAL=10      # Check every 10 seconds
NAMESPACE="warnet"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --min-duration)
            MIN_FORK_DURATION="$2"
            shift 2
            ;;
        --check-interval)
            CHECK_INTERVAL="$2"
            shift 2
            ;;
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/../test_results/sustained_fork_monitoring"
LOG_FILE="${OUTPUT_DIR}/monitor.log"
FORK_LOG="${OUTPUT_DIR}/sustained_forks.log"
TRANSIENT_LOG="${OUTPUT_DIR}/transient_forks.log"

mkdir -p "${OUTPUT_DIR}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

log() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_fork() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$FORK_LOG"
}

log_transient() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$TRANSIENT_LOG"
}

# Fork tracking state
FORK_STATE="none"           # "none" or "forked"
FORK_START_TIME=0           # Unix timestamp when fork started
FORK_ID=""                  # Unique ID for current fork
PREVIOUS_TIPS_HASH=""       # Hash of previous tips to detect changes

log "${GREEN}=== Sustained Fork Monitor Started ===${NC}"
log "Namespace: $NAMESPACE"
log "Minimum fork duration: ${MIN_FORK_DURATION}s"
log "Check interval: ${CHECK_INTERVAL}s"
log "Output directory: $OUTPUT_DIR"
log ""

ITERATION=0

while true; do
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    ITERATION=$((ITERATION + 1))
    CURRENT_TIME=$(date +%s)

    # Check if pods are running
    RUNNING_PODS=$(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)

    if [ $RUNNING_PODS -eq 0 ]; then
        log "${RED}No running pods detected in namespace: $NAMESPACE${NC}"
        sleep $CHECK_INTERVAL
        continue
    fi

    echo -e "${GREEN}[Iter $ITERATION - $TIMESTAMP] Monitoring $RUNNING_PODS nodes${NC}"

    # Get node list dynamically
    NODE_LIST=($(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Running --no-headers 2>/dev/null | awk '{print $1}'))

    if [ ${#NODE_LIST[@]} -eq 0 ]; then
        log "${RED}Could not get node list${NC}"
        sleep $CHECK_INTERVAL
        continue
    fi

    # Arrays to track heights and tips
    declare -A NODE_HEIGHTS
    declare -A NODE_TIPS
    declare -A NODE_VERSIONS

    # Collect data from each node
    for NODE in "${NODE_LIST[@]}"; do
        # Get block count
        HEIGHT=$(warnet bitcoin rpc "$NODE" getblockcount 2>/dev/null | tr -d '\r\n')

        # Get best block hash
        BEST_HASH=$(warnet bitcoin rpc "$NODE" getbestblockhash 2>/dev/null | tr -d '\r\n')

        # Get version
        VERSION=$(warnet bitcoin rpc "$NODE" getnetworkinfo 2>/dev/null | grep -o '"subversion":"[^"]*"' | cut -d'"' -f4 || echo "unknown")

        if [ ! -z "$HEIGHT" ] && [ ! -z "$BEST_HASH" ]; then
            NODE_HEIGHTS[$NODE]=$HEIGHT
            NODE_TIPS[$NODE]=$BEST_HASH
            NODE_VERSIONS[$NODE]=$VERSION

            echo -e "${BLUE}  $NODE${NC}: height=$HEIGHT tip=${BEST_HASH:0:12}... version=$VERSION"
        else
            echo -e "${YELLOW}  $NODE: RPC error${NC}"
        fi
    done

    # Detect forks by comparing tips
    UNIQUE_TIPS=($(printf '%s\n' "${NODE_TIPS[@]}" | sort -u))
    NUM_UNIQUE_TIPS=${#UNIQUE_TIPS[@]}

    # Create hash of current tip configuration
    CURRENT_TIPS_HASH=$(printf '%s\n' "${NODE_TIPS[@]}" | sort | md5sum | awk '{print $1}')

    echo ""

    if [ $NUM_UNIQUE_TIPS -gt 1 ]; then
        # FORK DETECTED

        if [ "$FORK_STATE" = "none" ]; then
            # New fork started
            FORK_STATE="forked"
            FORK_START_TIME=$CURRENT_TIME
            FORK_ID="fork_${TIMESTAMP}"

            echo -e "${YELLOW}⚠️  Fork detected (NEW)${NC}"
            echo -e "${YELLOW}   Tracking fork duration... (min: ${MIN_FORK_DURATION}s)${NC}"

            log "${YELLOW}Fork detected at $TIMESTAMP - tracking duration${NC}"

        else
            # Fork continues
            FORK_DURATION=$((CURRENT_TIME - FORK_START_TIME))

            echo -e "${YELLOW}⚠️  Fork ONGOING (duration: ${FORK_DURATION}s)${NC}"

            if [ $FORK_DURATION -ge $MIN_FORK_DURATION ]; then
                echo -e "${RED}   🔥 SUSTAINED FORK! (${FORK_DURATION}s >= ${MIN_FORK_DURATION}s)${NC}"
            fi
        fi

        # Show fork details
        echo -e "${YELLOW}   ${NUM_UNIQUE_TIPS} different chain tips:${NC}"
        for tip in "${UNIQUE_TIPS[@]}"; do
            echo -e "${YELLOW}   Tip ${tip:0:16}...${NC}"
            for NODE in "${!NODE_TIPS[@]}"; do
                if [ "${NODE_TIPS[$NODE]}" = "$tip" ]; then
                    echo -e "${YELLOW}     - $NODE (h=${NODE_HEIGHTS[$NODE]}, ${NODE_VERSIONS[$NODE]})${NC}"
                fi
            done
        done

    else
        # NO FORK (all nodes synchronized)

        if [ "$FORK_STATE" = "forked" ]; then
            # Fork just resolved
            FORK_DURATION=$((CURRENT_TIME - FORK_START_TIME))

            echo -e "${GREEN}✓ Fork RESOLVED after ${FORK_DURATION}s${NC}"

            if [ $FORK_DURATION -ge $MIN_FORK_DURATION ]; then
                # This was a sustained fork
                echo -e "${RED}   🔥 SUSTAINED FORK LOGGED (${FORK_DURATION}s)${NC}"

                log_fork "${RED}========================================${NC}"
                log_fork "${RED}SUSTAINED FORK: $FORK_ID${NC}"
                log_fork "Start: $(date -d @${FORK_START_TIME} +'%Y-%m-%d %H:%M:%S')"
                log_fork "End: $(date +'%Y-%m-%d %H:%M:%S')"
                log_fork "Duration: ${FORK_DURATION}s"
                log_fork "Resolved to tip: ${UNIQUE_TIPS[0]:0:16}..."
                log_fork ""

            else
                # This was just a transient fork (propagation delay)
                echo -e "${GREEN}   (Transient fork - only ${FORK_DURATION}s)${NC}"

                log_transient "Transient fork: ${FORK_DURATION}s (< ${MIN_FORK_DURATION}s threshold)"
            fi

            # Reset fork state
            FORK_STATE="none"
            FORK_START_TIME=0
            FORK_ID=""
        else
            # No fork, still synchronized
            echo -e "${GREEN}✓ Network synchronized - all nodes on same tip${NC}"
            echo -e "${GREEN}   Tip: ${UNIQUE_TIPS[0]:0:16}...${NC}"
        fi
    fi

    # Check height consensus
    UNIQUE_HEIGHTS=($(printf '%s\n' "${NODE_HEIGHTS[@]}" | sort -u -n))
    NUM_UNIQUE_HEIGHTS=${#UNIQUE_HEIGHTS[@]}

    if [ $NUM_UNIQUE_HEIGHTS -gt 1 ]; then
        HEIGHT_RANGE="${UNIQUE_HEIGHTS[0]}-${UNIQUE_HEIGHTS[-1]}"
        echo -e "${BLUE}   Height variance: $HEIGHT_RANGE${NC}"
    fi

    PREVIOUS_TIPS_HASH=$CURRENT_TIPS_HASH

    echo ""
    echo "---"
    echo ""

    sleep $CHECK_INTERVAL
done
