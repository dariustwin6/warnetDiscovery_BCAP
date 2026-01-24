#!/bin/bash
#
# Partition Utility Functions
# Dynamic network topology control for Bitcoin version-based partitioning
#

# Get pod IP address
get_node_ip() {
    local node=$1
    kubectl get pod "$node" -o jsonpath='{.status.podIP}' 2>/dev/null
}

# Get nodes by version from network.yaml
get_nodes_by_version() {
    local version=$1
    local network_yaml=$2

    if [ ! -f "$network_yaml" ]; then
        echo "Error: Network config not found: $network_yaml" >&2
        return 1
    fi

    # Extract node names matching version pattern using Python
    python3 -c "
import yaml
import sys

try:
    with open('$network_yaml', 'r') as f:
        config = yaml.safe_load(f)

    for node in config.get('nodes', []):
        if node.get('image', {}).get('tag') == '$version':
            print(node.get('name', ''))
except Exception as e:
    print(f'Error parsing YAML: {e}', file=sys.stderr)
    sys.exit(1)
"
}

# Create partition between two version groups
partition_by_version() {
    local network_yaml=$1
    local v27_version=${2:-"27.0"}
    local v26_version=${3:-"26.0"}
    local ban_duration=${4:-86400}  # 24 hours default

    echo "=== Creating Version-Based Partition ==="
    echo ""

    # Get node lists
    local v27_nodes=($(get_nodes_by_version "$v27_version" "$network_yaml"))
    local v26_nodes=($(get_nodes_by_version "$v26_version" "$network_yaml"))

    if [ ${#v27_nodes[@]} -eq 0 ] || [ ${#v26_nodes[@]} -eq 0 ]; then
        echo "Error: Could not find nodes for both versions" >&2
        echo "  v$v27_version nodes: ${#v27_nodes[@]}" >&2
        echo "  v$v26_version nodes: ${#v26_nodes[@]}" >&2
        return 1
    fi

    echo "Partition Groups:"
    echo "  v$v27_version: ${#v27_nodes[@]} nodes (${v27_nodes[*]})"
    echo "  v$v26_version: ${#v26_nodes[@]} nodes (${v26_nodes[*]})"
    echo ""

    # Ban v26 nodes from v27 nodes (parallel execution)
    echo "Disconnecting v$v27_version from v$v26_version..."
    local ban_count=0
    local pids=()

    for v27_node in "${v27_nodes[@]}"; do
        for v26_node in "${v26_nodes[@]}"; do
            local v26_ip=$(get_node_ip "$v26_node")
            if [ ! -z "$v26_ip" ]; then
                # Run setban in background for parallel execution
                (
                    if warnet bitcoin rpc "$v27_node" setban "$v26_ip" add "$ban_duration" 2>/dev/null; then
                        echo "  ✓ $v27_node banned $v26_node ($v26_ip)"
                    else
                        echo "  ✗ $v27_node failed to ban $v26_node" >&2
                    fi
                ) &
                pids+=($!)
            fi
        done
    done

    # Wait for all v27->v26 bans to complete
    echo "  Waiting for ${#pids[@]} ban operations to complete..."
    for pid in "${pids[@]}"; do
        wait "$pid" && ((ban_count++)) || true
    done

    echo ""

    # Ban v27 nodes from v26 nodes (parallel execution)
    echo "Disconnecting v$v26_version from v$v27_version..."
    pids=()

    for v26_node in "${v26_nodes[@]}"; do
        for v27_node in "${v27_nodes[@]}"; do
            local v27_ip=$(get_node_ip "$v27_node")
            if [ ! -z "$v27_ip" ]; then
                # Run setban in background for parallel execution
                (
                    if warnet bitcoin rpc "$v26_node" setban "$v27_ip" add "$ban_duration" 2>/dev/null; then
                        echo "  ✓ $v26_node banned $v27_node ($v27_ip)"
                    else
                        echo "  ✗ $v26_node failed to ban $v27_node" >&2
                    fi
                ) &
                pids+=($!)
            fi
        done
    done

    # Wait for all v26->v27 bans to complete
    echo "  Waiting for ${#pids[@]} ban operations to complete..."
    for pid in "${pids[@]}"; do
        wait "$pid" && ((ban_count++)) || true
    done

    echo ""
    echo "🚨 Network partitioned into 2 version-based islands!"
    echo "   Total bans applied: $ban_count"
    echo ""

    return 0
}

# Reconnect all nodes (clear bans and force connections)
reconnect_all() {
    local network_yaml=$1

    echo "=== Reconnecting Network ==="
    echo ""

    # Get all nodes
    local all_nodes=($(yq eval '.nodes[] | .name' "$network_yaml" 2>/dev/null))

    if [ ${#all_nodes[@]} -eq 0 ]; then
        echo "Error: Could not find nodes in $network_yaml" >&2
        return 1
    fi

    echo "Step 1: Clearing all bans..."
    local cleared_count=0
    for node in "${all_nodes[@]}"; do
        if warnet bitcoin rpc "$node" clearbanned 2>/dev/null; then
            echo "  ✓ $node: Bans cleared"
            ((cleared_count++))
        else
            echo "  ✗ $node: Failed to clear bans" >&2
        fi
    done

    echo ""
    echo "Step 2: Forcing peer reconnections..."

    # Build IP map
    declare -A node_ips
    for node in "${all_nodes[@]}"; do
        local ip=$(get_node_ip "$node")
        if [ ! -z "$ip" ]; then
            node_ips[$node]=$ip
        fi
    done

    # Force connections
    local connection_count=0
    for node_a in "${all_nodes[@]}"; do
        if [ "${node_ips[$node_a]}" ]; then
            for node_b in "${all_nodes[@]}"; do
                if [ "$node_a" != "$node_b" ] && [ "${node_ips[$node_b]}" ]; then
                    warnet bitcoin rpc "$node_a" addnode "${node_ips[$node_b]}" "onetry" 2>/dev/null
                    ((connection_count++))
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
    for node in "${all_nodes[@]}"; do
        local peer_count=$(warnet bitcoin rpc "$node" getconnectioncount 2>/dev/null)

        if [ ! -z "$peer_count" ]; then
            if [ "$peer_count" -gt 0 ]; then
                echo "  ✓ $node: $peer_count peers connected"
            else
                echo "  ⚠ $node: No peers connected yet"
            fi
        fi
    done

    echo ""
    echo "✓ Network reconnection complete!"
    echo "   Bans cleared: $cleared_count"
    echo "   Connection attempts: $connection_count"
    echo ""

    return 0
}

# Verify partition isolation
verify_partition_isolation() {
    local network_yaml=$1
    local v27_version=${2:-"27.0"}
    local v26_version=${3:-"26.0"}

    echo "=== Verifying Partition Isolation ==="
    echo ""

    # Get node lists
    local v27_nodes=($(get_nodes_by_version "$v27_version" "$network_yaml"))
    local v26_nodes=($(get_nodes_by_version "$v26_version" "$network_yaml"))

    # Build IP sets
    declare -A v27_ips
    declare -A v26_ips

    for node in "${v27_nodes[@]}"; do
        local ip=$(get_node_ip "$node")
        [ ! -z "$ip" ] && v27_ips[$ip]=1
    done

    for node in "${v26_nodes[@]}"; do
        local ip=$(get_node_ip "$node")
        [ ! -z "$ip" ] && v26_ips[$ip]=1
    done

    # Check v27 nodes don't have v26 peers
    echo "Checking v$v27_version nodes..."
    local isolated=true
    for node in "${v27_nodes[@]}"; do
        local peers=$(warnet bitcoin rpc "$node" getpeerinfo 2>/dev/null | jq -r '.[].addr' | cut -d: -f1)
        local cross_partition_peers=0

        for peer_ip in $peers; do
            if [ "${v26_ips[$peer_ip]}" ]; then
                echo "  ✗ $node has v$v26_version peer: $peer_ip"
                isolated=false
                ((cross_partition_peers++))
            fi
        done

        if [ $cross_partition_peers -eq 0 ]; then
            echo "  ✓ $node: No cross-partition peers"
        fi
    done

    echo ""
    echo "Checking v$v26_version nodes..."
    for node in "${v26_nodes[@]}"; do
        local peers=$(warnet bitcoin rpc "$node" getpeerinfo 2>/dev/null | jq -r '.[].addr' | cut -d: -f1)
        local cross_partition_peers=0

        for peer_ip in $peers; do
            if [ "${v27_ips[$peer_ip]}" ]; then
                echo "  ✗ $node has v$v27_version peer: $peer_ip"
                isolated=false
                ((cross_partition_peers++))
            fi
        done

        if [ $cross_partition_peers -eq 0 ]; then
            echo "  ✓ $node: No cross-partition peers"
        fi
    done

    echo ""
    if [ "$isolated" = true ]; then
        echo "✓ Partition verified: No cross-partition connections"
        return 0
    else
        echo "⚠ Warning: Cross-partition connections detected"
        return 1
    fi
}

# Usage examples
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    echo "Partition Utilities - Usage Examples:"
    echo ""
    echo "1. Partition by version:"
    echo "   source partition_utils.sh"
    echo "   partition_by_version /path/to/network.yaml \"27.0\" \"26.0\" 86400"
    echo ""
    echo "2. Reconnect all:"
    echo "   reconnect_all /path/to/network.yaml"
    echo ""
    echo "3. Verify isolation:"
    echo "   verify_partition_isolation /path/to/network.yaml \"27.0\" \"26.0\""
    echo ""
fi
