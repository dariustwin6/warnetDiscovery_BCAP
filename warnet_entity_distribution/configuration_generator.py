#!/usr/bin/env python3
"""
Network Configuration Generator
Creates multi-dimensional fork scenarios by allocating entities to partitions
"""

import json
import random
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from entity_database import EntityDatabase, Exchange, MiningPool, User

@dataclass
class ForkPartition:
    """One side of a fork"""
    name: str  # 'v27' or 'v26'
    exchanges: List[Exchange]
    mining_pools: List[MiningPool]
    users: List[User]
    
    def get_total_custody(self) -> float:
        exchange_custody = sum(e.custody_btc for e in self.exchanges)
        user_custody = sum(u.custody_btc for u in self.users)
        return exchange_custody + user_custody
    
    def get_total_volume(self) -> float:
        exchange_volume = sum(e.daily_volume_btc for e in self.exchanges)
        user_volume = sum(u.daily_volume_btc for u in self.users)
        return exchange_volume + user_volume
    
    def get_total_hashrate(self) -> float:
        return sum(p.hashrate_pct for p in self.mining_pools)
    
    def get_consensus_weight(self) -> float:
        """BCAP consensus weight"""
        return (self.get_total_custody() + self.get_total_volume()) / 2
    
    def get_node_count(self) -> int:
        return len(self.exchanges) + len(self.mining_pools) + len(self.users)
    
    def summary(self) -> dict:
        return {
            'name': self.name,
            'exchanges': len(self.exchanges),
            'mining_pools': len(self.mining_pools),
            'users': len(self.users),
            'total_nodes': self.get_node_count(),
            'custody_btc': self.get_total_custody(),
            'volume_btc_per_day': self.get_total_volume(),
            'hashrate_pct': self.get_total_hashrate(),
            'consensus_weight': self.get_consensus_weight()
        }

@dataclass
class NetworkConfiguration:
    """
    Complete network configuration - represents one point in parameter space
    """
    config_id: str
    fork_a: ForkPartition  # v27 partition
    fork_b: ForkPartition  # v26 partition
    
    def get_economic_split(self) -> Tuple[float, float]:
        """Returns (fork_a_pct, fork_b_pct) by consensus weight"""
        total_weight = self.fork_a.get_consensus_weight() + self.fork_b.get_consensus_weight()
        if total_weight == 0:
            return (50.0, 50.0)
        
        fork_a_pct = (self.fork_a.get_consensus_weight() / total_weight) * 100
        fork_b_pct = (self.fork_b.get_consensus_weight() / total_weight) * 100
        
        return (fork_a_pct, fork_b_pct)
    
    def get_hashrate_split(self) -> Tuple[float, float]:
        """Returns (fork_a_pct, fork_b_pct) by hashrate"""
        return (self.fork_a.get_total_hashrate(), self.fork_b.get_total_hashrate())
    
    def get_custody_split(self) -> Tuple[float, float]:
        """Returns (fork_a_pct, fork_b_pct) by custody"""
        total_custody = self.fork_a.get_total_custody() + self.fork_b.get_total_custody()
        if total_custody == 0:
            return (50.0, 50.0)
        
        fork_a_pct = (self.fork_a.get_total_custody() / total_custody) * 100
        fork_b_pct = (self.fork_b.get_total_custody() / total_custody) * 100
        
        return (fork_a_pct, fork_b_pct)
    
    def get_volume_split(self) -> Tuple[float, float]:
        """Returns (fork_a_pct, fork_b_pct) by volume"""
        total_volume = self.fork_a.get_total_volume() + self.fork_b.get_total_volume()
        if total_volume == 0:
            return (50.0, 50.0)
        
        fork_a_pct = (self.fork_a.get_total_volume() / total_volume) * 100
        fork_b_pct = (self.fork_b.get_total_volume() / total_volume) * 100
        
        return (fork_a_pct, fork_b_pct)
    
    def summary(self) -> dict:
        econ_a, econ_b = self.get_economic_split()
        hash_a, hash_b = self.get_hashrate_split()
        cust_a, cust_b = self.get_custody_split()
        vol_a, vol_b = self.get_volume_split()
        
        return {
            'config_id': self.config_id,
            'fork_a': self.fork_a.summary(),
            'fork_b': self.fork_b.summary(),
            'splits': {
                'economic': {'v27': econ_a, 'v26': econ_b},
                'hashrate': {'v27': hash_a, 'v26': hash_b},
                'custody': {'v27': cust_a, 'v26': cust_b},
                'volume': {'v27': vol_a, 'v26': vol_b}
            }
        }
    
    def to_short_string(self) -> str:
        """Compact representation for display"""
        econ_a, econ_b = self.get_economic_split()
        hash_a, hash_b = self.get_hashrate_split()
        
        return f"E{econ_a:.0f}/H{hash_a:.0f} (ex:{len(self.fork_a.exchanges)}/{len(self.fork_b.exchanges)}, " \
               f"pools:{len(self.fork_a.mining_pools)}/{len(self.fork_b.mining_pools)}, " \
               f"users:{len(self.fork_a.users)}/{len(self.fork_b.users)})"

class ConfigurationGenerator:
    """
    Generates diverse network configurations for exploration
    """
    
    def __init__(self, entity_db: EntityDatabase):
        self.entity_db = entity_db
    
    def generate_specific_config(
        self,
        config_id: str,
        exchange_allocation: List[int],  # [indices for fork_a]
        miner_allocation: List[int],     # [indices for fork_a]
        user_allocation_pct: float       # % of users to fork_a
    ) -> NetworkConfiguration:
        """
        Generate specific configuration by entity allocation
        
        Example:
            exchange_allocation=[0, 1]  → Exchanges 0, 1 go to fork_a, Exchange 2 to fork_b
            miner_allocation=[0, 2]      → Pools 0, 2 go to fork_a, rest to fork_b
            user_allocation_pct=70       → 70% of users to fork_a, 30% to fork_b
        """
        
        # Allocate exchanges
        fork_a_exchanges = [self.entity_db.exchanges[i] for i in exchange_allocation]
        fork_b_exchanges = [e for i, e in enumerate(self.entity_db.exchanges) 
                           if i not in exchange_allocation]
        
        # Allocate miners
        fork_a_miners = [self.entity_db.mining_pools[i] for i in miner_allocation]
        fork_b_miners = [m for i, m in enumerate(self.entity_db.mining_pools) 
                        if i not in miner_allocation]
        
        # Allocate users (top X% to fork_a)
        n_users_to_a = int(len(self.entity_db.users) * user_allocation_pct / 100)
        fork_a_users = self.entity_db.users[:n_users_to_a]
        fork_b_users = self.entity_db.users[n_users_to_a:]
        
        # Create partitions
        fork_a = ForkPartition(
            name='v27',
            exchanges=fork_a_exchanges,
            mining_pools=fork_a_miners,
            users=fork_a_users
        )
        
        fork_b = ForkPartition(
            name='v26',
            exchanges=fork_b_exchanges,
            mining_pools=fork_b_miners,
            users=fork_b_users
        )
        
        return NetworkConfiguration(
            config_id=config_id,
            fork_a=fork_a,
            fork_b=fork_b
        )
    
    def generate_random_config(self, config_id: str) -> NetworkConfiguration:
        """Generate random configuration"""
        
        # Random exchange allocation
        n_exchanges = len(self.entity_db.exchanges)
        n_to_a = random.randint(0, n_exchanges)
        exchange_indices = list(range(n_exchanges))
        random.shuffle(exchange_indices)
        exchange_allocation = exchange_indices[:n_to_a]
        
        # Random miner allocation
        n_pools = len(self.entity_db.mining_pools)
        n_to_a = random.randint(0, n_pools)
        miner_indices = list(range(n_pools))
        random.shuffle(miner_indices)
        miner_allocation = miner_indices[:n_to_a]
        
        # Random user allocation
        user_allocation_pct = random.uniform(0, 100)
        
        return self.generate_specific_config(
            config_id=config_id,
            exchange_allocation=exchange_allocation,
            miner_allocation=miner_allocation,
            user_allocation_pct=user_allocation_pct
        )
    
    def generate_coarse_grid(self, n_samples: int = 50) -> List[NetworkConfiguration]:
        """
        Generate diverse configurations for coarse exploration
        Uses Latin Hypercube-style sampling to ensure coverage
        """
        configs = []
        
        # Key scenarios to always include
        critical_scenarios = self._get_critical_scenarios()
        configs.extend(critical_scenarios)
        
        # Fill remaining with random samples
        n_random = n_samples - len(critical_scenarios)
        for i in range(n_random):
            config = self.generate_random_config(f'random-{i:03d}')
            configs.append(config)
        
        return configs
    
    def _get_critical_scenarios(self) -> List[NetworkConfiguration]:
        """
        Pre-defined critical scenarios we always want to test
        """
        scenarios = []
        
        # Scenario 1: All entities together (baseline)
        scenarios.append(self.generate_specific_config(
            config_id='baseline-all-v27',
            exchange_allocation=[0, 1, 2],  # All 3 exchanges
            miner_allocation=[0, 1, 2, 3, 4, 5],  # All pools
            user_allocation_pct=100  # All users
        ))
        
        # Scenario 2: Perfect 50/50 exchange-miner split (YOUR KEY HYPOTHESIS!)
        scenarios.append(self.generate_specific_config(
            config_id='perfect-split-50-50',
            exchange_allocation=[0],  # Top exchange only (50% custody)
            miner_allocation=[0, 1],  # Foundry + AntPool (~50% hashrate)
            user_allocation_pct=0  # All users to fork_b
        ))
        
        # Scenario 3: David vs Goliath - All users vs top exchange
        scenarios.append(self.generate_specific_config(
            config_id='david-vs-goliath',
            exchange_allocation=[],  # No exchanges to fork_a
            miner_allocation=[2, 3, 4],  # Some pools
            user_allocation_pct=100  # All users to fork_a
        ))
        
        # Scenario 4: 2 exchanges vs 1 exchange
        scenarios.append(self.generate_specific_config(
            config_id='exchange-2-vs-1',
            exchange_allocation=[0, 1],  # Top 2
            miner_allocation=[0, 1, 2],  # ~60% hashrate
            user_allocation_pct=50  # Split users
        ))
        
        # Scenario 5: Economic vs miners
        scenarios.append(self.generate_specific_config(
            config_id='economic-vs-miners',
            exchange_allocation=[0, 1, 2],  # All exchanges (90% custody)
            miner_allocation=[],  # NO miners to fork_a
            user_allocation_pct=100  # All users to fork_a
        ))
        
        return scenarios

# === EXAMPLE USAGE ===

if __name__ == "__main__":
    print("="*80)
    print("NETWORK CONFIGURATION GENERATOR")
    print("="*80)
    
    # Load entity database
    db = EntityDatabase.load('entity_database.json')
    print("\n✓ Loaded entity database")
    
    # Create generator
    generator = ConfigurationGenerator(db)
    
    # Example 1: Generate specific configuration
    print("\n" + "="*80)
    print("EXAMPLE 1: Perfect 50/50 Split (Your Hypothesis!)")
    print("="*80)
    
    config = generator.generate_specific_config(
        config_id='test-perfect-split',
        exchange_allocation=[0],  # Top exchange to fork_a
        miner_allocation=[0, 1],  # Foundry + AntPool to fork_a
        user_allocation_pct=0     # All users to fork_b
    )
    
    summary = config.summary()
    
    print(f"\nConfig ID: {config.config_id}")
    print(f"Short: {config.to_short_string()}")
    
    print(f"\n### Fork A (v27) ###")
    print(f"  Exchanges: {summary['fork_a']['exchanges']}")
    print(f"  Pools: {summary['fork_a']['mining_pools']}")
    print(f"  Users: {summary['fork_a']['users']}")
    print(f"  Custody: {summary['fork_a']['custody_btc']:,.0f} BTC")
    print(f"  Volume: {summary['fork_a']['volume_btc_per_day']:,.0f} BTC/day")
    print(f"  Hashrate: {summary['fork_a']['hashrate_pct']:.2f}%")
    print(f"  Weight: {summary['fork_a']['consensus_weight']:,.0f}")
    
    print(f"\n### Fork B (v26) ###")
    print(f"  Exchanges: {summary['fork_b']['exchanges']}")
    print(f"  Pools: {summary['fork_b']['mining_pools']}")
    print(f"  Users: {summary['fork_b']['users']}")
    print(f"  Custody: {summary['fork_b']['custody_btc']:,.0f} BTC")
    print(f"  Volume: {summary['fork_b']['volume_btc_per_day']:,.0f} BTC/day")
    print(f"  Hashrate: {summary['fork_b']['hashrate_pct']:.2f}%")
    print(f"  Weight: {summary['fork_b']['consensus_weight']:,.0f}")
    
    print(f"\n### Splits ###")
    econ = summary['splits']['economic']
    hash = summary['splits']['hashrate']
    cust = summary['splits']['custody']
    vol = summary['splits']['volume']
    
    print(f"  Economic: {econ['v27']:.1f}% vs {econ['v26']:.1f}%")
    print(f"  Hashrate: {hash['v27']:.1f}% vs {hash['v26']:.1f}%")
    print(f"  Custody:  {cust['v27']:.1f}% vs {cust['v26']:.1f}%")
    print(f"  Volume:   {vol['v27']:.1f}% vs {vol['v26']:.1f}%")
    
    # Example 2: Generate coarse grid
    print("\n" + "="*80)
    print("EXAMPLE 2: Coarse Grid (50 diverse scenarios)")
    print("="*80)
    
    configs = generator.generate_coarse_grid(n_samples=10)  # Just 10 for demo
    
    print(f"\n✓ Generated {len(configs)} configurations\n")
    
    for i, cfg in enumerate(configs[:5], 1):
        print(f"{i}. {cfg.config_id}: {cfg.to_short_string()}")
    
    print(f"... ({len(configs)-5} more)")
    
    # Save example config
    with open('example_config.json', 'w') as f:
        json.dump(config.summary(), f, indent=2)
    
    print("\n✓ Saved example config to example_config.json")
    
    print("\n" + "="*80)
    print("✓ Configuration generator ready!")
    print("="*80)
