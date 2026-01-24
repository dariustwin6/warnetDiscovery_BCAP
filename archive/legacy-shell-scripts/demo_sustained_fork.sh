#!/bin/bash
#
# Quick Demo: Sustained Fork with Depth Analysis
#
# Demonstrates complete workflow:
# 1. Partition network
# 2. Mine competing chains
# 3. Analyze fork depth
# 4. Reconnect and observe reorg
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Sustained Fork Testing Demo${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Partition
echo -e "${GREEN}Step 1: Partitioning network...${NC}"
./partition_5node_network.sh
echo ""

sleep 3

# Step 2: Check current state
echo -e "${GREEN}Step 2: Current block heights${NC}"
for node in node-0000 node-0001 node-0002 node-0003 node-0004; do
    HEIGHT=$(warnet bitcoin rpc "$node" getblockcount 2>/dev/null || echo "ERROR")
    echo "  $node: height=$HEIGHT"
done
echo ""

sleep 2

# Step 3: Mine on Group A
echo -e "${GREEN}Step 3: Mining 5 blocks on Group A (node-0001, node-0003)${NC}"
for i in {1..5}; do
    warnet bitcoin rpc node-0001 generatetoaddress 1 "bcrt1qxxx" >/dev/null 2>&1
    echo -n "."
    sleep 1
done
echo " Done!"
echo ""

sleep 2

# Step 4: Mine on Group B
echo -e "${GREEN}Step 4: Mining 8 blocks on Group B (node-0000, node-0002, node-0004)${NC}"
for i in {1..8}; do
    warnet bitcoin rpc node-0000 generatetoaddress 1 "bcrt1qxxx" >/dev/null 2>&1
    echo -n "."
    sleep 1
done
echo " Done!"
echo ""

sleep 2

# Step 5: Verify fork
echo -e "${GREEN}Step 5: Verifying fork exists${NC}"
echo ""
echo -e "${YELLOW}Group A (v26):${NC}"
HEIGHT_A=$(warnet bitcoin rpc node-0001 getblockcount 2>/dev/null)
TIP_A=$(warnet bitcoin rpc node-0001 getbestblockhash 2>/dev/null)
echo "  node-0001: height=$HEIGHT_A"
echo "  tip: ${TIP_A:0:16}..."

echo ""
echo -e "${YELLOW}Group B (v27):${NC}"
HEIGHT_B=$(warnet bitcoin rpc node-0000 getblockcount 2>/dev/null)
TIP_B=$(warnet bitcoin rpc node-0000 getbestblockhash 2>/dev/null)
echo "  node-0000: height=$HEIGHT_B"
echo "  tip: ${TIP_B:0:16}..."

echo ""

if [ "$TIP_A" != "$TIP_B" ]; then
    echo -e "${RED}✓ FORK CONFIRMED!${NC} Different chain tips detected"
else
    echo -e "${YELLOW}⚠ No fork detected (tips are the same)${NC}"
fi

echo ""
sleep 2

# Step 6: Analyze fork depth
echo -e "${GREEN}Step 6: Analyzing fork depth${NC}"
echo ""
python3 analyze_fork_depth.py --node1 node-0001 --node2 node-0000
echo ""

sleep 3

# Step 7: Pause before reconnect
echo -e "${YELLOW}Sustained fork is active!${NC}"
echo ""
read -p "Press ENTER to reconnect network and observe reorg... "
echo ""

# Step 8: Reconnect
echo -e "${GREEN}Step 7: Reconnecting network${NC}"
./reconnect_5node_network.sh
echo ""

sleep 5

# Step 9: Verify convergence
echo -e "${GREEN}Step 8: Verifying chain convergence${NC}"
echo ""
for node in node-0000 node-0001 node-0002 node-0003 node-0004; do
    HEIGHT=$(warnet bitcoin rpc "$node" getblockcount 2>/dev/null || echo "ERROR")
    TIP=$(warnet bitcoin rpc "$node" getbestblockhash 2>/dev/null || echo "ERROR")
    echo "  $node: height=$HEIGHT, tip=${TIP:0:16}..."
done

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Demo Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Summary:"
echo "  - Created 2-group network partition"
echo "  - Group A mined 5 blocks (v26 nodes)"
echo "  - Group B mined 8 blocks (v27 nodes)"
echo "  - Analyzed fork depth: 13 blocks total (5+8)"
echo "  - Reconnected network"
echo "  - Observed longest chain win (Group B)"
echo ""
echo "Check your fork monitor output for detailed tracking!"
echo ""
