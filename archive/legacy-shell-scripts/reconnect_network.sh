#!/bin/bash

echo "=== Reconnecting Warnet Network ==="
echo ""

# Method 1: Clear all bans using clearbanned
echo "Clearing all bans..."
for i in {0..7}; do
    NODE="tank-$(printf '%04d' $i)"
    
    # Check if node is running
    POD_STATUS=$(kubectl get pod $NODE -o jsonpath='{.status.phase}' 2>/dev/null)
    
    if [ "$POD_STATUS" = "Running" ]; then
        # Clear all bans at once
        RESULT=$(warnet bitcoin rpc $NODE clearbanned 2>&1)
        
        if [ $? -eq 0 ]; then
            echo "✓ $NODE: All bans cleared"
        else
            echo "✗ $NODE: Error clearing bans - $RESULT"
        fi
    else
        echo "⊘ $NODE: Not running (status: $POD_STATUS)"
    fi
done

echo ""
echo "=== Forcing Peer Reconnections ==="

# Get all node IPs
declare -A NODE_IPS
for i in {0..7}; do
    NODE="tank-$(printf '%04d' $i)"
    IP=$(kubectl get pod $NODE -o jsonpath='{.status.podIP}' 2>/dev/null)
    if [ ! -z "$IP" ]; then
        NODE_IPS[$NODE]=$IP
    fi
done

# Force connections between all nodes
for i in {0..7}; do
    NODE_A="tank-$(printf '%04d' $i)"
    
    if [ "${NODE_IPS[$NODE_A]}" ]; then
        echo "Connecting $NODE_A to other nodes..."
        
        for j in {0..7}; do
            if [ $i -ne $j ]; then
                NODE_B="tank-$(printf '%04d' $j)"
                IP_B="${NODE_IPS[$NODE_B]}"
                
                if [ ! -z "$IP_B" ]; then
                    # Add node as a peer
                    warnet bitcoin rpc $NODE_A addnode "$IP_B" "onetry" 2>/dev/null
                fi
            fi
        done
        echo "  ✓ Connection attempts sent"
    fi
done

echo ""
echo "=== Verification ==="
echo "Waiting 10 seconds for connections to establish..."
sleep 10

# Check peer counts
echo ""
for i in {0..7}; do
    NODE="tank-$(printf '%04d' $i)"
    PEER_COUNT=$(warnet bitcoin rpc $NODE getconnectioncount 2>/dev/null)
    
    if [ ! -z "$PEER_COUNT" ]; then
        if [ "$PEER_COUNT" -gt 0 ]; then
            echo "✓ $NODE: $PEER_COUNT peers connected"
        else
            echo "⚠ $NODE: No peers connected yet"
        fi
    fi
done

echo ""
echo "✓ Network reconnection complete!"
echo "Watch your monitor for reorg resolution..."
