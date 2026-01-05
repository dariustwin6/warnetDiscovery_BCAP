#!/usr/bin/env python3
"""
Test User Aggregation Feature

Demonstrates how to use the users_per_node parameter to control
network size for realistic block propagation testing.
"""

from entity_database import EntityDatabase
from configuration_generator import ConfigurationGenerator
from warnet_network_builder import WarnetNetworkBuilder


def test_aggregation_scenarios():
    """
    Test different user aggregation levels
    """

    # Load database
    db = EntityDatabase.load('entity_database.json')
    gen = ConfigurationGenerator(db)
    builder = WarnetNetworkBuilder()

    print("="*80)
    print("USER AGGREGATION TEST - Different Network Sizes")
    print("="*80)

    # Create a test configuration (50/50 split)
    base_config = gen.generate_specific_config(
        config_id='aggregation-test-base',
        exchange_allocation=[0],      # Top exchange to fork_a
        miner_allocation=[0, 1],      # Foundry + AntPool to fork_a
        user_allocation_pct=50        # 50% users to each fork (500 users each)
    )

    print(f"\nBase Configuration: {base_config.config_id}")
    print(f"Fork A users: {len(base_config.fork_a.users)}")
    print(f"Fork B users: {len(base_config.fork_b.users)}")

    # === TEST 1: Default (all users aggregated into 1 node per fork) ===
    print("\n" + "="*80)
    print("TEST 1: Maximum Aggregation (users_per_node=None)")
    print("="*80)

    config1 = gen.generate_specific_config(
        config_id='test-max-aggregation',
        exchange_allocation=[0],
        miner_allocation=[0, 1],
        user_allocation_pct=50
    )

    network_dir1 = builder.build_network_from_entity_config(
        config1,
        users_per_node=None  # Default: all users → 1 node per fork
    )

    print(f"Expected nodes: 1 exchange + 2 pools + 1 user aggregate = 4 nodes (fork_a)")
    print(f"              2 exchanges + 4 pools + 1 user aggregate = 7 nodes (fork_b)")
    print(f"              Total: ~11 nodes")

    # === TEST 2: 100 users per node (moderate aggregation) ===
    print("\n" + "="*80)
    print("TEST 2: Moderate Aggregation (users_per_node=100)")
    print("="*80)

    config2 = gen.generate_specific_config(
        config_id='test-moderate-aggregation',
        exchange_allocation=[0],
        miner_allocation=[0, 1],
        user_allocation_pct=50
    )

    network_dir2 = builder.build_network_from_entity_config(
        config2,
        users_per_node=100  # 500 users → 5 nodes per fork
    )

    print(f"Expected nodes: 1 exchange + 2 pools + 5 user nodes = 8 nodes (fork_a)")
    print(f"              2 exchanges + 4 pools + 5 user nodes = 11 nodes (fork_b)")
    print(f"              Total: ~19 nodes")

    # === TEST 3: 10 users per node (high granularity) ===
    print("\n" + "="*80)
    print("TEST 3: High Granularity (users_per_node=10)")
    print("="*80)

    config3 = gen.generate_specific_config(
        config_id='test-high-granularity',
        exchange_allocation=[0],
        miner_allocation=[0, 1],
        user_allocation_pct=50
    )

    network_dir3 = builder.build_network_from_entity_config(
        config3,
        users_per_node=10  # 500 users → 50 nodes per fork
    )

    print(f"Expected nodes: 1 exchange + 2 pools + 50 user nodes = 53 nodes (fork_a)")
    print(f"              2 exchanges + 4 pools + 50 user nodes = 56 nodes (fork_b)")
    print(f"              Total: ~109 nodes")

    # === TEST 4: 1 user per node (maximum realism) ===
    print("\n" + "="*80)
    print("TEST 4: Maximum Realism (users_per_node=1)")
    print("="*80)
    print("WARNING: This creates 1000+ nodes - only use for small-scale testing!")

    config4 = gen.generate_specific_config(
        config_id='test-max-realism',
        exchange_allocation=[0],
        miner_allocation=[0, 1],
        user_allocation_pct=50
    )

    network_dir4 = builder.build_network_from_entity_config(
        config4,
        users_per_node=1  # Each user → 1 node
    )

    print(f"Expected nodes: 1 exchange + 2 pools + 500 user nodes = 503 nodes (fork_a)")
    print(f"              2 exchanges + 4 pools + 500 user nodes = 506 nodes (fork_b)")
    print(f"              Total: ~1009 nodes (!!!)")

    # === SUMMARY ===
    print("\n" + "="*80)
    print("SUMMARY - Use Cases for Each Aggregation Level")
    print("="*80)

    print("""
users_per_node=None (Default)
  - Minimal network size (~10-20 nodes)
  - Fast deployment, low resource usage
  - Good for: Quick testing, resource-constrained environments
  - Trade-off: Simplified network topology

users_per_node=100
  - Moderate network size (~20-50 nodes)
  - Balanced resource usage
  - Good for: Medium-scale fork testing, CI/CD pipelines
  - Trade-off: Still simplified topology, but more realistic than default

users_per_node=10
  - Large network size (~100-200 nodes)
  - Higher resource usage
  - Good for: Realistic block propagation testing, gossip network analysis
  - Trade-off: Requires more resources, slower deployment

users_per_node=1
  - Maximum network size (1000+ nodes)
  - Very high resource usage
  - Good for: Maximum realism, research-grade simulations
  - Trade-off: Requires significant cluster resources

RECOMMENDATION for block propagation testing:
  - Start with users_per_node=100 for development
  - Use users_per_node=10 for production testing
  - Only use users_per_node=1 for critical research scenarios
    """)

    print("="*80)
    print("All test networks generated!")
    print("="*80)

    print("\nGenerated networks:")
    print(f"  {network_dir1}")
    print(f"  {network_dir2}")
    print(f"  {network_dir3}")
    print(f"  {network_dir4}")

    print("\nTo deploy a specific test:")
    print(f"  warnet deploy {network_dir2}  # Moderate aggregation (recommended)")


if __name__ == "__main__":
    test_aggregation_scenarios()
