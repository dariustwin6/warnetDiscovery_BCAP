# Economic Node Implementation for Warnet

This directory contains complete examples and utilities for implementing Economic Nodes in Warnet test networks, specifically designed for testing Bitcoin consensus scenarios outlined in the BCAP (Bitcoin Consensus Analysis Project).

## 📁 Directory Structure

```
warnet-economic-examples/
├── README.md                          # This file
├── networks/                          # Pre-configured network topologies
│   └── economic-30-nodes.yaml        # 30-node reference network
├── scenarios/                         # Test scenarios (to be added)
└── scripts/                          # Utility scripts
    └── economic_network_utils.py     # Network generator & analyzer
```

## 🎯 Quick Start

### 1. Generate a Network

Generate a 100-node network with 15% Economic Nodes:

```bash
python scripts/economic_network_utils.py generate \
    --nodes 100 \
    --economic-pct 0.15 \
    --output networks/my-network-100.yaml
```

### 2. Analyze a Network

Analyze the economic distribution and topology:

```bash
python scripts/economic_network_utils.py analyze \
    --config networks/economic-30-nodes.yaml
```

### 3. Deploy to Warnet

```bash
# Navigate to your Warnet project directory
cd /path/to/warnet/project

# Copy the network configuration
cp networks/economic-30-nodes.yaml ./networks/

# Deploy the network
warnet deploy ./networks/economic-30-nodes.yaml
```

## 📊 Understanding Economic Nodes

### What are Economic Nodes?

Economic Nodes represent high-impact Bitcoin network participants:
- **Exchanges** (Coinbase, Binance, Kraken)
- **Payment Processors** (BitPay, BTCPay Server operators)
- **Custody Providers** (Fidelity, institutional custodians)

### Why They Matter

According to BCAP research:
- Economic Nodes have **peak power during activation periods**
- They can **define which fork is "Bitcoin"** through market listings
- Their adoption rate is **critical for soft fork safety**
- **60-80% Economic Node adoption** is threshold for avoiding chain splits

### Configuration Characteristics

| Characteristic | Economic Node | Relay Node | Constrained Node |
|----------------|---------------|------------|------------------|
| **Weight** | 7-15x | 1x | 0.5x |
| **Connections** | 300-2000 | 125 | 8 |
| **Mempool** | 2-10 GB | 300 MB | 50 MB |
| **CPU** | 2-8 cores | 1 core | 0.25 cores |
| **Memory** | 8-32 GB | 2-4 GB | 512 MB - 1 GB |
| **Influence** | Very High | Medium | Low |

## 🧪 Pre-Configured Networks

### Economic-30-Nodes Network

**File**: `networks/economic-30-nodes.yaml`

**Composition**:
- 5 Economic Nodes (17%)
  - 2 Tier-1 Exchanges (weight: 15 each)
  - 1 Tier-2 Exchange (weight: 10)
  - 1 Payment Processor (weight: 8)
  - 1 Custody Provider (weight: 7)
- 20 Relay Nodes (66%)
  - Mixed versions: 27.0, 26.0, 25.0
- 5 Constrained Nodes (17%)
  - Older versions: 25.0, 24.0

**Total Economic Weight**: 65 (out of 92.5 total network weight)
**Economic Weight Percentage**: 70.3%

**Use Cases**:
- Baseline consensus testing
- Version compatibility testing
- Economic Node partial adoption scenarios

## 🛠️ Utility Script: economic_network_utils.py

### Generate Command

Create custom networks with specific parameters:

```bash
python scripts/economic_network_utils.py generate \
    --nodes <total_nodes> \
    --economic-pct <percentage> \
    --output <output_file.yaml>
```

**Parameters**:
- `--nodes`: Total number of nodes (default: 30)
- `--economic-pct`: Percentage of Economic Nodes (default: 0.15 = 15%)
- `--output`: Output YAML file path (required)

**Example**:
```bash
# Large network for stress testing
python scripts/economic_network_utils.py generate \
    --nodes 500 \
    --economic-pct 0.12 \
    --output networks/stress-test-500.yaml
```

### Analyze Command

Analyze network composition and calculate BCAP metrics:

```bash
python scripts/economic_network_utils.py analyze \
    --config <network_file.yaml>
```

**Output includes**:
- Network summary (node counts, percentages)
- Economic Node type distribution
- Bitcoin Core version distribution
- Resource allocation per node type
- Topology analysis (connectivity, hub nodes)
- BCAP economic metrics (consensus thresholds)

**Example Output**:
```
WARNET ECONOMIC NODE NETWORK ANALYSIS
================================================================================

### NETWORK SUMMARY ###
  total_nodes              : 30
  economic_nodes           : 5
  relay_nodes              : 20
  constrained_nodes        : 5
  economic_percentage      : 16.7%

### ECONOMIC METRICS (BCAP) ###
  total_network_weight                : 92.5
  economic_node_weight                : 65
  economic_weight_percentage          : 70.3%
  economic_version_uniformity         : 100.0%
  economic_consensus_threshold_60pct  : 39.0
  economic_consensus_threshold_80pct  : 52.0
```

## 📋 Testing Scenarios

### Scenario 1: Economic Node Partial Adoption

**Objective**: Test chain stability when Economic Nodes split 60/40 on soft fork adoption.

**Setup**:
1. Generate network with 100 nodes, 15% Economic
2. Deploy with Warnet
3. Run soft fork activation scenario
4. Measure:
   - Economic consensus score
   - Chain split probability
   - Transaction propagation

**Expected Criticality Score**: 40-60 (Medium-High Risk)

### Scenario 2: Bounty Claim Attack

**Objective**: Test BCAP bounty claim scenario with varying Economic Node adoption rates.

**Setup**:
1. Deploy network with 70% Economic Node adoption of soft fork
2. Build up 200 BTC in soft-fork-specific scripts
3. Inject high-fee bounty claim transaction
4. Measure:
   - Chain split occurrence
   - Economic Node response timing
   - Network recovery

**Expected Criticality Score**: 60-80 (High Risk if adoption < 80%)

### Scenario 3: False Miner Signaling

**Objective**: Detect miners signaling readiness without enforcing rules.

**Setup**:
1. Deploy network with mixed signaling
2. Some miners signal but don't enforce
3. Economic Nodes detect discrepancy
4. Measure:
   - False signaling rate
   - Reorg risk
   - Economic Node validation differences

**Expected Criticality Score**: 50-70 (High Risk if false signaling > 5%)

## 📈 Key Metrics to Monitor

### 1. Economic Consensus Score

```python
economic_consensus_score = max_weight_on_any_chain / total_economic_weight
```

**Interpretation**:
- `> 0.80`: Strong consensus, low split risk
- `0.60 - 0.80`: Moderate consensus, some risk
- `< 0.60`: Weak consensus, high split risk

### 2. Bounty Risk Score

```python
bounty_risk = (bounty_btc / 100) * (1 - economic_adoption_rate)
```

**Interpretation**:
- `< 0.20`: Low risk
- `0.20 - 0.50`: Medium risk
- `> 0.50`: High risk of bounty claim attack

### 3. False Signaling Rate

```python
false_signal_rate = blocks_signaling_but_not_enforcing / total_blocks_signaling
```

**Interpretation**:
- `< 0.05`: Acceptable (< 5%)
- `0.05 - 0.10`: Concerning (5-10%)
- `> 0.10`: Critical (> 10% - major reorg risk)

### 4. Economic Fragmentation

```python
fragmentation = 1 - (max_economic_weight / total_economic_weight)
```

**Interpretation**:
- `< 0.20`: Minimal fragmentation
- `0.20 - 0.40`: Moderate fragmentation
- `> 0.40`: Severe fragmentation (sustained split likely)

## 🔧 Integration with Warnet

### Deployment Steps

```bash
# 1. Generate or use pre-configured network
python scripts/economic_network_utils.py generate \
    --nodes 50 \
    --output my-test-network.yaml

# 2. Copy to Warnet project
cp my-test-network.yaml /path/to/warnet/project/networks/

# 3. Deploy
cd /path/to/warnet/project
warnet deploy networks/my-test-network.yaml

# 4. Verify deployment
warnet status

# 5. Run scenarios
warnet run scenarios/economic_consensus_test.py
```

### Accessing Nodes

```bash
# Access an Economic Node
warnet exec exchange-tier1-coinbase -- bitcoin-cli getblockchaininfo

# Access a relay node
warnet exec relay-node-5 -- bitcoin-cli getpeerinfo

# Monitor Economic Nodes specifically
warnet exec exchange-tier1-binance -- bitcoin-cli getmempoolinfo
```

### Monitoring

```bash
# View dashboard (includes Economic Node metrics if configured)
warnet dashboard

# Check logs for specific node
warnet logs exchange-tier1-coinbase

# Collect metrics
warnet metrics --node-type economic_node
```

## 🎓 Best Practices

### 1. Network Design

✅ **DO**:
- Keep Economic Nodes at 10-15% of total network
- Give Economic Nodes 5-15x weight multiplier
- Place Economic Nodes in hub positions (high connectivity)
- Mix Bitcoin Core versions realistically
- Use appropriate resource allocations

❌ **DON'T**:
- Make all nodes Economic Nodes (unrealistic)
- Give uniform weights (no differentiation)
- Under-resource Economic Nodes (causes artificial failures)
- Use only latest version (doesn't test compatibility)

### 2. Scenario Testing

✅ **DO**:
- Test partial Economic Node adoption (60/40, 70/30 splits)
- Simulate realistic upgrade timing (40-week lag)
- Include false signaling scenarios
- Test bounty accumulation at various levels
- Monitor economic consensus score continuously

❌ **DON'T**:
- Assume instant adoption
- Test only 100% or 0% adoption scenarios
- Ignore miner incentives
- Skip futures market simulation

### 3. Metrics Collection

✅ **DO**:
- Track Economic Node weight on each chain
- Measure adoption rate over time
- Calculate consensus scores at regular intervals
- Monitor transaction flow through Economic Nodes
- Record response timing by node type

❌ **DON'T**:
- Treat all nodes equally in analysis
- Ignore economic weight in calculations
- Only measure technical metrics
- Forget to track investor behavior simulation

## 📚 Related Resources

- **BCAP Paper**: https://github.com/bitcoin-cap/bcap
- **Warnet Documentation**: https://github.com/bitcoin-dev-project/warnet/tree/main/docs
- **Bitcoin Core**: https://github.com/bitcoin/bitcoin
- **SegWit Activation History**: https://bitcoinmagazine.com/technical/the-long-road-to-segwit

## 🤝 Contributing

To add new scenarios or configurations:

1. Create network configuration in `networks/`
2. Add corresponding scenario in `scenarios/`
3. Document expected outcomes and criticality thresholds
4. Test with at least 3 different network sizes

## 📝 Example Workflow

### End-to-End Testing Example

```bash
# 1. Generate 100-node network
python scripts/economic_network_utils.py generate \
    --nodes 100 \
    --economic-pct 0.15 \
    --output networks/test-100.yaml

# 2. Analyze before deployment
python scripts/economic_network_utils.py analyze \
    --config networks/test-100.yaml

# 3. Deploy to Warnet
warnet deploy networks/test-100.yaml

# 4. Wait for network to stabilize
sleep 60

# 5. Run economic consensus test
warnet run scenarios/economic_consensus.py

# 6. Collect results
warnet metrics --output results/test-100-results.json

# 7. Analyze criticality
python scripts/analyze_criticality.py results/test-100-results.json
```

## 🐛 Troubleshooting

### Issue: Economic Nodes not connecting

**Cause**: Resource limits too low or Kubernetes scheduling issues

**Solution**:
```bash
# Check node status
kubectl get pods -n warnet

# Increase resource limits in YAML
resources:
  limits:
    cpu: "8000m"  # Double the limit
    memory: "32Gi"
```

### Issue: Metrics not collecting for Economic Nodes

**Cause**: Tags not properly set or monitoring config missing

**Solution**:
```yaml
# Ensure tags are present
tags:
  - economic_node
  - exchange
```

### Issue: Network fragmentation too high in baseline

**Cause**: Too many Economic Nodes or improper weight distribution

**Solution**: Reduce Economic Node percentage to 10-12% or adjust weights

## 📞 Support

For questions or issues:
- Open an issue in the Warnet repository
- Refer to the BCAP paper for economic node behavior
- Check Warnet documentation for deployment issues

---

**Version**: 1.0  
**Last Updated**: November 2025  
**Compatibility**: Warnet 1.1.x, Bitcoin Core 24.0-27.0
