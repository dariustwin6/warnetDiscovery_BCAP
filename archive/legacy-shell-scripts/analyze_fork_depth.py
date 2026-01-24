#!/usr/bin/env python3
"""
Fork Depth Analyzer

Analyzes the depth of a fork by finding the common ancestor and measuring
how many blocks have been built on each competing chain.

Usage:
    python3 analyze_fork_depth.py --node1 tank-0000 --node2 tank-0001
    python3 analyze_fork_depth.py --tips TIP1_HASH TIP2_HASH --node tank-0000
"""

import subprocess
import json
import argparse
import sys
from typing import Dict, List, Tuple, Optional


def rpc_call(node: str, method: str, params: List = None) -> any:
    """Execute warnet bitcoin rpc command"""
    cmd = ['warnet', 'bitcoin', 'rpc', node, method]
    if params:
        cmd.extend([json.dumps(p) for p in params])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"RPC error for {node}.{method}: {e.stderr}", file=sys.stderr)
        return None
    except json.JSONDecodeError:
        # Some RPC calls return plain text
        return result.stdout.strip()


def get_block_header(node: str, block_hash: str, verbose: bool = True) -> Optional[Dict]:
    """Get block header information"""
    result = rpc_call(node, 'getblockheader', [block_hash, verbose])
    if result is None:
        return None
    if isinstance(result, str):
        # Non-verbose mode returned hex string
        return None
    return result


def get_block_hash(node: str, height: int) -> Optional[str]:
    """Get block hash at given height"""
    return rpc_call(node, 'getblockhash', [height])


def find_common_ancestor(node: str, tip1: str, tip2: str) -> Tuple[str, int]:
    """
    Find common ancestor block of two chain tips

    Returns:
        (common_ancestor_hash, height)
    """
    # Get headers for both tips
    header1 = get_block_header(node, tip1)
    header2 = get_block_header(node, tip2)

    if not header1 or not header2:
        return None, None

    height1 = header1.get('height')
    height2 = header2.get('height')

    if height1 is None or height2 is None:
        return None, None

    # Start from the lower height
    current_height = min(height1, height2)

    # Walk backwards until we find a common block
    while current_height >= 0:
        # Walk down from each tip to this height
        block_at_height_1 = walk_to_height(node, tip1, current_height)
        block_at_height_2 = walk_to_height(node, tip2, current_height)

        if block_at_height_1 and block_at_height_2 and block_at_height_1 == block_at_height_2:
            return block_at_height_1, current_height

        current_height -= 1

        # Safety limit - don't go back more than 1000 blocks
        if (min(height1, height2) - current_height) > 1000:
            return None, None

    return None, None


def walk_to_height(node: str, tip_hash: str, target_height: int) -> Optional[str]:
    """
    Walk backwards from a tip to a specific height

    Returns:
        Block hash at target_height on this chain
    """
    current = tip_hash
    iterations = 0
    max_iterations = 1000  # Safety limit

    while iterations < max_iterations:
        header = get_block_header(node, current)
        if not header:
            return None

        current_height = header.get('height')
        if current_height is None:
            return None

        if current_height == target_height:
            return current

        if current_height < target_height:
            # Overshot
            return None

        # Go to previous block
        previous = header.get('previousblockhash')
        if not previous:
            # Reached genesis
            return None

        current = previous
        iterations += 1

    return None


def analyze_fork_depth(node1: str, node2: str = None,
                       tip1: str = None, tip2: str = None) -> Dict:
    """
    Analyze fork depth between two nodes or two tips

    Args:
        node1: First node name (required)
        node2: Second node name (optional if tips provided)
        tip1: First chain tip hash (optional, auto-detected from node1)
        tip2: Second chain tip hash (optional, auto-detected from node2)

    Returns:
        Dictionary with fork analysis
    """
    # Get tips if not provided
    if not tip1:
        tip1 = rpc_call(node1, 'getbestblockhash')

    if not tip2:
        if not node2:
            raise ValueError("Must provide either node2 or tip2")
        tip2 = rpc_call(node2, 'getbestblockhash')

    if not tip1 or not tip2:
        return {
            'error': 'Could not get chain tips',
            'tip1': tip1,
            'tip2': tip2
        }

    # Check if they're the same (no fork)
    if tip1 == tip2:
        header = get_block_header(node1, tip1)
        return {
            'fork': False,
            'tip': tip1,
            'height': header['height'] if header else None,
            'message': 'No fork detected - both nodes on same tip'
        }

    # Get tip heights
    header1 = get_block_header(node1, tip1)
    header2 = get_block_header(node1, tip2)  # Use node1 to query both

    if not header1:
        # Try node2 for header1
        if node2:
            header1 = get_block_header(node2, tip1)

    if not header2 and node2:
        header2 = get_block_header(node2, tip2)

    if not header1 or not header2:
        return {
            'error': 'Could not get block headers',
            'tip1': tip1,
            'tip2': tip2
        }

    # Find common ancestor
    query_node = node1  # Use node1 to query blockchain state
    common_hash, common_height = find_common_ancestor(query_node, tip1, tip2)

    if not common_hash:
        return {
            'error': 'Could not find common ancestor',
            'tip1': tip1,
            'tip2': tip2,
            'height1': header1['height'],
            'height2': header2['height']
        }

    # Calculate fork depth
    depth1 = header1['height'] - common_height
    depth2 = header2['height'] - common_height
    total_depth = depth1 + depth2

    return {
        'fork': True,
        'tip1': {
            'hash': tip1,
            'height': header1['height'],
            'blocks_since_fork': depth1
        },
        'tip2': {
            'hash': tip2,
            'height': header2['height'],
            'blocks_since_fork': depth2
        },
        'common_ancestor': {
            'hash': common_hash,
            'height': common_height
        },
        'fork_depth': {
            'chain1_blocks': depth1,
            'chain2_blocks': depth2,
            'total_blocks': total_depth
        },
        'message': f'Fork depth: {total_depth} blocks ({depth1} + {depth2})'
    }


def print_fork_analysis(analysis: Dict):
    """Pretty print fork analysis"""
    if 'error' in analysis:
        print(f"\n❌ Error: {analysis['error']}")
        return

    if not analysis['fork']:
        print(f"\n✅ {analysis['message']}")
        print(f"   Tip: {analysis['tip'][:16]}...")
        print(f"   Height: {analysis['height']}")
        return

    print("\n🔥 FORK DETECTED")
    print("=" * 60)

    print(f"\nChain A:")
    print(f"  Tip:    {analysis['tip1']['hash'][:16]}...")
    print(f"  Height: {analysis['tip1']['height']}")
    print(f"  Blocks since fork: {analysis['tip1']['blocks_since_fork']}")

    print(f"\nChain B:")
    print(f"  Tip:    {analysis['tip2']['hash'][:16]}...")
    print(f"  Height: {analysis['tip2']['height']}")
    print(f"  Blocks since fork: {analysis['tip2']['blocks_since_fork']}")

    print(f"\nCommon Ancestor:")
    print(f"  Hash:   {analysis['common_ancestor']['hash'][:16]}...")
    print(f"  Height: {analysis['common_ancestor']['height']}")

    print(f"\nFork Depth Analysis:")
    print(f"  Chain A: {analysis['fork_depth']['chain1_blocks']} blocks")
    print(f"  Chain B: {analysis['fork_depth']['chain2_blocks']} blocks")
    print(f"  Total:   {analysis['fork_depth']['total_blocks']} blocks")
    print(f"\n{analysis['message']}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='Analyze Bitcoin fork depth')
    parser.add_argument('--node1', help='First node name')
    parser.add_argument('--node2', help='Second node name')
    parser.add_argument('--tip1', help='First chain tip hash')
    parser.add_argument('--tip2', help='Second chain tip hash')
    parser.add_argument('--json', action='store_true', help='Output JSON')

    args = parser.parse_args()

    if not args.node1 and not (args.tip1 and args.tip2):
        parser.error('Must provide --node1 or both --tip1 and --tip2')

    try:
        analysis = analyze_fork_depth(
            node1=args.node1,
            node2=args.node2,
            tip1=args.tip1,
            tip2=args.tip2
        )

        if args.json:
            print(json.dumps(analysis, indent=2))
        else:
            print_fork_analysis(analysis)

        # Exit code: 0 if no fork, 1 if fork detected, 2 if error
        if 'error' in analysis:
            sys.exit(2)
        elif analysis['fork']:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
