# Economic Nodes in Warnet - Quick Start Guide

## What You Have

I've created a complete implementation package for Economic Nodes in Warnet, based on the BCAP (Bitcoin Consensus Analysis Project) research. Here's what's included:

### 📦 Package Contents

1. **Comprehensive Implementation Guide** (`economic_nodes_warnet_implementation.md`)
   - 50+ pages of detailed documentation
   - Configuration patterns and examples
   - Testing scenarios with code
   - Monitoring and metrics setup

2. **Pre-Configured Network** (`networks/economic-30-nodes.yaml`)
   - 30-node reference network
   - 5 Economic Nodes (17%)
   - 20 Relay Nodes (66%)
   - 5 Constrained Nodes (17%)
   - Ready to deploy immediately

3. **Network Generator Script** (`scripts/economic_network_utils.py`)
   - Generate custom networks
   - Analyze existing configurations
   - Calculate BCAP metrics

4. **Complete README** with examples and workflows

## 🚀 Implementation in 3 Steps

### Step 1: Download and Extract

```bash
# Download the package
# (Link provided by Claude)

# Extract
tar -xzf warnet-economic-implementation.tar.gz
cd warnet-economic-examples
```

### Step 2: Deploy Pre-Configured Network

```bash
# Option A: Use the 30-node example directly
warnet deploy networks/economic-30-nodes.yaml

# Option B: Generate custom network
python scripts/economic_network_utils.py generate \
    --nodes 100 \
    --economic-pct 0.15 \
    --output networks/my-network.yaml

# Then deploy
warnet deploy networks/my-network.yaml
```

### Step 3: Test Economic Node Scenarios

```bash
# Verify deployment
warnet status

# Access an Economic Node
warnet exec exchange-tier1-coinbase -- bitcoin-cli getinfo

# Monitor the dashboard
warnet dashboard
```

## 🎯 How Economic Nodes Are Implemented

### In the YAML Configuration

```yaml
nodes:
  - name: exchange-tier1-coinbase
    image: "bitcoindevproject/bitcoin:27.0"
    tags:
      - economic_node        # Identifies as Economic Node
      - exchange             # Type
      - tier_1               # Tier
    metadata:
      weight: 15             # Economic influence (vs 1 for relay nodes)
      node_type: exchange
      adoption_speed: fast   # Response characteristics
    bitcoin_config:
      maxconnections: 2000   # High connectivity (vs 125 for relay)
      maxmempool: 10000      # 10GB mempool (vs 300MB for relay)
      rpcthreads: 32
      txindex: 1
    resources:
      requests:
        cpu: "4000m"         # 4 cores (vs 0.5 cores for relay)
        memory: "16Gi"       # 16GB RAM (vs 2GB for relay)
```

### Key Distinguishing Features

| Attribute | Economic Node | Relay Node | Why It Matters |
|-----------|---------------|------------|----------------|
| **Weight** | 7-15x | 1x | Economic influence in splits |
| **Connections** | 300-2000 | 125 | Network centrality/hub position |
| **Mempool** | 2-10 GB | 300 MB | Transaction volume capacity |
| **Resources** | 4-8 cores, 8-32 GB | 1 core, 2-4 GB | Real-world capacity |
| **Tags** | economic_node | relay_node | Identification in scenarios |

## 📊 Using Economic Nodes in Testing

### Scenario 1: Measure Economic Consensus

```python
# In your Warnet scenario script
economic_nodes = [n for n in nodes if 'economic_node' in n.tags]
relay_nodes = [n for n in nodes if 'relay_node' in n.tags]

# Check which chain Economic Nodes follow
chain_a_economic = [n for n in economic_nodes if n.best_block == chain_a_tip]
chain_b_economic = [n for n in economic_nodes if n.best_block == chain_b_tip]

# Calculate economic weight
chain_a_weight = sum([n.weight for n in chain_a_economic])
chain_b_weight = sum([n.weight for n in chain_b_economic])

# Economic consensus score
total_weight = chain_a_weight + chain_b_weight
consensus_score = max(chain_a_weight, chain_b_weight) / total_weight

if consensus_score < 0.7:
    print("WARNING: Economic consensus fragmented - chain split risk high")
```

### Scenario 2: Test Partial Adoption

```yaml
# Create two versions of network - some Economic Nodes upgraded
nodes:
  # 60% upgraded
  - name: exchange-upgraded-1
    image: "bitcoindevproject/bitcoin:27.0-softfork"
    tags: [economic_node, upgraded]
    weight: 15
    
  - name: exchange-upgraded-2
    image: "bitcoindevproject/bitcoin:27.0-softfork"
    tags: [economic_node, upgraded]
    weight: 15
    
  # 40% not upgraded
  - name: exchange-legacy-1
    image: "bitcoindevproject/bitcoin:27.0"
    tags: [economic_node, legacy]
    weight: 10
```

### Scenario 3: Bounty Claim Attack

```python
# Accumulate bounty in soft-fork scripts
bounty_btc = 200

# Check Economic Node adoption
upgraded_economic = [n for n in economic_nodes if 'upgraded' in n.tags]
adoption_rate = len(upgraded_economic) / len(economic_nodes)

# Calculate risk
bounty_risk = (bounty_btc / 100) * (1 - adoption_rate)

if bounty_risk > 0.5:
    print(f"CRITICAL: Bounty risk {bounty_risk:.2f} - attack likely")
    
# Inject bounty claim transaction
attack_tx = create_bounty_claim_tx(bounty_btc, fee=20)
legacy_nodes[0].send_tx(attack_tx)

# Monitor for chain split
time.sleep(10)
detect_chain_split(network)
```

## 🔍 Key Metrics to Track

### 1. Economic Weight Distribution

```bash
# Using the analyzer
python scripts/economic_network_utils.py analyze \
    --config networks/my-network.yaml

# Look for:
# - economic_weight_percentage (should be 60-80%)
# - economic_consensus_threshold_60pct
# - economic_consensus_threshold_80pct
```

### 2. Adoption Rate

```python
# In your test scenario
upgraded = [n for n in economic_nodes if n.version == '27.0-softfork']
adoption_rate = len(upgraded) / len(economic_nodes)

# Safe thresholds:
# > 0.80: Low risk
# 0.60-0.80: Medium risk  
# < 0.60: High risk of chain split
```

### 3. Economic Consensus Score

```python
def calculate_economic_consensus(network):
    chain_weights = {}
    
    for node in network.economic_nodes:
        tip = node.get_best_block()
        weight = node.weight
        
        chain_weights[tip] = chain_weights.get(tip, 0) + weight
    
    total = sum(chain_weights.values())
    max_weight = max(chain_weights.values())
    
    return max_weight / total  # 1.0 = perfect consensus

# Interpretation:
# > 0.80: Strong consensus
# 0.60-0.80: Moderate (some risk)
# < 0.60: Weak (high split risk)
```

## 📈 Integration with Your Testing Plan

### Phase 1: Baseline (Weeks 1-2)

```bash
# Deploy homogeneous network with Economic Nodes
warnet deploy networks/economic-30-nodes.yaml

# Establish baseline metrics
python scripts/analyze_baseline.py
```

### Phase 2: Version Mix (Weeks 3-4)

```bash
# Generate mixed version network
python scripts/economic_network_utils.py generate \
    --nodes 50 \
    --output networks/version-mix-50.yaml

# Edit to set different versions for 20% of nodes
# Deploy and test
```

### Phase 3: Soft Fork Testing (Weeks 7-8)

```bash
# Create network with 70% Economic Node adoption
# Test bounty claim scenarios
# Measure chain split risk
```

### Phase 4: Stress Testing (Weeks 9-10)

```bash
# Large network with extreme scenarios
python scripts/economic_network_utils.py generate \
    --nodes 500 \
    --economic-pct 0.12 \
    --output networks/stress-500.yaml
```

## 🎓 Understanding the BCAP Integration

Your testing plan now incorporates these key BCAP findings:

1. **Economic Nodes have peak power during activation** → Test at activation threshold
2. **40-week median upgrade time** → Include lagged upgrades in testing
3. **Bounty claim attacks are possible** → Test with accumulated soft-fork scripts
4. **60/40 Economic Node splits are dangerous** → Test partial adoption scenarios
5. **False signaling creates reorg risk** → Test miner signaling without enforcement

## 📞 Next Steps

1. **Review the full implementation guide**: `economic_nodes_warnet_implementation.md`
2. **Deploy the 30-node reference network**: Test basic functionality
3. **Generate your first custom network**: Use the utility script
4. **Integrate into your testing phases**: Follow the week-by-week plan
5. **Add monitoring**: Set up Prometheus metrics for Economic Nodes

## 💡 Pro Tips

1. **Start small**: Test with 30-node network before scaling to 100+
2. **Weight matters**: Economic Nodes should represent 60-80% of total weight
3. **Version diversity is realistic**: Mix versions like the real network
4. **Monitor consensus score continuously**: Don't just check at the end
5. **Test recovery**: After chain splits, measure how long to reconverge

## 📚 Files to Read

Priority order:
1. This guide (you're reading it!)
2. `README.md` - Complete examples and workflows
3. `economic_nodes_warnet_implementation.md` - Deep technical details
4. `networks/economic-30-nodes.yaml` - Example configuration

## ✅ Verification Checklist

After deploying your first Economic Node network:

- [ ] Economic Nodes represent 10-15% of total nodes
- [ ] Economic weight is 60-80% of total network weight
- [ ] Economic Nodes have higher connectivity than relay nodes
- [ ] Resource allocations are appropriate (4-8 cores, 8-32 GB RAM)
- [ ] Tags are properly set for identification in scenarios
- [ ] Network analyzer confirms correct distribution
- [ ] Can access Economic Nodes via Warnet CLI
- [ ] Monitoring captures Economic Node metrics

## 🐛 Common Issues

**Issue**: Economic Nodes won't start
- **Fix**: Check resource limits in your Kubernetes cluster

**Issue**: Can't distinguish Economic Nodes in tests
- **Fix**: Verify `tags` are set in YAML configuration

**Issue**: Consensus score always 1.0
- **Fix**: Ensure you're testing chain split scenarios

---

**Ready to start?** Deploy the 30-node network and run your first test!

```bash
warnet deploy networks/economic-30-nodes.yaml
warnet status
warnet dashboard
```

**Questions?** Refer to the comprehensive guide or Warnet documentation.
