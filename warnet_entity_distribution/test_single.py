#!/usr/bin/env python3
import sys
from pathlib import Path
from entity_test_runner import EntityTestRunner
from configuration_generator import NetworkConfiguration, ForkPartition, ConfigurationGenerator
from entity_database import EntityDatabase

# Load database
db = EntityDatabase.load('entity_database.json')
generator = ConfigurationGenerator(db)

# Generate perfect-split config
config = generator.generate_specific_config(
    config_id='test-perfect-split',
    exchange_allocation=[0],
    miner_allocation=[0, 1],
    user_allocation_pct=0
)

print(f"Config: {config.config_id}")
print(f"  Economic split: {config.get_economic_split()}")
print(f"  Hashrate split: {config.get_hashrate_split()}")

# Build network
from warnet_network_builder import WarnetNetworkBuilder
builder = WarnetNetworkBuilder()
network_dir = builder.build_network_from_entity_config(config, users_per_node=100)
print(f"Network built at: {network_dir}")

# Run test with 60-second duration to test quickly
runner = EntityTestRunner()
print("\nRunning 60-second test...")
result = runner.run_entity_test(
    network_dir=network_dir,
    config=config,
    duration=60,  # 1 minute test
    partition_mode="dynamic"
)

print(f"\nResult: {result['status']}")
print(f"Blocks mined: {result['steps']['mining']['blocks']}")
print(f"Final heights: {result['final_heights']}")
print(f"Fork depth: {result['fork_depth']}")
