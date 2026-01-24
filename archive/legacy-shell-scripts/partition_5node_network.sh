#!/bin/bash
#
# Partition 5-node network for sustained fork testing
# Adapted from manualFork.sh for node-0000 to node-0004
#
# Group A (v26): node-0001, node-0003, node-0004 (3 nodes - all interconnected)
# Group B (v27): node-0000, node-0002 (2 nodes - connected to each other)
#
# NOTE: Topology-aware partition - ensures nodes within each group can sync

echo "=== Creating Network Partition ==="
echo ""
echo "Group A (v26): node-0001, node-0003, node-0004"
echo "Group B (v27): node-0000, node-0002"
echo ""

# Define groups
GROUP_A=(node-0001 node-0003 node-0004)
GROUP_B=(node-0000 node-0002)

# Ban Group B from Group A
echo "Disconnecting Group A from Group B..."
for node_a in "${GROUP_A[@]}"; do
    for node_b in "${GROUP_B[@]}"; do
        IP_B=$(kubectl get pod $node_b -o jsonpath='{.status.podIP}' 2>/dev/null)
        if [ ! -z "$IP_B" ]; then
            warnet bitcoin rpc $node_a setban "$IP_B" add 86400 2>/dev/null
            echo "  ✓ $node_a banned $node_b ($IP_B)"
        fi
    done
done

echo ""

# Ban Group A from Group B
echo "Disconnecting Group B from Group A..."
for node_b in "${GROUP_B[@]}"; do
    for node_a in "${GROUP_A[@]}"; do
        IP_A=$(kubectl get pod $node_a -o jsonpath='{.status.podIP}' 2>/dev/null)
        if [ ! -z "$IP_A" ]; then
            warnet bitcoin rpc $node_b setban "$IP_A" add 86400 2>/dev/null
            echo "  ✓ $node_b banned $node_a ($IP_A)"
        fi
    done
done

echo ""
echo "🚨 Network partitioned into 2 islands!"
echo ""
echo "Next steps:"
echo "1. Mine blocks on Group A: warnet bitcoin rpc node-0001 generatetoaddress 5 bcrt1qxxx"
echo "2. Mine blocks on Group B: warnet bitcoin rpc node-0000 generatetoaddress 10 bcrt1qxxx"
echo "3. Let chains diverge for 1-2 minutes"
echo "4. Run: python3 analyze_fork_depth.py --node1 node-0001 --node2 node-0000"
echo "5. Reconnect: ./reconnect_5node_network.sh"
echo ""
