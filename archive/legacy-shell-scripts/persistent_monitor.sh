#!/bin/bash

# Try warnet namespace first, fall back to default
NAMESPACE="warnet"
RUNNING_PODS=$(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)

if [ $RUNNING_PODS -eq 0 ]; then
    # Try default namespace
    NAMESPACE="default"
    RUNNING_PODS=$(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
fi

OUTPUT_DIR="test_results/live_monitoring"
LOG_FILE="$OUTPUT_DIR/monitor.log"
SUMMARY_FILE="$OUTPUT_DIR/current_summary.txt"

mkdir -p $OUTPUT_DIR

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "${GREEN}=== Warnet Persistent Monitor Started ===${NC}"
log "Namespace: $NAMESPACE"
log "Output directory: $OUTPUT_DIR"
log "Monitoring interval: 30 seconds"
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
    
    # Arrays to track heights and tips
    declare -a HEIGHTS
    declare -a TIPS
    declare -a VERSIONS
    
    # Collect data from each node
    for i in {0..7}; do
        NODE="tank-$(printf '%04d' $i)"
        
        # Check if this specific pod is running
        POD_STATUS=$(kubectl get pod $NODE -n $NAMESPACE -o jsonpath='{.status.phase}' 2>/dev/null)
        
        if [ "$POD_STATUS" = "Running" ]; then
            # Get block count
            HEIGHT=$(warnet bitcoin rpc $NODE getblockcount 2>/dev/null | tr -d '\r\n')
            
            # Get best block hash
            BEST_HASH=$(warnet bitcoin rpc $NODE getbestblockhash 2>/dev/null | tr -d '\r\n')
            
            # Get network info for version
            VERSION=$(warnet bitcoin rpc $NODE getnetworkinfo 2>/dev/null | grep -o '"subversion":"[^"]*"' | cut -d'"' -f4)
            
            if [ ! -z "$HEIGHT" ]; then
                HEIGHTS[$i]=$HEIGHT
                TIPS[$i]=$BEST_HASH
                VERSIONS[$i]=$VERSION
                
                echo -e "${BLUE}  $NODE${NC}: height=$HEIGHT tip=${BEST_HASH:0:12}... version=$VERSION"
                
                # Collect detailed data
                warnet bitcoin rpc $NODE getchaintips > "$ITER_DIR/${NODE}_tips.json" 2>/dev/null
                warnet bitcoin rpc $NODE getpeerinfo > "$ITER_DIR/${NODE}_peers.json" 2>/dev/null
                warnet bitcoin rpc $NODE getmempoolinfo > "$ITER_DIR/${NODE}_mempool.json" 2>/dev/null
                warnet bitcoin rpc $NODE getblockchaininfo > "$ITER_DIR/${NODE}_blockchain.json" 2>/dev/null
                
                # Add to summary
                SUMMARY="${SUMMARY}$NODE: height=$HEIGHT version=$VERSION\n"
                SUMMARY="${SUMMARY}  tip: ${BEST_HASH:0:16}...\n"
            else
                echo -e "${YELLOW}  $NODE: Could not query (RPC error)${NC}"
            fi
        else
            echo -e "${RED}  $NODE: Not running (status: $POD_STATUS)${NC}"
        fi
    done
    
    # Detect forks by comparing tips
    UNIQUE_TIPS=($(printf '%s\n' "${TIPS[@]}" | sort -u))
    NUM_UNIQUE_TIPS=${#UNIQUE_TIPS[@]}
    
    echo ""
    if [ $NUM_UNIQUE_TIPS -gt 1 ]; then
        echo -e "${RED}⚠️  FORK DETECTED! ${NUM_UNIQUE_TIPS} different chain tips${NC}" | tee -a "$LOG_FILE"
        SUMMARY="${SUMMARY}\n⚠️  FORK DETECTED!\n"
        SUMMARY="${SUMMARY}Number of different tips: $NUM_UNIQUE_TIPS\n\n"
        
        # Group nodes by tip
        for tip in "${UNIQUE_TIPS[@]}"; do
            SUMMARY="${SUMMARY}Tip ${tip:0:16}...\n"
            for i in {0..7}; do
                if [ "${TIPS[$i]}" = "$tip" ]; then
                    NODE="tank-$(printf '%04d' $i)"
                    SUMMARY="${SUMMARY}  - $NODE (height=${HEIGHTS[$i]}, ${VERSIONS[$i]})\n"
                fi
            done
            SUMMARY="${SUMMARY}\n"
        done
        
        # Save fork detection
        echo "$TIMESTAMP" >> "$OUTPUT_DIR/fork_events.log"
    else
        echo -e "${GREEN}✓ Network synchronized - all nodes on same tip${NC}"
        SUMMARY="${SUMMARY}\n✓ Network synchronized\n"
    fi
    
    # Check height consensus
    UNIQUE_HEIGHTS=($(printf '%s\n' "${HEIGHTS[@]}" | sort -u))
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
