#!/bin/bash
#
# Natural Fork Development Test
#
# Workflow:
# 1. Start enhanced fork monitor (tracks timing and depth)
# 2. Start miner_std scenario (continuous natural mining)
# 3. Wait for initial convergence
# 4. Partition network (mining continues naturally)
# 5. Observe natural fork development with timing metrics
# 6. After desired time, reconnect and observe reorg
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Configuration
FORK_DURATION=${1:-120}  # Default: 2 minutes of natural fork development

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Natural Fork Development Test${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "This test demonstrates:"
echo "  - Natural mining on partitioned network"
echo "  - Real-world fork timing and depth"
echo "  - Progressive fork depth tracking"
echo "  - Natural chain reorganization"
echo ""
echo "Fork duration: ${FORK_DURATION}s"
echo ""

# Step 1: Start enhanced fork monitor in background
echo -e "${GREEN}Step 1: Starting enhanced fork monitor${NC}"
MONITOR_LOG="../test_results/natural_fork_test_$(date +%Y%m%d_%H%M%S).log"
mkdir -p ../test_results
./enhanced_fork_monitor.sh > "$MONITOR_LOG" 2>&1 &
MONITOR_PID=$!
echo "  Monitor PID: $MONITOR_PID"
echo "  Logging to: $MONITOR_LOG"
sleep 5
echo ""

# Step 2: Check if miner is already running
echo -e "${GREEN}Step 2: Checking for active miner${NC}"
MINER_POD=$(kubectl get pods -n default --no-headers 2>/dev/null | grep "^commander-" | awk '{print $1}' | head -1)

if [ -z "$MINER_POD" ]; then
    echo "  No miner running, starting miner_std scenario..."
    cd ../../..
    warnet run warnet/scenarios/miner_std.py --interval 5 > /dev/null 2>&1 &
    MINER_PID=$!
    cd "$SCRIPT_DIR"
    echo "  Miner started (PID: $MINER_PID)"
    echo "  Waiting 30s for mining to begin..."
    sleep 30
else
    echo "  Miner already running: $MINER_POD"
fi
echo ""

# Step 3: Verify nodes are synchronized
echo -e "${GREEN}Step 3: Verifying initial synchronization${NC}"
sleep 5
TIPS=($(for node in node-0000 node-0001 node-0002 node-0003 node-0004; do
    warnet bitcoin rpc "$node" getbestblockhash 2>/dev/null
done | sort -u))

if [ ${#TIPS[@]} -eq 1 ]; then
    echo -e "  ${GREEN}✓${NC} All nodes synchronized on same tip"
    echo "    Tip: ${TIPS[0]:0:16}..."
else
    echo -e "  ${YELLOW}⚠${NC} Nodes not fully synchronized yet (${#TIPS[@]} different tips)"
    echo "    Waiting 10s for convergence..."
    sleep 10
fi
echo ""

# Step 4: Partition network (while mining continues!)
echo -e "${GREEN}Step 4: Partitioning network${NC}"
echo -e "  ${YELLOW}>>> Natural mining will continue on both isolated groups${NC}"
echo ""
./partition_5node_network.sh
echo ""

# Step 5: Record partition start time
PARTITION_START=$(date +%s)
echo -e "${MAGENTA}Fork development phase started${NC}"
echo "  Start time: $(date +'%Y-%m-%d %H:%M:%S')"
echo "  Duration: ${FORK_DURATION}s"
echo ""
echo -e "${YELLOW}Watching natural fork develop...${NC}"
echo "(Check monitor log for real-time fork depth: tail -f $MONITOR_LOG)"
echo ""

# Track fork depth over time
echo "Time(s) | Group A Height | Group B Height | Fork Detected"
echo "--------|----------------|----------------|---------------"

for ((i=0; i<=$FORK_DURATION; i+=10)); do
    sleep 10

    # Get heights (using representative nodes from each group)
    # Group A: node-0001, node-0003, node-0004 (v26)
    # Group B: node-0000, node-0002 (v27)
    HEIGHT_A=$(warnet bitcoin rpc node-0001 getblockcount 2>/dev/null || echo "?")
    HEIGHT_B=$(warnet bitcoin rpc node-0000 getblockcount 2>/dev/null || echo "?")

    # Check if forked
    TIP_A=$(warnet bitcoin rpc node-0001 getbestblockhash 2>/dev/null || echo "")
    TIP_B=$(warnet bitcoin rpc node-0000 getbestblockhash 2>/dev/null || echo "")

    if [ "$TIP_A" != "$TIP_B" ] && [ ! -z "$TIP_A" ] && [ ! -z "$TIP_B" ]; then
        FORK_STATUS="YES"
    else
        FORK_STATUS="no"
    fi

    printf "%7d | %14s | %14s | %s\n" $i "$HEIGHT_A" "$HEIGHT_B" "$FORK_STATUS"
done

echo ""

# Step 6: Reconnect and observe reorg
PARTITION_END=$(date +%s)
PARTITION_DURATION=$((PARTITION_END - PARTITION_START))

echo ""
echo -e "${GREEN}Step 6: Natural fork development complete${NC}"
echo "  Duration: ${PARTITION_DURATION}s"
echo ""

# Get final fork state before reconnection
echo "Final fork state:"
for node in node-0000 node-0001 node-0002 node-0003 node-0004; do
    HEIGHT=$(warnet bitcoin rpc "$node" getblockcount 2>/dev/null || echo "ERROR")
    TIP=$(warnet bitcoin rpc "$node" getbestblockhash 2>/dev/null || echo "ERROR")
    echo "  $node: height=$HEIGHT, tip=${TIP:0:16}..."
done
echo ""

read -p "Press ENTER to reconnect network and observe natural reorg... "
echo ""

echo -e "${GREEN}Step 7: Reconnecting network${NC}"
REORG_START=$(date +%s)
./reconnect_5node_network.sh
echo ""

echo -e "${YELLOW}Observing chain reorganization...${NC}"
sleep 5

# Track convergence
echo ""
echo "Time(s) | Unique Tips | All Converged?"
echo "--------|-------------|---------------"

for ((i=0; i<=60; i+=5)); do
    sleep 5

    TIPS=($(for node in node-0000 node-0001 node-0002 node-0003 node-0004; do
        warnet bitcoin rpc "$node" getbestblockhash 2>/dev/null
    done | sort -u))

    NUM_TIPS=${#TIPS[@]}

    if [ $NUM_TIPS -eq 1 ]; then
        CONVERGED="YES"
        printf "%7d | %11d | %s\n" $i "$NUM_TIPS" "$CONVERGED"
        break
    else
        CONVERGED="no"
        printf "%7d | %11d | %s\n" $i "$NUM_TIPS" "$CONVERGED"
    fi
done

REORG_END=$(date +%s)
REORG_DURATION=$((REORG_END - REORG_START))

echo ""
echo -e "${GREEN}Step 8: Final state${NC}"
for node in node-0000 node-0001 node-0002 node-0003 node-0004; do
    HEIGHT=$(warnet bitcoin rpc "$node" getblockcount 2>/dev/null || echo "ERROR")
    TIP=$(warnet bitcoin rpc "$node" getbestblockhash 2>/dev/null || echo "ERROR")
    echo "  $node: height=$HEIGHT, tip=${TIP:0:16}..."
done
echo ""

# Stop monitor
echo -e "${GREEN}Step 9: Stopping monitor${NC}"
kill $MONITOR_PID 2>/dev/null || true
echo "  Monitor logs saved to: $MONITOR_LOG"
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Natural Fork Test Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Summary:"
echo "  - Partition duration: ${PARTITION_DURATION}s"
echo "  - Reorg duration: ${REORG_DURATION}s"
echo "  - Monitor log: $MONITOR_LOG"
echo ""
echo "Analysis:"
echo "  1. Check monitor log for fork depth progression"
echo "  2. Extract timing metrics for fork detection"
echo "  3. Analyze natural mining behavior under partition"
echo "  4. Compare v26 vs v27 mining rates"
echo ""
echo "For detailed fork depth history:"
echo "  cat ../test_results/enhanced_monitoring/fork_depths.log"
echo ""
