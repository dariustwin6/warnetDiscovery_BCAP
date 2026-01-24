#!/bin/bash
#
# Reconnect 5-node network after partition
# Adapted from reconnect_network.sh for node-0000 to node-0004
#

echo "=== Reconnecting 5-Node Warnet Network ==="
echo ""

NODES=(node-0000 node-0001 node-0002 node-0003 node-0004)

# Method 1: Clear all bans
echo "Step 1: Clearing all bans..."
for node in "${NODES[@]}"; do
    POD_STATUS=$(kubectl get pod $node -o jsonpath='{.status.phase}' 2>/dev/null)

    if [ "$POD_STATUS" = "Running" ]; then
        RESULT=$(warnet bitcoin rpc $node clearbanned 2>&1)

        if [ $? -eq 0 ]; then
            echo "  ✓ $node: All bans cleared"
        else
            echo "  ✗ $node: Error clearing bans"
        fi
    else
        echo "  ⊘ $node: Not running"
    fi
done

echo ""
echo "Step 2: Forcing peer reconnections..."

# Get all node IPs
declare -A NODE_IPS
for node in "${NODES[@]}"; do
    IP=$(kubectl get pod $node -o jsonpath='{.status.podIP}' 2>/dev/null)
    if [ ! -z "$IP" ]; then
        NODE_IPS[$node]=$IP
    fi
done

# Force connections
for node_a in "${NODES[@]}"; do
    if [ "${NODE_IPS[$node_a]}" ]; then
        for node_b in "${NODES[@]}"; do
            if [ "$node_a" != "$node_b" ]; then
                IP_B="${NODE_IPS[$node_b]}"

                if [ ! -z "$IP_B" ]; then
                    warnet bitcoin rpc $node_a addnode "$IP_B" "onetry" 2>/dev/null
                fi
            fi
        done
        echo "  ✓ $node_a: Connection attempts sent"
    fi
done

echo ""
echo "Step 3: Waiting for connections to establish..."
sleep 10

# Verify peer counts
echo ""
echo "Verification:"
for node in "${NODES[@]}"; do
    PEER_COUNT=$(warnet bitcoin rpc $node getconnectioncount 2>/dev/null)

    if [ ! -z "$PEER_COUNT" ]; then
        if [ "$PEER_COUNT" -gt 0 ]; then
            echo "  ✓ $node: $PEER_COUNT peers connected"
        else
            echo "  ⚠ $node: No peers connected yet"
        fi
    fi
done

echo ""
echo "✓ Network reconnection complete!"
echo ""
echo "Next: Watch for chain reorganization in your monitor"
echo "The longest chain should win and nodes will reorg"
echo ""
