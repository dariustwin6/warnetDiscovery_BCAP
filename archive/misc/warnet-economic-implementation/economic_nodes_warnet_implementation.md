# Implementing Economic Nodes in Warnet Scenarios

## Table of Contents
1. [Overview](#overview)
2. [Conceptual Model](#conceptual-model)
3. [Implementation Approaches](#implementation-approaches)
4. [Configuration Examples](#configuration-examples)
5. [Scenario Testing](#scenario-testing)
6. [Monitoring & Metrics](#monitoring--metrics)
7. [Advanced Patterns](#advanced-patterns)

---

## Overview

Economic Nodes in Bitcoin represent nodes operated by exchanges, payment processors, custody providers, and other high-volume transaction participants. In Warnet testing, we need to simulate their unique characteristics:

- **High transaction volume** (receiving/sending)
- **Critical network position** (many connections)
- **Validation authority** (their acceptance determines "real" Bitcoin)
- **Market influence** (can create futures markets, list forks)

### Key Characteristics to Model

| Characteristic | Implementation Method |
|----------------|----------------------|
| Transaction Volume | Generate transactions targeting these nodes |
| Network Centrality | Increase connection count, strategic topology placement |
| Validation Weight | Track their acceptance in criticality scoring |
| Market Influence | Simulate price discovery based on their choices |

---

## Conceptual Model

### Three-Tier Node Classification

```
┌─────────────────────────────────────────┐
│         ECONOMIC NODES (10-15%)         │
│  - Exchanges (Coinbase, Binance)        │
│  - Payment Processors (BitPay)          │
│  - Custody Providers (Fidelity)         │
│  - High transaction volume              │
│  - Network influence weight: 10x        │
└─────────────────────────────────────────┘
             ↑ ↓ ↑ ↓ ↑ ↓
┌─────────────────────────────────────────┐
│      RELAY NODES (60-70%)               │
│  - Standard full nodes                  │
│  - Medium connectivity                  │
│  - Network influence weight: 1x         │
└─────────────────────────────────────────┘
             ↑ ↓ ↑ ↓ ↑ ↓
┌─────────────────────────────────────────┐
│      CONSTRAINED NODES (20-30%)         │
│  - Limited resources                    │
│  - Lower connectivity                   │
│  - Network influence weight: 0.5x       │
└─────────────────────────────────────────┘
```

---

## Implementation Approaches

### Approach 1: YAML Configuration with Tags

Use custom tags in `network.yaml` to designate Economic Nodes:

```yaml
# network.yaml
nodes:
  - name: exchange-node-1
    image: "bitcoindevproject/bitcoin:27.0"
    tags:
      - economic_node
      - exchange
      - high_volume
    weight: 10  # Economic influence multiplier
    bitcoin_config:
      maxconnections: 1000
      maxmempool: 5000  # 5GB mempool
      rpcthreads: 16
    resources:
      cpu: "4000m"
      memory: "8Gi"
    connections:
      - exchange-node-2
      - relay-node-1
      - relay-node-2
      - relay-node-5
      - relay-node-10
      # ... more connections
      
  - name: exchange-node-2
    image: "bitcoindevproject/bitcoin:27.0"
    tags:
      - economic_node
      - exchange
      - high_volume
    weight: 10
    bitcoin_config:
      maxconnections: 1000
      maxmempool: 5000
    resources:
      cpu: "4000m"
      memory: "8Gi"
      
  - name: payment-processor-1
    image: "bitcoindevproject/bitcoin:27.0"
    tags:
      - economic_node
      - payment_processor
      - medium_volume
    weight: 8
    bitcoin_config:
      maxconnections: 500
      maxmempool: 2000
    resources:
      cpu: "2000m"
      memory: "4Gi"
      
  - name: custody-provider-1
    image: "bitcoindevproject/bitcoin:27.0"
    tags:
      - economic_node
      - custody
      - high_security
    weight: 7
    bitcoin_config:
      maxconnections: 300
      maxmempool: 3000
      # Higher security settings
      whitelist: "127.0.0.1"
    resources:
      cpu: "2000m"
      memory: "6Gi"
      
  # Standard relay nodes (60-70% of network)
  - name: relay-node-1
    image: "bitcoindevproject/bitcoin:27.0"
    tags:
      - relay_node
      - standard
    weight: 1
    bitcoin_config:
      maxconnections: 125
      maxmempool: 300
    resources:
      cpu: "1000m"
      memory: "2Gi"
      
  # ... (repeat for relay-node-2 through relay-node-70)
  
  # Constrained nodes (20-30% of network)
  - name: constrained-node-1
    image: "bitcoindevproject/bitcoin:26.0"  # Older version
    tags:
      - constrained_node
      - resource_limited
    weight: 0.5
    bitcoin_config:
      maxconnections: 8
      maxmempool: 50  # 50MB only
    resources:
      cpu: "250m"
      memory: "512Mi"
      
  # ... (repeat for constrained-node-2 through constrained-node-30)
```

### Approach 2: Node Defaults with Overrides

Use `node-defaults.yaml` for base configuration, then override for Economic Nodes:

```yaml
# node-defaults.yaml
bitcoin_config:
  maxconnections: 125
  maxmempool: 300
  blockmaxweight: 4000000
  
resources:
  cpu: "1000m"
  memory: "2Gi"
  
tags:
  - relay_node
  - standard
  
weight: 1
```

```yaml
# network.yaml (Economic Node overrides)
nodes:
  - name: exchange-coinbase
    override_defaults: true
    image: "bitcoindevproject/bitcoin:27.0"
    tags:
      - economic_node
      - exchange
      - tier_1
    weight: 15  # Highest influence
    bitcoin_config:
      maxconnections: 2000
      maxmempool: 10000
      rpcthreads: 32
      # Custom txindex for exchange operations
      txindex: 1
    resources:
      cpu: "8000m"
      memory: "16Gi"
    network_position: "central"  # Place in hub position
```

### Approach 3: Programmatic Generation

Generate network topology programmatically with Economic Node distribution:

```python
# generate_economic_network.py
import yaml
import random

def generate_warnet_network(
    total_nodes=100,
    economic_node_pct=0.15,
    relay_node_pct=0.65,
    constrained_node_pct=0.20
):
    """Generate Warnet network.yaml with Economic Node distribution."""
    
    num_economic = int(total_nodes * economic_node_pct)
    num_relay = int(total_nodes * relay_node_pct)
    num_constrained = total_nodes - num_economic - num_relay
    
    nodes = []
    
    # Economic Nodes
    economic_types = [
        ("exchange", 10, 1000, 5000),
        ("payment_processor", 8, 500, 2000),
        ("custody", 7, 300, 3000),
    ]
    
    for i in range(num_economic):
        node_type, weight, max_conn, mempool = random.choice(economic_types)
        node = {
            "name": f"economic-{node_type}-{i}",
            "image": "bitcoindevproject/bitcoin:27.0",
            "tags": ["economic_node", node_type, "high_volume"],
            "weight": weight,
            "bitcoin_config": {
                "maxconnections": max_conn,
                "maxmempool": mempool,
                "rpcthreads": 16,
            },
            "resources": {
                "cpu": "4000m",
                "memory": "8Gi"
            }
        }
        nodes.append(node)
    
    # Relay Nodes
    for i in range(num_relay):
        node = {
            "name": f"relay-{i}",
            "image": "bitcoindevproject/bitcoin:27.0",
            "tags": ["relay_node", "standard"],
            "weight": 1,
            "bitcoin_config": {
                "maxconnections": 125,
                "maxmempool": 300,
            },
            "resources": {
                "cpu": "1000m",
                "memory": "2Gi"
            }
        }
        nodes.append(node)
    
    # Constrained Nodes
    for i in range(num_constrained):
        node = {
            "name": f"constrained-{i}",
            "image": "bitcoindevproject/bitcoin:25.0",  # Older version
            "tags": ["constrained_node", "resource_limited"],
            "weight": 0.5,
            "bitcoin_config": {
                "maxconnections": 8,
                "maxmempool": 50,
            },
            "resources": {
                "cpu": "250m",
                "memory": "512Mi"
            }
        }
        nodes.append(node)
    
    # Generate connections (Economic Nodes are hubs)
    for node in nodes:
        if "economic_node" in node["tags"]:
            # Economic nodes connect to many peers
            num_connections = random.randint(20, 50)
        elif "relay_node" in node["tags"]:
            num_connections = random.randint(8, 20)
        else:
            num_connections = random.randint(3, 8)
        
        # Select random peers (excluding self)
        available_peers = [n["name"] for n in nodes if n["name"] != node["name"]]
        node["connections"] = random.sample(available_peers, 
                                           min(num_connections, len(available_peers)))
    
    network_config = {
        "network": {
            "name": "economic-node-test",
            "nodes": nodes
        }
    }
    
    with open("network.yaml", "w") as f:
        yaml.dump(network_config, f, default_flow_style=False)
    
    return network_config

if __name__ == "__main__":
    config = generate_warnet_network(total_nodes=100)
    print(f"Generated network with {len(config['network']['nodes'])} nodes")
```

---

## Configuration Examples

### Example 1: Basic Economic Node Network (20 nodes)

```yaml
# networks/basic-economic/network.yaml
network:
  name: basic-economic-test
  
nodes:
  # 3 Economic Nodes (15%)
  - name: exchange-1
    image: "bitcoindevproject/bitcoin:27.0"
    tags: [economic_node, exchange]
    weight: 10
    bitcoin_config:
      maxconnections: 500
      maxmempool: 5000
    resources:
      cpu: "4000m"
      memory: "8Gi"
    connections: [exchange-2, relay-1, relay-2, relay-3, relay-5, relay-8, relay-10]
    
  - name: exchange-2
    image: "bitcoindevproject/bitcoin:27.0"
    tags: [economic_node, exchange]
    weight: 10
    bitcoin_config:
      maxconnections: 500
      maxmempool: 5000
    resources:
      cpu: "4000m"
      memory: "8Gi"
    connections: [exchange-1, relay-2, relay-4, relay-6, relay-7, relay-9]
    
  - name: payment-processor-1
    image: "bitcoindevproject/bitcoin:27.0"
    tags: [economic_node, payment_processor]
    weight: 8
    bitcoin_config:
      maxconnections: 300
      maxmempool: 2000
    resources:
      cpu: "2000m"
      memory: "4Gi"
    connections: [exchange-1, relay-1, relay-3, relay-5, relay-7]
  
  # 13 Relay Nodes (65%)
  - name: relay-1
    image: "bitcoindevproject/bitcoin:27.0"
    tags: [relay_node]
    weight: 1
    bitcoin_config:
      maxconnections: 125
      maxmempool: 300
    resources:
      cpu: "1000m"
      memory: "2Gi"
    connections: [exchange-1, relay-2, relay-3, constrained-1]
  
  # ... (relay-2 through relay-13)
  
  # 4 Constrained Nodes (20%)
  - name: constrained-1
    image: "bitcoindevproject/bitcoin:25.0"
    tags: [constrained_node]
    weight: 0.5
    bitcoin_config:
      maxconnections: 8
      maxmempool: 50
    resources:
      cpu: "250m"
      memory: "512Mi"
    connections: [relay-1, relay-5]
  
  # ... (constrained-2 through constrained-4)
```

### Example 2: Mixed Version with Economic Nodes

```yaml
# networks/version-mix-economic/network.yaml
network:
  name: version-mix-economic-test
  
nodes:
  # Economic Nodes on latest version
  - name: exchange-latest
    image: "bitcoindevproject/bitcoin:27.0"
    tags: [economic_node, exchange, version_latest]
    weight: 10
    bitcoin_config:
      maxconnections: 1000
      maxmempool: 5000
    
  # Economic Node on previous version (testing compatibility)
  - name: exchange-previous
    image: "bitcoindevproject/bitcoin:26.0"
    tags: [economic_node, exchange, version_previous]
    weight: 10
    bitcoin_config:
      maxconnections: 1000
      maxmempool: 5000
    
  # Relay nodes mixed versions
  - name: relay-latest-1
    image: "bitcoindevproject/bitcoin:27.0"
    tags: [relay_node, version_latest]
    weight: 1
    
  - name: relay-previous-1
    image: "bitcoindevproject/bitcoin:26.0"
    tags: [relay_node, version_previous]
    weight: 1
    
  - name: relay-old-1
    image: "bitcoindevproject/bitcoin:25.0"
    tags: [relay_node, version_old]
    weight: 1
    
  # Constrained nodes on older versions
  - name: constrained-old-1
    image: "bitcoindevproject/bitcoin:24.0"
    tags: [constrained_node, version_old]
    weight: 0.5
```

### Example 3: Soft Fork Testing with Economic Nodes

```yaml
# networks/softfork-economic/network.yaml
network:
  name: softfork-activation-test
  
nodes:
  # Economic Nodes - Split adoption
  # 60% upgraded
  - name: exchange-upgraded-1
    image: "bitcoindevproject/bitcoin:27.0-softfork"  # Custom image with soft fork
    tags: [economic_node, exchange, upgraded]
    weight: 10
    bitcoin_config:
      maxconnections: 1000
      maxmempool: 5000
    signaling: true  # Signal readiness for soft fork
    
  - name: exchange-upgraded-2
    image: "bitcoindevproject/bitcoin:27.0-softfork"
    tags: [economic_node, exchange, upgraded]
    weight: 10
    signaling: true
    
  - name: payment-processor-upgraded
    image: "bitcoindevproject/bitcoin:27.0-softfork"
    tags: [economic_node, payment_processor, upgraded]
    weight: 8
    signaling: true
  
  # 40% not upgraded (legacy)
  - name: exchange-legacy-1
    image: "bitcoindevproject/bitcoin:27.0"  # No soft fork
    tags: [economic_node, exchange, legacy]
    weight: 10
    signaling: false
    
  - name: custody-legacy-1
    image: "bitcoindevproject/bitcoin:27.0"
    tags: [economic_node, custody, legacy]
    weight: 7
    signaling: false
  
  # Relay nodes - mixed
  # ... (50% upgraded, 50% legacy)
  
  # Miners - signaling
  - name: miner-1
    image: "bitcoindevproject/bitcoin:27.0-softfork"
    tags: [miner, signaling]
    weight: 5
    bitcoin_config:
      # Mining configuration
    signaling: true
```

---

## Scenario Testing

### Scenario 1: Economic Node Consensus Test

```python
# scenarios/economic_node_consensus.py
"""
Test how Economic Node adoption affects network consensus.
Scenario: Introduce chain split, measure which chain Economic Nodes follow.
"""

from warnet.test_framework.test_framework import BitcoinTestFramework
from warnet.test_framework.util import assert_equal

class EconomicNodeConsensusTest(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 50
        self.setup_clean_chain = True
        
    def setup_network(self):
        """Network with 10% Economic Nodes."""
        self.economic_nodes = []
        self.relay_nodes = []
        
        # Identify Economic Nodes from tags
        for node in self.nodes:
            tags = node.get_tags()
            if 'economic_node' in tags:
                self.economic_nodes.append(node)
            else:
                self.relay_nodes.append(node)
        
        self.log.info(f"Economic Nodes: {len(self.economic_nodes)}")
        self.log.info(f"Relay Nodes: {len(self.relay_nodes)}")
        
    def run_test(self):
        """
        1. Create two competing chains
        2. Measure which chain Economic Nodes follow
        3. Calculate economic consensus score
        """
        self.log.info("Creating competing chains...")
        
        # Chain A: Followed by 60% of Economic Nodes
        # Chain B: Followed by 40% of Economic Nodes
        
        chain_a_economic = self.economic_nodes[:int(len(self.economic_nodes) * 0.6)]
        chain_b_economic = self.economic_nodes[int(len(self.economic_nodes) * 0.6):]
        
        # Force chain split
        self.generate_competing_chains(chain_a_economic, chain_b_economic)
        
        # Calculate economic consensus score
        chain_a_weight = sum([n.get_weight() for n in chain_a_economic])
        chain_b_weight = sum([n.get_weight() for n in chain_b_economic])
        
        total_economic_weight = chain_a_weight + chain_b_weight
        
        economic_consensus_score = abs(chain_a_weight - chain_b_weight) / total_economic_weight
        
        self.log.info(f"Chain A Economic Weight: {chain_a_weight}")
        self.log.info(f"Chain B Economic Weight: {chain_b_weight}")
        self.log.info(f"Economic Consensus Score: {economic_consensus_score}")
        
        # Score > 0.5 means strong consensus
        # Score < 0.2 means dangerous fragmentation
        
        if economic_consensus_score < 0.3:
            self.log.warning("CRITICAL: Economic Node fragmentation detected!")
            self.log.warning("High risk of sustained chain split")
        
        # Measure transaction flow
        self.test_transaction_propagation()
        
    def generate_competing_chains(self, chain_a_nodes, chain_b_nodes):
        """Generate two competing chain tips."""
        # Implementation details...
        pass
    
    def test_transaction_propagation(self):
        """Test if transactions propagate across Economic Node divide."""
        # Send transaction from Chain A node
        # Check if Chain B Economic Nodes see it
        pass
```

### Scenario 2: Bounty Claim Attack with Economic Nodes

```python
# scenarios/bounty_claim_attack.py
"""
Simulate BCAP bounty claim scenario with Economic Node adoption rates.
"""

from warnet.test_framework.test_framework import BitcoinTestFramework
import time

class BountyClaimAttackTest(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 100
        self.setup_clean_chain = False
        
    def setup_network(self):
        """
        Network setup:
        - 70% Economic Nodes upgraded to soft fork
        - 30% Economic Nodes on legacy rules
        - Build up bounty in soft-fork-specific scripts
        """
        self.upgraded_economic = []
        self.legacy_economic = []
        self.relay_nodes = []
        
        for node in self.nodes:
            tags = node.get_tags()
            if 'economic_node' in tags:
                if 'upgraded' in tags:
                    self.upgraded_economic.append(node)
                else:
                    self.legacy_economic.append(node)
            else:
                self.relay_nodes.append(node)
        
        self.log.info(f"Upgraded Economic Nodes: {len(self.upgraded_economic)}")
        self.log.info(f"Legacy Economic Nodes: {len(self.legacy_economic)}")
        
    def run_test(self):
        """
        1. Users lock BTC in soft-fork-specific scripts
        2. Build up "bounty" to 200 BTC
        3. Inject high-fee legacy transaction claiming bounty
        4. Measure if chain split occurs
        5. Track Economic Node responses
        """
        self.log.info("Phase 1: Building up bounty...")
        
        bounty_amount = 0
        target_bounty = 200  # BTC
        
        # Deposit transactions using soft fork features
        while bounty_amount < target_bounty:
            # Create transaction using OP_SUCCESS-based script
            tx = self.create_soft_fork_deposit(amount=10)
            self.nodes[0].sendrawtransaction(tx)
            bounty_amount += 10
            self.log.info(f"Bounty accumulated: {bounty_amount} BTC")
        
        self.log.info(f"Phase 2: Bounty at {bounty_amount} BTC")
        
        # Inject bounty claim transaction (high fee, legacy rules)
        self.log.info("Phase 3: Injecting bounty claim attack...")
        
        attack_tx = self.create_bounty_claim_tx(
            bounty_amount=bounty_amount,
            fee=20  # 20 BTC fee to incentivize miners
        )
        
        # Send to legacy nodes
        self.legacy_economic[0].sendrawtransaction(attack_tx)
        
        # Wait for propagation
        time.sleep(10)
        
        # Phase 4: Measure chain split
        self.log.info("Phase 4: Checking for chain split...")
        
        chain_tips = self.get_chain_tips_all_nodes()
        
        unique_tips = set(chain_tips.values())
        
        if len(unique_tips) > 1:
            self.log.warning("CHAIN SPLIT DETECTED!")
            self.analyze_chain_split(chain_tips)
        else:
            self.log.info("No chain split occurred")
        
        # Phase 5: Economic Node response analysis
        self.analyze_economic_node_response()
        
    def analyze_chain_split(self, chain_tips):
        """Analyze which nodes follow which chain."""
        chains = {}
        
        for node, tip in chain_tips.items():
            if tip not in chains:
                chains[tip] = {
                    'nodes': [],
                    'economic_weight': 0,
                    'hash_power': 0
                }
            
            chains[tip]['nodes'].append(node)
            
            # Calculate economic weight
            if node in self.upgraded_economic or node in self.legacy_economic:
                weight = node.get_weight()
                chains[tip]['economic_weight'] += weight
        
        self.log.info("Chain split analysis:")
        for chain_id, data in chains.items():
            self.log.info(f"  Chain {chain_id[:8]}...")
            self.log.info(f"    Nodes: {len(data['nodes'])}")
            self.log.info(f"    Economic Weight: {data['economic_weight']}")
        
        # Calculate fragmentation score
        weights = [d['economic_weight'] for d in chains.values()]
        total_weight = sum(weights)
        fragmentation = 1 - (max(weights) / total_weight)
        
        self.log.info(f"Economic Fragmentation Score: {fragmentation:.2f}")
        
        if fragmentation > 0.3:
            self.log.warning("HIGH FRAGMENTATION: Sustained chain split likely")
        
    def analyze_economic_node_response(self):
        """Track how Economic Nodes respond to bounty claim."""
        # Implementation...
        pass
```

### Scenario 3: False Signaling Detection

```python
# scenarios/false_signaling_detection.py
"""
Detect miners signaling for soft fork without actually enforcing rules.
Economic Nodes play key role in detecting this.
"""

from warnet.test_framework.test_framework import BitcoinTestFramework

class FalseSignalingTest(BitcoinTestFramework):
    def run_test(self):
        """
        1. Some miners signal readiness
        2. But don't enforce new rules
        3. Economic Nodes detect discrepancy
        4. Measure reorg risk
        """
        
        # Check miner signaling
        signaling_miners = self.get_signaling_miners()
        
        # Create transaction violating new rules
        invalid_under_new_rules_tx = self.create_soft_fork_violating_tx()
        
        # Check which miners mine it
        false_signalers = []
        
        for miner in signaling_miners:
            # Submit to miner
            result = miner.submit_block_template_with_tx(invalid_under_new_rules_tx)
            
            if result['accepted']:
                false_signalers.append(miner)
                self.log.warning(f"Miner {miner.name} false signaling!")
        
        false_signal_rate = len(false_signalers) / len(signaling_miners)
        
        self.log.info(f"False Signaling Rate: {false_signal_rate:.2%}")
        
        if false_signal_rate > 0.05:  # > 5%
            self.log.warning("CRITICAL: Significant false signaling detected")
            self.log.warning("Reorg risk elevated")
        
        # Track Economic Node response
        self.test_economic_node_validation(invalid_under_new_rules_tx)
```

---

## Monitoring & Metrics

### Custom Metrics for Economic Nodes

```python
# monitoring/economic_node_metrics.py
"""
Custom Prometheus metrics for Economic Node monitoring.
"""

from prometheus_client import Gauge, Counter, Histogram

# Economic Node specific metrics
economic_node_weight = Gauge(
    'warnet_economic_node_weight',
    'Economic influence weight of node',
    ['node_name', 'node_type']
)

economic_transaction_volume = Counter(
    'warnet_economic_transaction_volume',
    'Transaction volume through Economic Nodes',
    ['node_name', 'direction']  # direction: inbound/outbound
)

economic_consensus_score = Gauge(
    'warnet_economic_consensus_score',
    'Consensus score based on Economic Node agreement'
)

chain_split_economic_weight = Gauge(
    'warnet_chain_split_economic_weight',
    'Economic weight on each side of chain split',
    ['chain_id']
)

economic_node_validation_latency = Histogram(
    'warnet_economic_node_validation_latency',
    'Block validation latency for Economic Nodes',
    ['node_name']
)

bounty_accumulated = Gauge(
    'warnet_soft_fork_bounty_btc',
    'BTC accumulated in soft-fork-specific scripts'
)

def calculate_economic_consensus_score(network_state):
    """
    Calculate consensus score based on Economic Node positions.
    Returns value 0-1 where:
    - 1.0 = Perfect consensus
    - 0.5 = Maximum fragmentation
    - 0.0 = Impossible (would require negative weight)
    """
    chain_tips = {}
    
    for node in network_state.economic_nodes:
        tip = node.get_best_block_hash()
        weight = node.get_weight()
        
        if tip not in chain_tips:
            chain_tips[tip] = 0
        
        chain_tips[tip] += weight
    
    if len(chain_tips) == 0:
        return 1.0
    
    weights = list(chain_tips.values())
    total_weight = sum(weights)
    max_weight = max(weights)
    
    # Consensus score: how much weight is on dominant chain
    score = max_weight / total_weight
    
    return score

def calculate_bounty_risk(network_state):
    """
    Calculate risk score for bounty claim attacks.
    """
    bounty_amount = network_state.get_soft_fork_bounty_amount()
    economic_adoption = network_state.get_economic_node_adoption_rate()
    
    # Risk increases with bounty size and decreases with adoption
    risk_score = (bounty_amount / 100) * (1 - economic_adoption)
    
    return min(risk_score, 1.0)
```

### Grafana Dashboard for Economic Nodes

```yaml
# dashboards/economic_nodes.json (simplified)
{
  "dashboard": {
    "title": "Economic Node Monitoring",
    "panels": [
      {
        "title": "Economic Consensus Score",
        "targets": [
          {
            "expr": "warnet_economic_consensus_score"
          }
        ],
        "alert": {
          "conditions": [
            {
              "evaluator": {
                "params": [0.7],
                "type": "lt"
              },
              "operator": {
                "type": "and"
              },
              "query": {
                "params": ["A", "5m", "now"]
              },
              "reducer": {
                "type": "last"
              },
              "type": "query"
            }
          ],
          "message": "Economic consensus score below 0.7 - potential fragmentation"
        }
      },
      {
        "title": "Chain Split Economic Weight",
        "targets": [
          {
            "expr": "warnet_chain_split_economic_weight"
          }
        ]
      },
      {
        "title": "Bounty Risk Score",
        "targets": [
          {
            "expr": "warnet_soft_fork_bounty_btc * (1 - warnet_economic_node_adoption_rate)"
          }
        ]
      },
      {
        "title": "Transaction Volume by Economic Node",
        "targets": [
          {
            "expr": "rate(warnet_economic_transaction_volume[5m])"
          }
        ]
      }
    ]
  }
}
```

---

## Advanced Patterns

### Pattern 1: Dynamic Economic Node Weight Adjustment

```python
# scenarios/dynamic_weight_adjustment.py
"""
Adjust Economic Node weights dynamically based on transaction volume.
Simulates real-world where exchanges grow/shrink in importance.
"""

class DynamicWeightAdjustment:
    def __init__(self, network):
        self.network = network
        self.transaction_history = {}
        
    def update_weights(self):
        """Update Economic Node weights based on recent activity."""
        
        for node in self.network.get_economic_nodes():
            # Calculate transaction volume last 1000 blocks
            volume = self.calculate_transaction_volume(node, blocks=1000)
            
            # Adjust weight based on volume
            base_weight = node.get_base_weight()
            
            if volume > 10000:  # Very high volume
                new_weight = base_weight * 1.5
            elif volume > 5000:  # High volume
                new_weight = base_weight * 1.2
            elif volume < 1000:  # Low volume
                new_weight = base_weight * 0.8
            else:
                new_weight = base_weight
            
            node.set_weight(new_weight)
            
            print(f"Node {node.name}: volume={volume}, weight={new_weight}")
```

### Pattern 2: Economic Node Cartel Formation

```python
# scenarios/economic_cartel.py
"""
Simulate scenario where Economic Nodes coordinate (cartel).
Tests network resilience to coordinated action.
"""

class EconomicCartelTest(BitcoinTestFramework):
    def run_test(self):
        """
        Test: Top 3 Economic Nodes (60% of weight) coordinate
        to reject specific transactions or enforce fork choice.
        """
        
        # Identify top Economic Nodes by weight
        sorted_economic = sorted(
            self.economic_nodes,
            key=lambda n: n.get_weight(),
            reverse=True
        )
        
        cartel = sorted_economic[:3]
        cartel_weight = sum([n.get_weight() for n in cartel])
        total_weight = sum([n.get_weight() for n in self.economic_nodes])
        
        cartel_pct = cartel_weight / total_weight
        
        self.log.info(f"Cartel controls {cartel_pct:.1%} of economic weight")
        
        if cartel_pct > 0.51:
            self.log.warning("Cartel has majority economic weight!")
            
        # Test coordinated transaction censorship
        self.test_transaction_censorship(cartel)
        
        # Test coordinated fork choice
        self.test_fork_choice_coordination(cartel)
```

### Pattern 3: Economic Node Futures Market Simulation

```python
# scenarios/futures_market.py
"""
Simulate futures market creation by Economic Nodes during fork.
Models price discovery and miner incentive shifts.
"""

class FuturesMarketSimulation:
    def __init__(self, network):
        self.network = network
        self.markets = {}
        
    def create_fork_futures(self, fork_a, fork_b):
        """
        Economic Nodes create futures markets for both forks.
        Price discovery influences miner behavior.
        """
        
        # Initial prices (1:1)
        self.markets[fork_a] = {'price': 1.0, 'volume': 0}
        self.markets[fork_b] = {'price': 1.0, 'volume': 0}
        
        # Simulate investor trades
        for round in range(10):  # 10 trading rounds
            self.simulate_trading_round()
            self.update_miner_incentives()
            self.log_market_state()
    
    def simulate_trading_round(self):
        """Investors express preferences via trading."""
        # Simplified: assume 70% prefer fork A
        fork_a_buyers = 0.7
        fork_b_buyers = 0.3
        
        # Price adjustment
        self.markets[fork_a]['price'] *= (1 + fork_a_buyers * 0.1)
        self.markets[fork_b]['price'] *= (1 + fork_b_buyers * 0.1)
        
    def update_miner_incentives(self):
        """Miners switch to more valuable fork."""
        fork_a_value = self.markets[fork_a]['price']
        fork_b_value = self.markets[fork_b]['price']
        
        # Miners allocate hashpower proportional to value
        # (simplified)
        for miner in self.network.get_miners():
            if fork_a_value > fork_b_value * 1.1:  # 10% threshold
                miner.switch_to_fork(fork_a)
```

---

## Summary & Best Practices

### Key Implementation Principles

1. **Designate 10-15% of nodes as Economic Nodes** with elevated weights
2. **Use tags** to identify node roles (`economic_node`, `exchange`, `custody`, etc.)
3. **Configure higher resources** for Economic Nodes (CPU, memory, connections)
4. **Strategic topology placement** - Economic Nodes as network hubs
5. **Track adoption rates** - critical metric for consensus scenarios
6. **Monitor economic consensus score** - aggregate weight on each side of splits
7. **Simulate realistic transaction volume** to Economic Nodes
8. **Test bounty accumulation** in soft fork scenarios
9. **Measure response timing** - Economic Nodes often slower to react than individuals
10. **Create futures market simulations** for fork scenarios

### Critical Scenarios to Test

✅ **High Priority:**
- Economic Node partial adoption (60/40 split)
- Bounty claim attacks with varying Economic Node adoption
- False miner signaling with Economic Node detection
- Chain split with Economic Node fragmentation

✅ **Medium Priority:**
- Economic Node version compatibility
- Cartel coordination scenarios
- Futures market price discovery
- Transaction censorship by Economic Nodes

✅ **Low Priority:**
- Dynamic weight adjustments
- Economic Node failure/recovery
- Geographic distribution effects

### Monitoring Checklist

- [ ] Economic consensus score < 0.7 (fragmentation alert)
- [ ] Bounty accumulation > 100 BTC (attack risk)
- [ ] Economic Node adoption rate < 80% (activation risk)
- [ ] Chain split with economic weight < 2:1 ratio (sustained split risk)
- [ ] False signaling rate > 5% (reorg risk)
- [ ] Transaction volume anomalies at Economic Nodes

---

## Additional Resources

- **Warnet Documentation**: https://github.com/bitcoin-dev-project/warnet/tree/main/docs
- **BCAP Paper**: https://github.com/bitcoin-cap/bcap
- **Bitcoin Core Functional Tests**: https://github.com/bitcoin/bitcoin/tree/master/test/functional
- **Prometheus Metrics**: https://prometheus.io/docs/concepts/metric_types/
- **Kubernetes Resources**: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/

---

**Document Version**: 1.0  
**Last Updated**: November 2025  
**Author**: Technical Documentation for Warnet Economic Node Testing
