#!/bin/bash

# Auto-detect namespace
NAMESPACE="warnet"
PODS=$(kubectl get pods -n $NAMESPACE 2>/dev/null | grep -c "tank-")

if [ $PODS -eq 0 ]; then
    NAMESPACE="default"
fi

echo "=== Warnet Quick Status ==="
echo "Namespace: $NAMESPACE"
echo ""

# Check pod status
echo "Pod Status:"
kubectl get pods -n $NAMESPACE 2>/dev/null | grep -E "NAME|tank-" || echo "No pods found"
echo ""

# Check if monitoring data exists
if [ -f "test_results/live_monitoring/current_summary.txt" ]; then
    echo "Latest Network Summary:"
    cat test_results/live_monitoring/current_summary.txt
else
    echo "No monitoring data yet. Start the monitor with: ./tools/persistent_monitor.sh"
fi

echo ""

# Run criticality assessment if data exists
if [ -d "test_results/live_monitoring" ] && [ -n "$(ls -A test_results/live_monitoring/iter_* 2>/dev/null)" ]; then
    echo "Running criticality assessment..."
    python3 monitoring/assess_criticality.py
fi
