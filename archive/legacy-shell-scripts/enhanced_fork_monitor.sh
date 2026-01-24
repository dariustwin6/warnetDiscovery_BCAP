#!/bin/bash
#
# Enhanced Fork Monitor
#
# Like persistent_monitor.sh but adds fork depth analysis
# Instantly detects forks AND measures how deep they are
#

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Try warnet namespace first, fall back to default
NAMESPACE="warnet"
RUNNING_PODS=$(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)

if [ $RUNNING_PODS -eq 0 ]; then
    NAMESPACE="default"
    RUNNING_PODS=$(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
fi

OUTPUT_DIR="${SCRIPT_DIR}/../test_results/enhanced_monitoring"
LOG_FILE="$OUTPUT_DIR/monitor.log"
SUMMARY_FILE="$OUTPUT_DIR/current_summary.txt"
FORK_DEPTH_LOG="$OUTPUT_DIR/fork_depths.log"

mkdir -p $OUTPUT_DIR

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "${GREEN}=== Enhanced Warnet Fork Monitor Started ===${NC}"
log "Namespace: $NAMESPACE"
log "Output directory: $OUTPUT_DIR"
log "Monitoring interval: 30 seconds"
log "Fork depth analysis: ENABLED"
echo ""

ITERATION=0

while true; do
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    ITERATION=$((ITERATION + 1))

    # Check if pods are running
    RUNNING_PODS=$(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)

    if [ $RUNNING_PODS -eq 0 ]; then
        echo -e "${RED}[$TIMESTAMP] No running pods detected in namespace: $NAMESPACE${NC}" | tee -a "$LOG_FILE"
        sleep 30
        continue
    fi

    echo -e "${GREEN}[Iteration $ITERATION - $TIMESTAMP] Monitoring $RUNNING_PODS active nodes in namespace: $NAMESPACE${NC}"

    # Create iteration directory
    ITER_DIR="$OUTPUT_DIR/iter_${ITERATION}_${TIMESTAMP}"
    mkdir -p "$ITER_DIR"

    # Initialize summary for this iteration
    SUMMARY="=== Network Summary - $(date) ===\n"
    SUMMARY="${SUMMARY}Namespace: $NAMESPACE\n"
    SUMMARY="${SUMMARY}Iteration: $ITERATION\n\n"

    # Get node list dynamically (exclude commander pods)
    NODE_LIST=($(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Running --no-headers 2>/dev/null | awk '{print $1}' | grep -v "^commander-"))

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

        # Get network info for version
        VERSION=$(warnet bitcoin rpc "$NODE" getnetworkinfo 2>/dev/null | grep -o '"subversion":"[^"]*"' | cut -d'"' -f4)

        if [ ! -z "$HEIGHT" ] && [ ! -z "$BEST_HASH" ]; then
            NODE_HEIGHTS[$NODE]=$HEIGHT
            NODE_TIPS[$NODE]=$BEST_HASH
            NODE_VERSIONS[$NODE]=$VERSION

            echo -e "${BLUE}  $NODE${NC}: height=$HEIGHT tip=${BEST_HASH:0:12}... version=$VERSION"

            # Collect detailed data
            warnet bitcoin rpc "$NODE" getchaintips > "$ITER_DIR/${NODE}_tips.json" 2>/dev/null
            warnet bitcoin rpc "$NODE" getpeerinfo > "$ITER_DIR/${NODE}_peers.json" 2>/dev/null
            warnet bitcoin rpc "$NODE" getmempoolinfo > "$ITER_DIR/${NODE}_mempool.json" 2>/dev/null
            warnet bitcoin rpc "$NODE" getblockchaininfo > "$ITER_DIR/${NODE}_blockchain.json" 2>/dev/null

            # Add to summary
            SUMMARY="${SUMMARY}$NODE: height=$HEIGHT version=$VERSION\n"
            SUMMARY="${SUMMARY}  tip: ${BEST_HASH:0:16}...\n"
        else
            echo -e "${YELLOW}  $NODE: Could not query (RPC error)${NC}"
        fi
    done

    # Detect forks by comparing tips
    UNIQUE_TIPS=($(printf '%s\n' "${NODE_TIPS[@]}" | sort -u))
    NUM_UNIQUE_TIPS=${#UNIQUE_TIPS[@]}

    echo ""
    if [ $NUM_UNIQUE_TIPS -gt 1 ]; then
        echo -e "${RED}⚠️  FORK DETECTED! ${NUM_UNIQUE_TIPS} different chain tips${NC}" | tee -a "$LOG_FILE"
        SUMMARY="${SUMMARY}\n⚠️  FORK DETECTED!\n"
        SUMMARY="${SUMMARY}Number of different tips: $NUM_UNIQUE_TIPS\n\n"

        # Group nodes by tip
        declare -A TIP_NODES
        declare -A TIP_FIRST_NODE  # Track first node for each tip

        for NODE in "${!NODE_TIPS[@]}"; do
            TIP="${NODE_TIPS[$NODE]}"
            if [ -z "${TIP_NODES[$TIP]}" ]; then
                TIP_NODES[$TIP]="$NODE"
                TIP_FIRST_NODE[$TIP]="$NODE"
            else
                TIP_NODES[$TIP]="${TIP_NODES[$TIP]} $NODE"
            fi
        done

        # Display fork groups
        for tip in "${UNIQUE_TIPS[@]}"; do
            SUMMARY="${SUMMARY}Tip ${tip:0:16}...\n"
            for node in ${TIP_NODES[$tip]}; do
                SUMMARY="${SUMMARY}  - $node (height=${NODE_HEIGHTS[$node]}, ${NODE_VERSIONS[$node]})\n"
            done
            SUMMARY="${SUMMARY}\n"
        done

        # FORK DEPTH ANALYSIS
        echo ""
        echo -e "${MAGENTA}📊 Analyzing fork depth...${NC}"

        # Get two representative nodes (one from each tip)
        TIP_ARRAY=(${UNIQUE_TIPS[@]})
        NODE1="${TIP_FIRST_NODE[${TIP_ARRAY[0]}]}"
        NODE2="${TIP_FIRST_NODE[${TIP_ARRAY[1]}]}"

        # Run fork depth analysis
        DEPTH_ANALYSIS=$(python3 "${SCRIPT_DIR}/analyze_fork_depth.py" --node1 "$NODE1" --node2 "$NODE2" 2>&1)
        DEPTH_EXIT_CODE=$?

        if [ $DEPTH_EXIT_CODE -eq 1 ]; then
            # Fork detected with depth
            echo "$DEPTH_ANALYSIS"
            echo "$DEPTH_ANALYSIS" >> "$ITER_DIR/fork_depth_analysis.txt"

            # Extract fork depth from output
            FORK_DEPTH=$(echo "$DEPTH_ANALYSIS" | grep "Total:" | awk '{print $2}')

            if [ ! -z "$FORK_DEPTH" ]; then
                echo -e "${MAGENTA}Fork depth: $FORK_DEPTH blocks${NC}"
                SUMMARY="${SUMMARY}Fork depth: $FORK_DEPTH blocks\n"

                # Log to fork depth history
                echo "[$TIMESTAMP] Fork depth: $FORK_DEPTH blocks (nodes: $NODE1 vs $NODE2)" >> "$FORK_DEPTH_LOG"
            fi
        elif [ $DEPTH_EXIT_CODE -eq 0 ]; then
            echo -e "${GREEN}Fork depth analysis: No fork (nodes re-synced?)${NC}"
        else
            echo -e "${YELLOW}Fork depth analysis failed${NC}"
            echo "$DEPTH_ANALYSIS"
        fi

        # Save fork detection
        echo "$TIMESTAMP" >> "$OUTPUT_DIR/fork_events.log"

    else
        echo -e "${GREEN}✓ Network synchronized - all nodes on same tip${NC}"
        SUMMARY="${SUMMARY}\n✓ Network synchronized\n"
        SUMMARY="${SUMMARY}Common tip: ${UNIQUE_TIPS[0]:0:16}...\n"
    fi

    # Check height consensus
    UNIQUE_HEIGHTS=($(printf '%s\n' "${NODE_HEIGHTS[@]}" | sort -u -n))
    NUM_UNIQUE_HEIGHTS=${#UNIQUE_HEIGHTS[@]}

    if [ $NUM_UNIQUE_HEIGHTS -gt 1 ]; then
        HEIGHT_RANGE="${UNIQUE_HEIGHTS[0]}-${UNIQUE_HEIGHTS[-1]}"
        echo -e "${YELLOW}⚠️  Height variance: $HEIGHT_RANGE${NC}"
        SUMMARY="${SUMMARY}Height range: $HEIGHT_RANGE\n"
    fi

    # Save summary
    echo -e "$SUMMARY" > "$SUMMARY_FILE"
    echo -e "$SUMMARY" > "$ITER_DIR/summary.txt"

    echo ""
    echo "---"
    echo ""

    sleep 30
done
