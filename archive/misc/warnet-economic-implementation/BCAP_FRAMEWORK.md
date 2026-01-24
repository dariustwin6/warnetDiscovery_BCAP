# BCAP Framework - Economic Node Implementation

## Executive Summary

This document explains the **BCAP (Bitcoin Consensus Activation Process)** framework alignment in our Warnet economic node implementation. The model has been refined to accurately reflect how economic nodes influence Bitcoin consensus based on custody and payment flows.

---

## Economic Node Definition (BCAP)

**Official Definition:**
> "Economic Nodes are full nodes that not only validate and relay transactions, but also receive and send substantial amounts of bitcoin payments. Economic Nodes have power and influence which is proportional to the frequency and volume of payments received."

### Why Economic Nodes Matter

Economic nodes are critical chokepoints in Bitcoin's economy:

1. **Supply Validation (Custody)**: They validate which chain holds the "real" BTC that users care about
   - If an exchange with 2M BTC chooses chain A over chain B, their users will follow
   - Custody = economic legitimacy

2. **Payment Flow Control (Operations)**: They control payment acceptance
   - If BitPay accepts only chain A, merchants using BitPay follow chain A
   - Payment processors = operational chokepoints

---

## Dual-Metric Model

### PRIMARY METRIC: Custody (Supply Validation)

**Definition**: Amount of BTC under validation by the economic node

**Measurement**:
- `custody_btc`: Total BTC in hot wallets + cold storage
- `supply_percentage`: Custody as % of circulating supply (19.5M BTC assumed)
- `consensus_weight`: Derived directly from supply_percentage

**Why Primary**: Custody represents **stored economic value** that users trust the node to validate. If Coinbase holds 10% of all BTC, their chain choice affects 10% of economic activity.

**Example**:
```yaml
custody_btc: 2000000  # 2M BTC
supply_percentage: 10.3  # (2M / 19.5M circulating)
consensus_weight: 10.3  # Direct mapping
```

### SECONDARY METRIC: Payment Flow (Daily)

**Definition**: Daily bitcoin payment volume (deposits + withdrawals)

**Measurement**:
- `daily_deposits_btc`: Incoming payments per day
- `daily_withdrawals_btc`: Outgoing payments per day
- `daily_volume_btc`: Total daily flow (max of deposits/withdrawals)

**Why Secondary**: Payment flow represents **operational importance**. High-volume payment processors like BitPay control merchant acceptance even with minimal custody.

**Example**:
```yaml
daily_deposits_btc: 100000
daily_withdrawals_btc: 95000
daily_volume_btc: 100000
```

### Weight Calculation

```
consensus_weight = supply_percentage + flow_adjustment

Where:
- supply_percentage dominates (PRIMARY)
- flow_adjustment adds marginal weight for operational chokepoints (SECONDARY)
```

**Current Implementation**: `consensus_weight ≈ supply_percentage`
- Major exchanges: 10-13% (high custody)
- Regional exchanges: 2-3% (medium custody)
- Payment processors: 0.5-1.5% (low custody, high flow → operational importance)
- Custody providers: 2-5% (high custody, low flow)

---

## Economic Node Categories

### 1. Major Exchange (Coinbase/Binance-scale)

**Profile**:
- Custody: 1.8M - 2.5M BTC (9-13% of supply)
- Daily volume: 80k - 120k BTC
- Consensus weight: 9-13
- Influence: **CRITICAL**

**Characteristics**:
- Largest custodians of BTC
- High-frequency retail + institutional trading
- Fast adoption speed (profit-driven)
- Hub topology (many connections)

**Configuration**:
```yaml
custody_btc: 2000000
supply_percentage: 10.3
daily_volume_btc: 100000
consensus_weight: 10.3
economic_influence: "critical"
```

**Bitcoin Config**:
- `maxmempool: 10000` (10GB)
- `maxconnections: 2000`
- `txindex: 1` (full transaction index)

---

### 2. Regional Exchange (Kraken/Gemini-scale)

**Profile**:
- Custody: 300k - 600k BTC (1.5-3% of supply)
- Daily volume: 20k - 40k BTC
- Consensus weight: 2-3
- Influence: **SIGNIFICANT**

**Characteristics**:
- Regional market focus
- Medium trading volume
- Medium adoption speed
- Moderate connectivity

**Configuration**:
```yaml
custody_btc: 450000
supply_percentage: 2.3
daily_volume_btc: 30000
consensus_weight: 2.3
economic_influence: "significant"
```

**Bitcoin Config**:
- `maxmempool: 5000` (5GB)
- `maxconnections: 1000`
- `txindex: 1`

---

### 3. Payment Processor (BitPay/Strike-scale)

**Profile**:
- Custody: 10k - 50k BTC (0.05-0.25% of supply)
- Daily volume: 5k - 15k BTC
- Consensus weight: 0.5-1.5
- Influence: **MODERATE**

**Characteristics**:
- **Operational chokepoint** (merchant payment acceptance)
- High-frequency transactions
- Minimal custody (hot wallets only)
- Medium adoption speed

**Configuration**:
```yaml
custody_btc: 30000
supply_percentage: 0.15
daily_volume_btc: 10000
consensus_weight: 1.0  # Boosted by operational importance
economic_influence: "moderate"
```

**Bitcoin Config**:
- `maxmempool: 2000` (2GB)
- `maxconnections: 500`
- `mempoolexpiry: 1` (1 hour - fast turnover)

**Note**: Despite low custody, payment processors have **disproportionate influence** because they control merchant acceptance.

---

### 4. Custody Provider (Fidelity Digital Assets-scale)

**Profile**:
- Custody: 400k - 1M BTC (2-5% of supply)
- Daily volume: 1k - 5k BTC
- Consensus weight: 2-5
- Influence: **SIGNIFICANT**

**Characteristics**:
- Institutional custody focus
- Cold storage dominant
- Low-frequency movements
- **Slow adoption speed** (conservative)

**Configuration**:
```yaml
custody_btc: 700000
supply_percentage: 3.6
daily_volume_btc: 3000
consensus_weight: 3.6
economic_influence: "significant"
```

**Bitcoin Config**:
- `maxmempool: 3000` (3GB)
- `maxconnections: 300`
- `discover: 0` (manual peering only - security)

**Note**: Custody providers are **conservative validators** - slow to change but hold significant supply.

---

### 5. Mining Pools (Reference Category)

**Profile**:
- Custody: 500 - 2k BTC (<0.01% of supply)
- Daily volume: 100 - 500 BTC
- Consensus weight: 0.01-0.05
- Influence: **MINOR (economically)**

**Note**: Mining pools have **hash power** (different consensus mechanism), but minimal **economic weight** in BCAP terms.

---

## Network Weight Distribution Example (30-node network)

### Economic Nodes (5 nodes, 28.6% consensus weight)

| Node | Category | Custody | % Supply | Daily Vol | Weight | Influence |
|------|----------|---------|----------|-----------|--------|-----------|
| Coinbase | Major Exchange | 2.0M | 10.3% | 100k | 10.3 | Critical |
| Binance | Major Exchange | 2.2M | 11.3% | 110k | 11.3 | Critical |
| Kraken | Regional Exchange | 450k | 2.3% | 30k | 2.3 | Significant |
| BitPay | Payment Processor | 30k | 0.15% | 10k | 1.0 | Moderate |
| Fidelity | Custody Provider | 700k | 3.6% | 3k | 3.6 | Significant |
| **TOTAL** | **5 nodes** | **5.38M** | **27.65%** | **253k** | **28.5** | - |

### Non-Economic Nodes (25 nodes)

- **20 Relay Nodes**: weight = 1 each = 20 total
- **5 Constrained Nodes**: weight = 0.5 each = 2.5 total

### Total Network Weight

- **Economic nodes**: 28.5 (55% of total weight, 17% of node count)
- **Non-economic nodes**: 22.5 (45% of total weight, 83% of node count)
- **Total**: 51.0

**Key Insight**: 5 economic nodes (17% of network) hold 55% of consensus weight through custody.

---

## Consensus Scenarios

### Scenario 1: Hard Fork (Chain Split)

**Setup**: Contentious hard fork creates Chain A vs Chain B

**Economic Node Decisions**:
- **Coinbase** (10.3%): Chooses Chain A → 10.3% of supply validates Chain A
- **Binance** (11.3%): Chooses Chain B → 11.3% of supply validates Chain B
- **Kraken** (2.3%): Chooses Chain A → adds to Chain A
- **BitPay** (1.0%): Chooses Chain A → **merchants follow Chain A**
- **Fidelity** (3.6%): Waits 6 months (conservative)

**Result**:
- Chain A: 10.3 + 2.3 + 1.0 = **13.6% economic weight** (+ BitPay operational importance)
- Chain B: 11.3 = **11.3% economic weight**
- Undecided: 3.6 (Fidelity waiting)

**Analysis**: Chain A has slight edge + payment processor support → likely winner

### Scenario 2: Mempool Policy Divergence

**Setup**: High fee environment, different mempool policies

**Economic Node Behavior**:
- **Coinbase** (10GB mempool): Accepts all transactions, includes low-fee txs
- **BitPay** (2GB mempool, 1hr expiry): Drops low-fee txs quickly
- **User Impact**: BitPay merchants see different tx set than Coinbase users

**Result**: Users fragment based on which economic node they use

---

## Testing Applications

### Test 1: Version Split Consensus

**Objective**: Measure consensus behavior when economic nodes run different versions

**Setup**:
```yaml
exchange-1 (weight 10.3): v26.0
exchange-2 (weight 11.3): v27.0
payment-processor (weight 1.0): v27.0
custody-provider (weight 3.6): v26.0
```

**Metrics**:
- Does a chain split occur?
- Which version wins?
- How long does resolution take?

### Test 2: Mempool Policy Impact

**Objective**: Measure how mempool size affects transaction propagation

**Setup**:
```yaml
exchange-1 (weight 10.3): maxmempool=50MB
exchange-2 (weight 11.3): maxmempool=10GB
```

**Metrics**:
- Do both nodes see the same transactions?
- How do fee spikes affect each node?
- Which node's mempool reflects "economic reality"?

### Test 3: Custody-Based Attack Resistance

**Objective**: Can high-custody nodes resist Sybil attacks?

**Setup**:
- 100 relay nodes (weight 1 each = 100 total)
- 5 economic nodes (weight 28.5 total)
- Simulate: 90/100 relay nodes are malicious

**Metrics**:
- Do economic nodes (28.5 weight) resist 90 Sybil nodes (90 weight)?
- Answer: NO - need additional mechanisms beyond custody weight

---

## Implementation Notes

### YAML Schema

```yaml
metadata:
  # PRIMARY METRIC: Custody
  custody_btc: 2000000
  supply_percentage: 10.3
  custody_notes: "Hot wallets + cold storage"

  # SECONDARY METRIC: Payment Flow
  daily_deposits_btc: 100000
  daily_withdrawals_btc: 95000
  daily_volume_btc: 100000
  payment_notes: "High-frequency retail + institutional"

  # DERIVED: Consensus Weight
  consensus_weight: 10.3
  weight_calculation: "custody_primary_flow_secondary"
  economic_influence: "critical"
```

### EconomicNode Class Usage

```python
from economic_network_utils import EconomicNode

# Use preset categories
node = EconomicNode(
    name="coinbase-1",
    node_type="major_exchange",
    version="27.0"
)

# Or override custody/volume
custom_node = EconomicNode(
    name="custom-exchange",
    node_type="major_exchange",
    version="26.0",
    custody_btc=1500000,  # Custom 1.5M BTC
    daily_volume_btc=80000
)

yaml_config = custom_node.to_dict()
```

---

## Comparison: Old vs New Model

### Old Model (Arbitrary Weights)

```yaml
metadata:
  weight: 15  # ❌ What does 15 mean?
  node_type: exchange
```

**Problems**:
- No grounding in economic reality
- Can't compare across scenarios
- Doesn't reflect BCAP framework

### New Model (BCAP-Aligned)

```yaml
metadata:
  custody_btc: 2000000  # ✅ 2M BTC in custody
  supply_percentage: 10.3  # ✅ 10.3% of circulating supply
  daily_volume_btc: 100000  # ✅ 100k BTC daily flow
  consensus_weight: 10.3  # ✅ Derived from custody
```

**Benefits**:
- Grounded in measurable economic data
- Comparable across networks
- Aligns with BCAP framework definition
- Enables realistic scenario testing

---

## Data Sources & Estimates

### Custody Estimates

**Sources**:
- Public exchange reserve data (Glassnode, CryptoQuant)
- Self-reported custody figures
- On-chain analysis of known addresses

**Assumptions**:
- Circulating supply: 19.5M BTC (as of 2024)
- Exchange reserves fluctuate ±20%
- Cold storage typically 90%+ of custody

### Payment Flow Estimates

**Sources**:
- Exchange API data (24h deposit/withdrawal volume)
- On-chain transaction clustering
- Payment processor public metrics

**Assumptions**:
- Daily volume = max(deposits, withdrawals)
- 95% withdrawal ratio for balanced exchanges
- Payment processors: high velocity, low custody

---

## Future Enhancements

### 1. Dynamic Weight Calculation

**Current**: Static weights based on category
**Future**: Real-time weight calculation based on actual custody/flow

```python
def calculate_dynamic_weight(custody_btc, daily_volume_btc):
    """Calculate consensus weight from custody + flow metrics."""
    supply_weight = (custody_btc / 19_500_000) * 100

    # Operational bonus for high-volume payment processors
    flow_bonus = 0
    if daily_volume_btc > 50000 and custody_btc < 100000:
        flow_bonus = 0.5  # Payment processor operational importance

    return supply_weight + flow_bonus
```

### 2. Time-Based Weight Evolution

Track how economic node influence changes over time:
- Exchange reserve growth/decline
- Adoption speed modeling (fast/medium/slow)
- Network effect amplification

### 3. Multi-Chain Scenarios

Model economic nodes operating across multiple chains:
- BTC mainnet + testnet
- Fork scenarios with persistent chains
- Cross-chain custody tracking

---

## References

1. **BCAP Framework**: Original Bitcoin Consensus Activation Process definition
2. **Warnet Documentation**: Economic node implementation guide
3. **Bitcoin Core**: bitcoin.conf parameters and mempool behavior
4. **Exchange Reserves**: Public custody data sources

---

## Glossary

- **Custody**: Total BTC held in hot + cold storage by economic node
- **Supply Validation**: Node's role in validating which chain holds legitimate BTC
- **Payment Flow**: Daily volume of incoming/outgoing BTC transactions
- **Operational Chokepoint**: Node that controls payment acceptance (e.g., payment processors)
- **Consensus Weight**: Numerical influence in BCAP consensus scenarios
- **Economic Influence**: Qualitative assessment (critical/significant/moderate/minor)

---

## Contact & Contributions

For questions, issues, or improvements to the BCAP framework implementation:
- **Issues**: `warnet-economic-implementation/` repository
- **Documentation**: This file (`BCAP_FRAMEWORK.md`)

---

**Last Updated**: 2024-11-26
**Version**: 1.0 (BCAP-aligned dual-metric model)
