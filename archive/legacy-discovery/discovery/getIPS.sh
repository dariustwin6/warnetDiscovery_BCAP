#!/bin/bash
for i in {0000..0007}; do
    echo "tank-$i:"
    warnet bitcoin rpc tank-$i getnetworkinfo | grep -A5 "10.244" 2>/dev/null || echo "Node not responding"
    echo "---"
done

# Quick way to identify which IP belongs to which tank
for i in {0000..0007}; do
    echo "tank-$i IP:"
    warnet bitcoin rpc tank-$i getnetworkinfo | grep "10.244" | head -1
done
