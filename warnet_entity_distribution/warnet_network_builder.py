#!/usr/bin/env python3
"""
Warnet Network Builder - Converts entity configs to network.yaml
Bridges entity_framework with existing Warnet partition infrastructure
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path
from configuration_generator import NetworkConfiguration, ForkPartition
from entity_database import Exchange, MiningPool, User
import yaml


class WarnetNetworkBuilder:
    """
    Builds Warnet-compatible network.yaml from entity allocations
    """

    def __init__(self, base_networks_dir: str = None):
        if base_networks_dir is None:
            base_networks_dir = "/home/pfoytik/bitcoinTools/warnet/test-networks"
        self.base_networks_dir = Path(base_networks_dir).expanduser()

    def build_network_from_entity_config(
        self,
        config: NetworkConfiguration,
        output_dir: str = None,
        users_per_node: int = None
    ) -> Path:
        """
        Generate network.yaml from entity configuration

        Args:
            config: NetworkConfiguration with entity allocations
            output_dir: Where to save network directory
            users_per_node: How many users to aggregate per node
                           - None (default): All users in each fork → 1 aggregated node
                           - 1: Each user → 1 individual node (1000 user nodes!)
                           - 10: Every 10 users → 1 node (100 user nodes)
                           - 100: Every 100 users → 1 node (10 user nodes)

        Returns:
            Path to generated network directory
        """

        # Create output directory
        if output_dir is None:
            output_dir = self.base_networks_dir / config.config_id
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        # Build network structure
        network_data = self._build_network_yaml(config, users_per_node)

        # Save network.yaml
        network_file = output_dir / 'network.yaml'
        with open(network_file, 'w') as f:
            yaml.dump(network_data, f, default_flow_style=False, sort_keys=False)

        # Generate node-defaults.yaml
        defaults_data = self._build_node_defaults()
        defaults_file = output_dir / 'node-defaults.yaml'
        with open(defaults_file, 'w') as f:
            yaml.dump(defaults_data, f, default_flow_style=False)

        print(f"✓ Generated network: {output_dir}")

        return output_dir

    def _aggregate_users(self, users: list, users_per_node: int = None) -> list:
        """
        Aggregate users into groups for network simulation

        Args:
            users: List of User objects
            users_per_node: How many users per aggregated node
                           - None: All users → 1 node
                           - 1: Each user → 1 node
                           - N: Every N users → 1 node

        Returns:
            List of aggregated user groups (each group becomes 1 node)
        """
        if not users or len(users) == 0:
            return []

        # Default: aggregate all into one node
        if users_per_node is None:
            return [users]

        # Each user gets their own node
        if users_per_node == 1:
            return [[u] for u in users]

        # Group users into chunks
        aggregated = []
        for i in range(0, len(users), users_per_node):
            group = users[i:i + users_per_node]
            aggregated.append(group)

        return aggregated

    def _build_network_yaml(self, config: NetworkConfiguration, users_per_node: int = None) -> dict:
        """
        Build network.yaml structure from entity config

        Format matches existing test-networks/ scenarios

        Args:
            config: NetworkConfiguration with entity allocations
            users_per_node: How many users to aggregate per node (None = all users in fork)
        """

        nodes = []
        node_counter = 0

        # Build addnode lists for dynamic partitioning
        # In dynamic mode, we create bridge connections between partitions
        # that will be severed later via setban RPC

        # === FORK A (v27) NODES ===

        fork_a_start = node_counter

        # Exchanges on Fork A
        for exchange in config.fork_a.exchanges:
            nodes.append({
                'name': f'node-{node_counter:04d}',
                'image': {'tag': '27.0'},
                'addnode': [],  # Will fill in later
                'bitcoin_config': {
                    'maxconnections': 125,
                    'maxmempool': 300,
                    'txindex': 1
                },
                'metadata': {
                    'role': 'exchange' if 'Exchange 1' not in exchange.name else 'major_exchange',
                    'custody_btc': int(exchange.custody_btc),
                    'daily_volume_btc': int(exchange.daily_volume_btc),
                    'entity_id': exchange.id,
                    'entity_name': exchange.name,
                    'consensus_weight': round(exchange.consensus_weight(), 2)
                }
            })
            node_counter += 1

        # Mining pools on Fork A
        for pool in config.fork_a.mining_pools:
            nodes.append({
                'name': f'node-{node_counter:04d}',
                'image': {'tag': '27.0'},
                'addnode': [],
                'bitcoin_config': {
                    'maxconnections': 125,
                    'maxmempool': 300,
                    'txindex': 1
                },
                'metadata': {
                    'role': 'mining_pool',
                    'hashrate_pct': pool.hashrate_pct,
                    'entity_id': pool.id,
                    'entity_name': pool.name,
                    'location': pool.location
                }
            })
            node_counter += 1

        # Users on Fork A (with configurable aggregation)
        user_groups_a = self._aggregate_users(config.fork_a.users, users_per_node)
        for group_idx, user_group in enumerate(user_groups_a):
            total_custody = sum(u.custody_btc for u in user_group)
            total_volume = sum(u.daily_volume_btc for u in user_group)

            if total_custody > 0 or total_volume > 0:
                # Determine role based on aggregation
                if len(user_group) == 1:
                    role = f'user_{user_group[0].user_type}'
                    entity_id = user_group[0].id
                else:
                    role = 'user_aggregated'
                    entity_id = f'user_group_a_{group_idx}'

                nodes.append({
                    'name': f'node-{node_counter:04d}',
                    'image': {'tag': '27.0'},
                    'addnode': [],
                    'bitcoin_config': {
                        'maxconnections': 125,
                        'maxmempool': 300,
                        'txindex': 1
                    },
                    'metadata': {
                        'role': role,
                        'entity_id': entity_id,
                        'custody_btc': int(total_custody),
                        'daily_volume_btc': int(total_volume),
                        'represents': len(user_group),
                        'consensus_weight': round((total_custody + total_volume) / 2, 2)
                    }
                })
                node_counter += 1

        fork_a_end = node_counter

        # === FORK B (v26/v22) NODES ===

        fork_b_start = node_counter

        # Exchanges on Fork B
        for exchange in config.fork_b.exchanges:
            nodes.append({
                'name': f'node-{node_counter:04d}',
                'image': {'tag': '26.0'},  # Use v26 for older partition
                'addnode': [],
                'bitcoin_config': {
                    'maxconnections': 125,
                    'maxmempool': 300,
                    'txindex': 1
                },
                'metadata': {
                    'role': 'exchange' if 'Exchange 1' not in exchange.name else 'major_exchange',
                    'custody_btc': int(exchange.custody_btc),
                    'daily_volume_btc': int(exchange.daily_volume_btc),
                    'entity_id': exchange.id,
                    'entity_name': exchange.name,
                    'consensus_weight': round(exchange.consensus_weight(), 2)
                }
            })
            node_counter += 1

        # Mining pools on Fork B
        for pool in config.fork_b.mining_pools:
            nodes.append({
                'name': f'node-{node_counter:04d}',
                'image': {'tag': '26.0'},
                'addnode': [],
                'bitcoin_config': {
                    'maxconnections': 125,
                    'maxmempool': 300,
                    'txindex': 1
                },
                'metadata': {
                    'role': 'mining_pool',
                    'hashrate_pct': pool.hashrate_pct,
                    'entity_id': pool.id,
                    'entity_name': pool.name,
                    'location': pool.location
                }
            })
            node_counter += 1

        # Users on Fork B (with configurable aggregation)
        user_groups_b = self._aggregate_users(config.fork_b.users, users_per_node)
        for group_idx, user_group in enumerate(user_groups_b):
            total_custody = sum(u.custody_btc for u in user_group)
            total_volume = sum(u.daily_volume_btc for u in user_group)

            if total_custody > 0 or total_volume > 0:
                # Determine role based on aggregation
                if len(user_group) == 1:
                    role = f'user_{user_group[0].user_type}'
                    entity_id = user_group[0].id
                else:
                    role = 'user_aggregated'
                    entity_id = f'user_group_b_{group_idx}'

                nodes.append({
                    'name': f'node-{node_counter:04d}',
                    'image': {'tag': '26.0'},
                    'addnode': [],
                    'bitcoin_config': {
                        'maxconnections': 125,
                        'maxmempool': 300,
                        'txindex': 1
                    },
                    'metadata': {
                        'role': role,
                        'entity_id': entity_id,
                        'custody_btc': int(total_custody),
                        'daily_volume_btc': int(total_volume),
                        'represents': len(user_group),
                        'consensus_weight': round((total_custody + total_volume) / 2, 2)
                    }
                })
                node_counter += 1

        fork_b_end = node_counter

        # Build addnode connections (dynamic partitioning with bridge connections)
        # Each node connects to some nodes in its partition AND some in other partition
        for i in range(len(nodes)):
            node = nodes[i]
            node_name = node['name']

            if i < fork_a_end:  # Fork A node
                # Connect to other fork_a nodes
                fork_a_nodes = [nodes[j]['name'] for j in range(fork_a_start, fork_a_end) if j != i]
                # Add up to 4 connections within partition
                node['addnode'].extend(fork_a_nodes[:4])

                # Add 1 bridge connection to fork_b for dynamic partitioning
                if fork_b_end > fork_b_start:
                    bridge_node = nodes[fork_b_start]['name']
                    node['addnode'].append(bridge_node)

            else:  # Fork B node
                # Connect to other fork_b nodes
                fork_b_nodes = [nodes[j]['name'] for j in range(fork_b_start, fork_b_end) if j != i]
                node['addnode'].extend(fork_b_nodes[:4])

                # Add 1 bridge connection to fork_a
                if fork_a_end > fork_a_start:
                    bridge_node = nodes[fork_a_start]['name']
                    node['addnode'].append(bridge_node)

        return {
            'caddy': {'enabled': True},
            'fork_observer': {
                'enabled': True,
                'configQueryInterval': 10
            },
            'nodes': nodes
        }

    def _build_node_defaults(self) -> dict:
        """Standard node-defaults.yaml"""
        return {
            'bitcoin_config': {
                'regtest': 1,
                'dnsseed': 0,
                'txindex': 1,
                'fallbackfee': '0.00001'
            }
        }


# Example usage and testing
if __name__ == "__main__":
    from entity_database import EntityDatabase
    from configuration_generator import ConfigurationGenerator

    print("="*80)
    print("WARNET NETWORK BUILDER - TEST")
    print("="*80)

    # Load database
    db = EntityDatabase.load('entity_database.json')
    print(f"\n✓ Loaded entity database")
    print(f"  Exchanges: {len(db.exchanges)}")
    print(f"  Mining pools: {len(db.mining_pools)}")
    print(f"  Users: {len(db.users)}")

    # Generate a test config - Perfect 50/50 split
    gen = ConfigurationGenerator(db)
    config = gen.generate_specific_config(
        config_id='entity-test-perfect-split',
        exchange_allocation=[0],      # Exchange 0 (2M BTC) to fork_a
        miner_allocation=[0, 1],      # Foundry + AntPool (50% hashrate) to fork_a
        user_allocation_pct=0         # All users to fork_b
    )

    print(f"\n✓ Generated test configuration: {config.config_id}")
    summary = config.summary()
    print(f"\nFork A (v27):")
    print(f"  Economic: {summary['splits']['economic']['v27']:.1f}%")
    print(f"  Hashrate: {summary['splits']['hashrate']['v27']:.1f}%")
    print(f"  Nodes: {summary['fork_a']['total_nodes']}")
    print(f"\nFork B (v26):")
    print(f"  Economic: {summary['splits']['economic']['v26']:.1f}%")
    print(f"  Hashrate: {summary['splits']['hashrate']['v26']:.1f}%")
    print(f"  Nodes: {summary['fork_b']['total_nodes']}")

    # Build network
    builder = WarnetNetworkBuilder()

    # Default: all users aggregated (minimal nodes)
    network_dir = builder.build_network_from_entity_config(config)

    # For realistic block propagation testing, use users_per_node parameter:
    # network_dir = builder.build_network_from_entity_config(config, users_per_node=10)
    # users_per_node options:
    #   None (default) - All users in each fork → 1 node per fork
    #   100 - Moderate aggregation (~20 nodes total)
    #   10  - High granularity (~100 nodes total)
    #   1   - Maximum realism (1000+ nodes - requires significant resources!)

    print(f"\n✓ Network ready at: {network_dir}")
    print(f"\nYou can now deploy with:")
    print(f"  cd {network_dir.parent}")
    print(f"  warnet deploy {network_dir}")
    print(f"\nTo test user aggregation options, run:")
    print(f"  python3 test_user_aggregation.py")
