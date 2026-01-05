#!/usr/bin/env python3
"""
Entity Database - Realistic Bitcoin Network Entities
Represents actual exchanges, mining pools, and users with realistic values
"""

import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import random

@dataclass
class Exchange:
    """Major cryptocurrency exchange"""
    id: str
    name: str
    custody_btc: float        # Total BTC in custody
    daily_volume_btc: float   # Daily trading volume
    withdrawal_volume_btc: float  # Daily on-chain withdrawals
    deposit_volume_btc: float     # Daily on-chain deposits
    
    def consensus_weight(self) -> float:
        """Calculate BCAP consensus weight"""
        # From BCAP: weight = (custody + volume) / 2
        return (self.custody_btc + self.daily_volume_btc) / 2
    
    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class MiningPool:
    """Bitcoin mining pool"""
    id: str
    name: str
    hashrate_pct: float       # % of total network hashrate
    location: str             # Geographic location
    
    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class User:
    """Individual user or small entity"""
    id: str
    custody_btc: float
    daily_volume_btc: float
    user_type: str  # 'whale', 'large', 'medium', 'small'
    
    def consensus_weight(self) -> float:
        """Calculate BCAP consensus weight"""
        return (self.custody_btc + self.daily_volume_btc) / 2
    
    def to_dict(self) -> dict:
        return asdict(self)

class EntityDatabase:
    """
    Database of all network entities with realistic values
    """
    
    def __init__(self):
        self.exchanges: List[Exchange] = []
        self.mining_pools: List[MiningPool] = []
        self.users: List[User] = []
        
        self._initialize_realistic_entities()
    
    def _initialize_realistic_entities(self):
        """Create realistic entity population"""
        
        # === MAJOR EXCHANGES (Top 3) ===
        # Based on realistic custody and volume estimates
        
        self.exchanges = [
            Exchange(
                id='exchange-0000',
                name='Major Exchange 1',
                custody_btc=2_000_000,      # 2M BTC (~10% of supply)
                daily_volume_btc=200_000,   # 200K BTC/day
                withdrawal_volume_btc=10_000,
                deposit_volume_btc=10_000
            ),
            Exchange(
                id='exchange-0001',
                name='Major Exchange 2',
                custody_btc=1_200_000,      # 1.2M BTC (~6% of supply)
                daily_volume_btc=120_000,   # 120K BTC/day
                withdrawal_volume_btc=6_000,
                deposit_volume_btc=6_000
            ),
            Exchange(
                id='exchange-0002',
                name='Major Exchange 3',
                custody_btc=800_000,        # 800K BTC (~4% of supply)
                daily_volume_btc=80_000,    # 80K BTC/day
                withdrawal_volume_btc=4_000,
                deposit_volume_btc=4_000
            )
        ]
        
        # === MINING POOLS (Top 5 by realistic hashrate) ===
        # Based on actual mining pool distribution
        
        self.mining_pools = [
            MiningPool(
                id='pool-foundry',
                name='Foundry USA',
                hashrate_pct=26.89,
                location='USA'
            ),
            MiningPool(
                id='pool-antpool',
                name='AntPool',
                hashrate_pct=23.11,
                location='China'
            ),
            MiningPool(
                id='pool-f2pool',
                name='F2Pool',
                hashrate_pct=14.22,
                location='China'
            ),
            MiningPool(
                id='pool-viabtc',
                name='ViaBTC',
                hashrate_pct=10.78,
                location='China'
            ),
            MiningPool(
                id='pool-binance',
                name='Binance Pool',
                hashrate_pct=10.00,
                location='Multiple'
            )
        ]
        
        # Remaining hashrate distributed among smaller pools
        remaining_hashrate = 100 - sum(p.hashrate_pct for p in self.mining_pools)
        
        self.mining_pools.append(
            MiningPool(
                id='pool-other',
                name='Other Pools',
                hashrate_pct=remaining_hashrate,
                location='Multiple'
            )
        )
        
        # === USERS (Power-law distribution) ===
        self.users = self._generate_user_population(
            total_count=1000,
            total_custody_btc=200_000,  # ~1% of supply
            total_volume_btc=20_000,    # ~5% of on-chain volume
            exponent=2.0  # Power-law exponent
        )
    
    def _generate_user_population(
        self, 
        total_count: int,
        total_custody_btc: float,
        total_volume_btc: float,
        exponent: float = 2.0
    ) -> List[User]:
        """
        Generate user population with power-law distribution
        
        Power-law: A few whales, many small users
        """
        users = []
        
        # Generate power-law weights
        ranks = list(range(1, total_count + 1))
        weights = [1 / (r ** exponent) for r in ranks]
        total_weight = sum(weights)
        
        # Normalize to get fractions
        fractions = [w / total_weight for w in weights]
        
        # Assign custody and volume
        for i, fraction in enumerate(fractions):
            custody = total_custody_btc * fraction
            volume = total_volume_btc * fraction
            
            # Classify user type
            if custody > 100:
                user_type = 'whale'
            elif custody > 10:
                user_type = 'large'
            elif custody > 1:
                user_type = 'medium'
            else:
                user_type = 'small'
            
            user = User(
                id=f'user-{i:04d}',
                custody_btc=custody,
                daily_volume_btc=volume,
                user_type=user_type
            )
            users.append(user)
        
        return users
    
    def get_total_custody(self) -> float:
        """Total BTC in custody across all entities"""
        exchange_custody = sum(e.custody_btc for e in self.exchanges)
        user_custody = sum(u.custody_btc for u in self.users)
        return exchange_custody + user_custody
    
    def get_total_volume(self) -> float:
        """Total daily volume across all entities"""
        exchange_volume = sum(e.daily_volume_btc for e in self.exchanges)
        user_volume = sum(u.daily_volume_btc for u in self.users)
        return exchange_volume + user_volume
    
    def get_total_hashrate(self) -> float:
        """Total hashrate (should always be 100%)"""
        return sum(p.hashrate_pct for p in self.mining_pools)
    
    def summary(self) -> dict:
        """Summary statistics"""
        return {
            'exchanges': {
                'count': len(self.exchanges),
                'total_custody_btc': sum(e.custody_btc for e in self.exchanges),
                'total_volume_btc': sum(e.daily_volume_btc for e in self.exchanges),
                'avg_custody_btc': sum(e.custody_btc for e in self.exchanges) / len(self.exchanges)
            },
            'mining_pools': {
                'count': len(self.mining_pools),
                'total_hashrate_pct': sum(p.hashrate_pct for p in self.mining_pools),
                'top_3_hashrate_pct': sum(sorted([p.hashrate_pct for p in self.mining_pools], reverse=True)[:3])
            },
            'users': {
                'count': len(self.users),
                'total_custody_btc': sum(u.custody_btc for u in self.users),
                'total_volume_btc': sum(u.daily_volume_btc for u in self.users),
                'whales': len([u for u in self.users if u.user_type == 'whale']),
                'large': len([u for u in self.users if u.user_type == 'large']),
                'medium': len([u for u in self.users if u.user_type == 'medium']),
                'small': len([u for u in self.users if u.user_type == 'small'])
            },
            'network_total': {
                'total_custody_btc': self.get_total_custody(),
                'total_volume_btc': self.get_total_volume(),
                'total_hashrate_pct': self.get_total_hashrate()
            }
        }
    
    def save(self, filename: str):
        """Save database to JSON"""
        data = {
            'exchanges': [e.to_dict() for e in self.exchanges],
            'mining_pools': [p.to_dict() for p in self.mining_pools],
            'users': [u.to_dict() for u in self.users],
            'summary': self.summary()
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ Saved entity database to {filename}")
    
    @classmethod
    def load(cls, filename: str) -> 'EntityDatabase':
        """Load database from JSON"""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        db = cls.__new__(cls)  # Create without __init__
        
        db.exchanges = [Exchange(**e) for e in data['exchanges']]
        db.mining_pools = [MiningPool(**p) for p in data['mining_pools']]
        db.users = [User(**u) for u in data['users']]
        
        return db

# === EXAMPLE USAGE ===

if __name__ == "__main__":
    print("="*80)
    print("ENTITY DATABASE - BITCOIN NETWORK COMPOSITION")
    print("="*80)
    
    # Create database
    db = EntityDatabase()
    
    # Print summary
    print("\n### NETWORK SUMMARY ###\n")
    summary = db.summary()
    
    print(f"Exchanges: {summary['exchanges']['count']}")
    print(f"  Total custody: {summary['exchanges']['total_custody_btc']:,.0f} BTC")
    print(f"  Total volume:  {summary['exchanges']['total_volume_btc']:,.0f} BTC/day")
    print(f"  Avg custody:   {summary['exchanges']['avg_custody_btc']:,.0f} BTC")
    
    print(f"\nMining Pools: {summary['mining_pools']['count']}")
    print(f"  Total hashrate: {summary['mining_pools']['total_hashrate_pct']:.2f}%")
    print(f"  Top 3 pools:    {summary['mining_pools']['top_3_hashrate_pct']:.2f}%")
    
    print(f"\nUsers: {summary['users']['count']}")
    print(f"  Total custody: {summary['users']['total_custody_btc']:,.0f} BTC")
    print(f"  Total volume:  {summary['users']['total_volume_btc']:,.0f} BTC/day")
    print(f"  Whales (>100 BTC):  {summary['users']['whales']}")
    print(f"  Large (10-100):     {summary['users']['large']}")
    print(f"  Medium (1-10):      {summary['users']['medium']}")
    print(f"  Small (<1):         {summary['users']['small']}")
    
    print(f"\n### NETWORK TOTALS ###\n")
    print(f"Total custody: {summary['network_total']['total_custody_btc']:,.0f} BTC")
    print(f"Total volume:  {summary['network_total']['total_volume_btc']:,.0f} BTC/day")
    print(f"Total hashrate: {summary['network_total']['total_hashrate_pct']:.2f}%")
    
    print("\n### INDIVIDUAL EXCHANGES ###\n")
    for ex in db.exchanges:
        weight = ex.consensus_weight()
        print(f"{ex.name}:")
        print(f"  Custody: {ex.custody_btc:,.0f} BTC")
        print(f"  Volume:  {ex.daily_volume_btc:,.0f} BTC/day")
        print(f"  Weight:  {weight:,.0f}")
        print()
    
    print("### MINING POOLS ###\n")
    for pool in db.mining_pools:
        print(f"{pool.name}: {pool.hashrate_pct:.2f}% ({pool.location})")
    
    print("\n### TOP 10 USERS ###\n")
    for user in db.users[:10]:
        weight = user.consensus_weight()
        print(f"{user.id} ({user.user_type}): {user.custody_btc:.2f} BTC, "
              f"{user.daily_volume_btc:.2f} BTC/day, weight: {weight:.2f}")
    
    # Save to file
    db.save('entity_database.json')
    
    print("\n" + "="*80)
    print("✓ Entity database created and saved!")
    print("="*80)
