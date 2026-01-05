#!/usr/bin/env python3
"""
Create Custom Entity-Based Network Configurations

This script shows examples of how to create different network variations
by allocating specific exchanges, mining pools, and users to each fork.
"""

from entity_database import EntityDatabase
from configuration_generator import ConfigurationGenerator
from warnet_network_builder import WarnetNetworkBuilder


def create_variation_examples():
    """
    Examples of different network configurations you can create
    """

    # Load entity database
    db = EntityDatabase.load('entity_database.json')
    gen = ConfigurationGenerator(db)
    builder = WarnetNetworkBuilder()

    print("="*80)
    print("CUSTOM NETWORK VARIATIONS")
    print("="*80)

    # ===================================================================
    # VARIATION 1: All Exchanges vs All Miners (Economic vs Hashrate)
    # ===================================================================
    print("\n### VARIATION 1: Economic Power vs Mining Power ###")
    print("Fork A (v27): All 3 exchanges, no miners")
    print("Fork B (v26): No exchanges, all miners")

    config1 = gen.generate_specific_config(
        config_id='economic-vs-miners',
        exchange_allocation=[0, 1, 2],  # ALL 3 exchanges to Fork A
        miner_allocation=[],            # NO miners to Fork A (all go to Fork B)
        user_allocation_pct=50          # Split users 50/50
    )

    summary1 = config1.summary()
    print(f"Result: Economic {summary1['splits']['economic']['v27']:.1f}% vs {summary1['splits']['economic']['v26']:.1f}%")
    print(f"        Hashrate {summary1['splits']['hashrate']['v27']:.1f}% vs {summary1['splits']['hashrate']['v26']:.1f}%")

    network_dir1 = builder.build_network_from_entity_config(config1)
    print(f"✓ Network created at: {network_dir1}")

    # ===================================================================
    # VARIATION 2: Top Exchange + Top Miner vs The Rest
    # ===================================================================
    print("\n### VARIATION 2: Dominant Players vs The Rest ###")
    print("Fork A (v27): Top exchange (50%) + Top miner (27%)")
    print("Fork B (v26): Everything else")

    config2 = gen.generate_specific_config(
        config_id='dominant-vs-rest',
        exchange_allocation=[0],     # Only Major Exchange 1 (2M BTC)
        miner_allocation=[0],        # Only Foundry USA (26.89%)
        user_allocation_pct=30       # 30% of users to dominant side
    )

    summary2 = config2.summary()
    print(f"Result: Economic {summary2['splits']['economic']['v27']:.1f}% vs {summary2['splits']['economic']['v26']:.1f}%")
    print(f"        Hashrate {summary2['splits']['hashrate']['v27']:.1f}% vs {summary2['splits']['hashrate']['v26']:.1f}%")

    network_dir2 = builder.build_network_from_entity_config(config2)
    print(f"✓ Network created at: {network_dir2}")

    # ===================================================================
    # VARIATION 3: Regional Split (USA vs China)
    # ===================================================================
    print("\n### VARIATION 3: Geographic Split (USA vs China) ###")
    print("Fork A (v27): US-based entities")
    print("Fork B (v26): China-based entities")

    config3 = gen.generate_specific_config(
        config_id='usa-vs-china',
        exchange_allocation=[0],     # Assume Exchange 0 is US-based
        miner_allocation=[0],        # Foundry USA (26.89%) - USA
        user_allocation_pct=40       # 40% users to USA side
    )
    # Note: Miners 1,2,3 (AntPool, F2Pool, ViaBTC) are China-based = 48.11%

    summary3 = config3.summary()
    print(f"Result: Economic {summary3['splits']['economic']['v27']:.1f}% vs {summary3['splits']['economic']['v26']:.1f}%")
    print(f"        Hashrate {summary3['splits']['hashrate']['v27']:.1f}% vs {summary3['splits']['hashrate']['v26']:.1f}%")

    network_dir3 = builder.build_network_from_entity_config(config3)
    print(f"✓ Network created at: {network_dir3}")

    # ===================================================================
    # VARIATION 4: Balanced 50/50 Everything
    # ===================================================================
    print("\n### VARIATION 4: Perfectly Balanced (Thanos Style) ###")
    print("Fork A (v27): Half of everything")
    print("Fork B (v26): Half of everything")

    config4 = gen.generate_specific_config(
        config_id='perfect-balance',
        exchange_allocation=[0],         # Top exchange ~50% economic
        miner_allocation=[0, 1],         # Foundry + AntPool = 50% hashrate
        user_allocation_pct=50           # 50% users
    )

    summary4 = config4.summary()
    print(f"Result: Economic {summary4['splits']['economic']['v27']:.1f}% vs {summary4['splits']['economic']['v26']:.1f}%")
    print(f"        Hashrate {summary4['splits']['hashrate']['v27']:.1f}% vs {summary4['splits']['hashrate']['v26']:.1f}%")

    network_dir4 = builder.build_network_from_entity_config(config4)
    print(f"✓ Network created at: {network_dir4}")

    # ===================================================================
    # VARIATION 5: The People vs The Institutions
    # ===================================================================
    print("\n### VARIATION 5: David vs Goliath (Users vs Institutions) ###")
    print("Fork A (v27): All 1000 users + small miners")
    print("Fork B (v26): All exchanges + top miners")

    config5 = gen.generate_specific_config(
        config_id='david-vs-goliath',
        exchange_allocation=[],          # NO exchanges to Fork A
        miner_allocation=[2, 3, 4, 5],  # Only smaller pools to Fork A
        user_allocation_pct=100          # ALL users to Fork A
    )

    summary5 = config5.summary()
    print(f"Result: Economic {summary5['splits']['economic']['v27']:.1f}% vs {summary5['splits']['economic']['v26']:.1f}%")
    print(f"        Hashrate {summary5['splits']['hashrate']['v27']:.1f}% vs {summary5['splits']['hashrate']['v26']:.1f}%")

    network_dir5 = builder.build_network_from_entity_config(config5)
    print(f"✓ Network created at: {network_dir5}")

    # ===================================================================
    # VARIATION 6: Asymmetric Extreme (90/10 split)
    # ===================================================================
    print("\n### VARIATION 6: Extreme Asymmetry (90/10) ###")
    print("Fork A (v27): Almost everything")
    print("Fork B (v26): Tiny minority")

    config6 = gen.generate_specific_config(
        config_id='extreme-asymmetry-90-10',
        exchange_allocation=[0, 1, 2],  # All exchanges
        miner_allocation=[0, 1, 2, 3],  # Top 4 pools = ~75% hashrate
        user_allocation_pct=90          # 90% of users
    )

    summary6 = config6.summary()
    print(f"Result: Economic {summary6['splits']['economic']['v27']:.1f}% vs {summary6['splits']['economic']['v26']:.1f}%")
    print(f"        Hashrate {summary6['splits']['hashrate']['v27']:.1f}% vs {summary6['splits']['hashrate']['v26']:.1f}%")

    network_dir6 = builder.build_network_from_entity_config(config6)
    print(f"✓ Network created at: {network_dir6}")

    print("\n" + "="*80)
    print("✓ All 6 variations created!")
    print("="*80)
    print("\nTo deploy a specific variation:")
    print("  warnet deploy /home/pfoytik/bitcoinTools/warnet/test-networks/<config-id>")
    print("\nExample:")
    print("  warnet deploy /home/pfoytik/bitcoinTools/warnet/test-networks/economic-vs-miners")


def custom_allocation_template():
    """
    Template for creating your own custom allocation
    """
    print("\n" + "="*80)
    print("CUSTOM ALLOCATION TEMPLATE")
    print("="*80)
    print("""
To create your own custom network:

1. Choose which exchanges go to Fork A (v27):
   exchange_allocation=[0, 1, 2]  # List of indices (0-2)

   Available exchanges:
   [0] Major Exchange 1: 2,000,000 BTC, 200,000 BTC/day
   [1] Major Exchange 2: 1,200,000 BTC, 120,000 BTC/day
   [2] Major Exchange 3: 800,000 BTC, 80,000 BTC/day

2. Choose which miners go to Fork A (v27):
   miner_allocation=[0, 1, 2, 3, 4, 5]  # List of indices (0-5)

   Available miners:
   [0] Foundry USA: 26.89% hashrate (USA)
   [1] AntPool: 23.11% hashrate (China)
   [2] F2Pool: 14.22% hashrate (China)
   [3] ViaBTC: 10.78% hashrate (China)
   [4] Binance Pool: 10.00% hashrate (Multiple)
   [5] Other Pools: 15.00% hashrate (Multiple)

3. Choose user allocation percentage (0-100):
   user_allocation_pct=50  # % of users to Fork A

   Users are allocated by size (largest first):
   - 0% = all users to Fork B
   - 50% = top 500 users to Fork A, bottom 500 to Fork B
   - 100% = all users to Fork A

Example:

    from entity_database import EntityDatabase
    from configuration_generator import ConfigurationGenerator
    from warnet_network_builder import WarnetNetworkBuilder

    db = EntityDatabase.load('entity_database.json')
    gen = ConfigurationGenerator(db)
    builder = WarnetNetworkBuilder()

    config = gen.generate_specific_config(
        config_id='my-custom-network',
        exchange_allocation=[0, 1],    # Top 2 exchanges to Fork A
        miner_allocation=[0, 2, 4],    # Foundry, F2Pool, Binance to Fork A
        user_allocation_pct=60         # 60% users to Fork A
    )

    network_dir = builder.build_network_from_entity_config(config)
    print(f"Created: {network_dir}")

Then deploy:
    warnet deploy {network_dir}
""")


if __name__ == "__main__":
    # Create all example variations
    create_variation_examples()

    # Print template for custom allocations
    custom_allocation_template()
