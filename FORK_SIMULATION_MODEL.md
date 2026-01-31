# Fork Simulation Model Specification

This document describes the economic simulation model used in the Warnet fork testing system. The model tracks how token prices, node decisions, and fee markets evolve during a sustained Bitcoin protocol fork, with feedback loops between all three subsystems.

---

## Table of Contents

1. [Token Price Determination](#1-token-price-determination)
2. [Node Fork Decisions](#2-node-fork-decisions)
3. [Dynamic Fee Market](#3-dynamic-fee-market)
4. [Feedback Loops](#4-feedback-loops)
5. [Anti-Oscillation Mechanisms](#5-anti-oscillation-mechanisms)

---

## 1. Token Price Determination

**Source:** `warnet/resources/scenarios/lib/price_oracle.py`

At the moment of a sustained protocol fork, the single Bitcoin token conceptually splits into two tokens -- one for each fork (v27 and v26). The price oracle models how these tokens diverge from the pre-fork base price based on three fundamental inputs.

### 1.1 Prerequisites: Sustained Fork Detection

Prices remain at the base price (no divergence) until the fork is **sustained**. A fork is considered sustained when:

```
fork_depth = (v27_height + v26_height) - (2 x common_ancestor_height) >= 6
```

This prevents natural chain reorgs (which happen routinely) from triggering price divergence. Only after 6+ blocks have been mined across both chains does the model begin separate token valuation.

### 1.2 The Three Price Factors

Once the fork is sustained, each factor is computed and mapped to a **0.8 - 1.2 range** (a 20% swing band):

```
factor = 0.8 + (weight x 0.4)
```

Where `weight` is a 0-1 normalized input. A weight of 0.0 yields factor 0.8 (bearish), 0.5 yields 1.0 (neutral), and 1.0 yields 1.2 (bullish).

#### Factor 1: Chain Height (Block Production) -- 30% coefficient

```
chain_weight = chain_height / (v27_height + v26_height)
chain_factor = 0.8 + (chain_weight x 0.4)
```

**What it models:** A fork that produces blocks faster demonstrates viable mining support. Faster block production means the chain is functional, transactions confirm, and the network is usable. A chain that falls behind signals reduced security and usability, creating sell pressure on its token.

**Example:** If v27 is at height 120 and v26 at height 80 (total 200):
- v27 chain_weight = 120/200 = 0.60, chain_factor = 0.8 + (0.6 x 0.4) = **1.04**
- v26 chain_weight = 80/200 = 0.40, chain_factor = 0.8 + (0.4 x 0.4) = **0.96**

#### Factor 2: Economic Allocation (Custody + Volume) -- 50% coefficient

```
economic_weight = economic_pct / 100.0
economic_factor = 0.8 + (economic_weight x 0.4)
```

**What it models:** This is the **dominant** price factor. Economic allocation represents the aggregate "vote" of all non-mining nodes -- exchanges, payment processors, and users -- choosing which fork's economy to participate in. When exchanges list a fork's token and users transact on it, that creates real buying demand. When economic actors leave a fork, it creates selling pressure.

Economic weight is itself a dynamic value, computed from the weighted decisions of all economic and user nodes (see Section 2.2). Each node's influence on this percentage is proportional to its **consensus weight**, which is derived from:

```
consensus_weight = (0.7 x custody_btc + 0.3 x daily_volume_btc) / 10,000
```

Custody (70% of weight) represents the BTC held by the entity (exchange reserves, wallet balances). Volume (30% of weight) represents daily transaction flow. A major exchange with 1.5M BTC in custody and 150K daily volume has a consensus weight of ~111.7, while an individual user with 3.5 BTC and 0.5 daily volume has a weight of ~0.0003 -- roughly a 370,000:1 ratio reflecting the real-world economic influence disparity.

**Example:** If 80% of economic weight has chosen v27:
- v27 economic_factor = 0.8 + (0.8 x 0.4) = **1.12**
- v26 economic_factor = 0.8 + (0.2 x 0.4) = **0.88**

#### Factor 3: Hashrate Allocation -- 20% coefficient

```
hashrate_weight = hashrate_pct / 100.0
hashrate_factor = 0.8 + (hashrate_weight x 0.4)
```

**What it models:** Hashrate represents security. A fork with more hashrate is harder to attack (51% attack requires more resources), and block production is more reliable. However, hashrate follows price (miners chase profitability), so it is weighted at only 20% to avoid circular amplification. It acts more as a security premium/discount than a primary price driver.

**Example:** If v27 has 90% of hashrate:
- v27 hashrate_factor = 0.8 + (0.9 x 0.4) = **1.16**
- v26 hashrate_factor = 0.8 + (0.1 x 0.4) = **0.84**

### 1.3 Combined Price Formula

The three factors are combined using their coefficients:

```
combined_factor = (chain_factor x 0.30) + (economic_factor x 0.50) + (hashrate_factor x 0.20)

new_price = base_price x combined_factor
```

A hard constraint caps divergence:

```
min_price = base_price x (1 - max_divergence)     [default: -20%]
max_price = base_price x (1 + max_divergence)     [default: +20%]
new_price = clamp(new_price, min_price, max_price)
```

### 1.4 Complete Price Example

Given: base_price = $60,000, v27 has 60% of blocks, 80% of economic weight, 90% of hashrate:

| Factor | v27 Weight | v27 Factor | v26 Weight | v26 Factor |
|--------|-----------|------------|-----------|------------|
| Chain (30%) | 0.60 | 1.040 | 0.40 | 0.960 |
| Economic (50%) | 0.80 | 1.120 | 0.20 | 0.880 |
| Hashrate (20%) | 0.90 | 1.160 | 0.10 | 0.840 |

```
v27_combined = (1.040 x 0.30) + (1.120 x 0.50) + (1.160 x 0.20) = 0.312 + 0.560 + 0.232 = 1.104
v26_combined = (0.960 x 0.30) + (0.880 x 0.50) + (0.840 x 0.20) = 0.288 + 0.440 + 0.168 = 0.896

v27_price = $60,000 x 1.104 = $66,240
v26_price = $60,000 x 0.896 = $53,760
```

This produces a ~23% price divergence between the two tokens, though the 20% max divergence cap would clamp the v27 price to $72,000 and the v26 price floor to $48,000 in more extreme scenarios.

### 1.5 Coefficient Rationale

| Factor | Coefficient | Rationale |
|--------|------------|-----------|
| Chain Height | 0.30 | Important signal but partially redundant with hashrate |
| Economic Weight | **0.50** | Dominant factor -- exchange listings and user adoption create real buy/sell pressure |
| Hashrate | 0.20 | Security premium, but hashrate follows price (avoid circular amplification) |

---

## 2. Node Fork Decisions

Three types of nodes make independent fork decisions: mining pools, economic nodes, and user nodes. Each uses a different decision model reflecting their real-world motivations and constraints.

### 2.1 Mining Pool Decisions

**Source:** `warnet/resources/scenarios/lib/mining_pool_strategy.py`

Mining pools decide which fork to direct their hashrate toward. Their decisions directly determine the hashrate allocation that feeds into the price oracle.

#### Inputs

| Input | Source | Role |
|-------|--------|------|
| Token price per fork | Price Oracle | Revenue calculation |
| Fee rate per fork (sats/vB) | Fee Oracle | Revenue calculation |
| Block subsidy (BTC) | Protocol parameter (3.125) | Fixed revenue component |
| Mining cost (USD/block) | Configuration | Cost baseline |
| Fork preference | Pool profile | Ideological direction |
| Ideology strength (0-1) | Pool profile | Loss tolerance multiplier |
| Max loss (USD and %) | Pool profile | Hard limits on ideology |

#### Decision Pipeline

**Step 1: Calculate profitability on each fork**

```
fee_btc = (fee_rate_sats_per_vB x 1,000,000 vB) / 100,000,000
revenue_per_block = (block_subsidy + fee_btc) x price_usd
blocks_per_hour = 6.0 x (pool_hashrate_pct / 100.0)
profit_per_hour = (revenue_per_block x blocks_per_hour) - (mining_cost_usd x blocks_per_hour)
```

Note: Block subsidy is the fixed protocol reward (currently 3.125 BTC after 2024 halving). Fee revenue per block assumes a full 1 MB block. The pool's share of blocks is proportional to its hashrate percentage.

**Step 2: Rational choice** -- mine the more profitable fork.

```
profit_advantage = |profit_fork_A - profit_fork_B| / profit_lesser_fork
```

**Step 3: Ideology override** -- if the pool prefers a less profitable fork:

```
max_acceptable_loss_pct = ideology_strength x max_loss_pct
```

If `loss_pct <= max_acceptable_loss_pct`, ideology wins and the pool mines its preferred fork at a loss.

**Step 4: Forced switch** -- if cumulative opportunity cost exceeds `max_loss_usd` OR `loss_pct > max_acceptable_loss_pct`, the pool is forced to switch to the profitable fork regardless of ideology.

**Step 5: Cooldown** -- pools only re-evaluate every 10 minutes (default) to prevent rapid oscillation.

#### Example: Ideological Pool

A pool with `ideology_strength=0.5` and `max_loss_pct=0.20`:
- Will accept up to `0.5 x 0.20 = 10%` profitability loss to support its preferred fork
- At 12% loss, forced to switch to the profitable fork
- After switching, must wait 10 minutes before reconsidering

#### Hashrate Output

All pool decisions aggregate into `v27_hashrate_pct` and `v26_hashrate_pct`:

```
v27_hashrate = sum(pool.hashrate_pct for each pool mining v27)
v26_hashrate = sum(pool.hashrate_pct for each pool mining v26)
```

These percentages feed back into the price oracle (Section 1) and fee oracle (Section 3).

### 2.2 Economic Node Decisions

**Source:** `warnet/resources/scenarios/lib/economic_node_strategy.py`

Economic nodes represent exchanges, payment processors, and other high-value entities. They decide which fork's economy to participate in -- listing its token, processing its transactions, holding its reserves.

#### Inputs

| Input | Source | Role |
|-------|--------|------|
| Token price per fork | Price Oracle | Rational signal |
| Fork preference | Node profile / Config | Ideological direction |
| Ideology strength (0-1) | Config scenario | Loss tolerance multiplier |
| Switching threshold (0-1) | Config scenario | Minimum price advantage to consider |
| Inertia (0-1) | Config scenario | Resistance to change (infrastructure cost) |
| Max loss % (0-1) | Config scenario | Max acceptable price disadvantage |
| Current fork | Internal state | Inertia baseline |

#### Decision Pipeline

**Step 1: Rational choice** -- follow the higher-priced fork token.

```
price_advantage = |v27_price - v26_price| / price_of_lesser_fork
rational_choice = fork with higher price
```

**Step 2: Ideology override** -- if the node prefers the lower-priced fork:

```
max_acceptable_loss = ideology_strength x max_loss_pct
```

If `price_advantage <= max_acceptable_loss`, ideology wins.

**Step 3: Inertia check** -- even if the rational/ideology step says to switch, inertia may prevent it:

```
effective_threshold = switching_threshold + inertia
```

If `price_advantage < effective_threshold`, the node **stays on its current fork** regardless of the rational choice. This models the real cost of switching exchange infrastructure, updating APIs, migrating wallets, etc.

**Step 4: Cooldown** -- economic nodes re-evaluate every 30 minutes (default), user nodes every 60 minutes.

#### Key Difference from Miners

Economic nodes do **not** use the fee oracle. They don't earn block rewards. Instead, they care about which token is more valuable for their business operations. Their decision is simpler: higher price + ideology + inertia = fork choice.

#### Economic Weight Output

All economic node decisions aggregate into `v27_economic_pct` and `v26_economic_pct`:

```
v27_weight = sum(node.consensus_weight for each node choosing v27)
v26_weight = sum(node.consensus_weight for each node choosing v26)
v27_economic_pct = (v27_weight / total_weight) x 100
```

This is the dynamic value that feeds the 50%-weighted economic factor in the price oracle.

### 2.3 User Node Decisions

**Source:** `warnet/resources/scenarios/lib/economic_node_strategy.py` (same module, `NodeType.USER`)

User nodes use the same decision engine as economic nodes but with different default parameters reflecting individual behavior:

| Parameter | Economic Default | User Default | Rationale |
|-----------|-----------------|--------------|-----------|
| Ideology strength | 0.1 | 0.3 | Users are more ideological than businesses |
| Switching threshold | 0.03 (3%) | 0.08 (8%) | Users are slower to react to price signals |
| Inertia | 0.15 | 0.05 | Lower infrastructure switching costs |
| Switching cooldown | 1800s (30 min) | 3600s (1 hour) | Less frequent re-evaluation |
| Max loss % | 0.05 (5%) | 0.15 (15%) | Users tolerate more loss for beliefs |

User nodes have very low consensus weight (a few BTC of custody vs. millions for exchanges), so their individual decisions barely move the economic weight. Their influence is collective: thousands of users shifting can move the needle, but a single major exchange switching has far more impact.

### 2.4 Decision Summary by Node Type

| Aspect | Mining Pool | Economic Node | User Node |
|--------|------------|--------------|-----------|
| **Primary input** | USD profitability (price x fees) | Token price | Token price |
| **Secondary input** | Ideology | Ideology + Inertia | Ideology + Inertia |
| **Fee market influence** | Yes (revenue component) | No | No |
| **Chain height influence** | Indirect (via price) | Indirect (via price) | Indirect (via price) |
| **Output feeds into** | Hashrate allocation (20% of price) | Economic allocation (50% of price) | Economic allocation (50% of price) |
| **Re-evaluation interval** | 10 minutes | 30 minutes | 60 minutes |
| **Typical weight** | 5-28% of hashrate | 30-110 consensus weight | 0.0001-0.001 consensus weight |

---

## 3. Dynamic Fee Market

**Source:** `warnet/resources/scenarios/lib/fee_oracle.py`

The fee market models transaction costs on each fork. Fees affect miner profitability (and therefore hashrate allocation) and represent the cost of using each fork's network.

### 3.1 Organic Fee Calculation

Organic fees arise from natural transaction demand:

```
organic_fee = base_fee_rate x block_factor x activity_factor x mempool_pressure
```

Where:

#### Block Factor (Block Production Rate)

```
block_factor = 6.0 / blocks_per_hour
```

**What it models:** Slower block production means less block space per hour, creating congestion. If a fork has 10% of hashrate, it produces ~0.6 blocks/hour instead of 6, creating a 10x fee multiplier. This reflects real mempool dynamics: fewer blocks = longer confirmation times = users bid up fees to get included.

**Example:**
- Normal (6 blocks/hour): block_factor = 6.0/6.0 = **1.0x**
- 50% hashrate (3 blocks/hour): block_factor = 6.0/3.0 = **2.0x**
- 10% hashrate (0.6 blocks/hour): block_factor = 6.0/0.6 = **10.0x**

#### Activity Factor (Economic Activity Concentration)

```
activity_factor = economic_activity_pct / 50.0
```

**What it models:** A fork with more economic activity (users, exchanges, payment processors) has more transactions competing for block space. The 50% baseline represents an even split. If 80% of economic activity is on one fork, that fork sees 1.6x the transaction demand.

This is where **custody** and **volume** indirectly affect fees. Economic nodes with high custody and volume generate more transaction demand when they choose a fork. When a major exchange (150K BTC daily volume) moves to a fork, it brings significant transaction flow that increases organic fee pressure.

**Example:**
- 50% economic activity: activity_factor = 50/50 = **1.0x**
- 80% economic activity: activity_factor = 80/50 = **1.6x**
- 20% economic activity: activity_factor = 20/50 = **0.4x**

#### Combined Organic Fee

The base fee rate (default: 1.0 sat/vB) is multiplied by both factors:

**Example:** Fork with 10% hashrate and 20% economic activity:
```
organic_fee = 1.0 x (6.0/0.6) x (20/50) x 1.0 = 1.0 x 10.0 x 0.4 = 4.0 sat/vB
```

Despite low activity, the extreme block scarcity drives fees to 4x baseline.

**Example:** Fork with 90% hashrate and 80% economic activity:
```
organic_fee = 1.0 x (6.0/5.4) x (80/50) x 1.0 = 1.0 x 1.11 x 1.6 = 1.78 sat/vB
```

High activity is absorbed by plentiful block space, keeping fees modest.

### 3.2 Fee Manipulation (Propping Up an Undesired Fork)

An actor can spend BTC on artificial high-fee transactions to inflate a fork's fee market, making it appear more profitable to miners and potentially attracting hashrate to a weaker fork.

#### Manipulation Premium

```
sats_spent = artificial_fee_spending_btc x 100,000,000
premium_sats_per_vB = sats_spent / (blocks_mined x 1,000,000 vB_per_block)
total_fee = organic_fee + manipulation_premium
```

**What it models:** The manipulator creates transactions that pay above-market fees, raising the effective fee rate for miners. This is the mechanism for "propping up" an undesired fork -- making it artificially profitable to mine.

**Example:** Spending 1 BTC on artificial fees across 1 block:
```
sats_spent = 100,000,000
premium = 100,000,000 / (1 x 1,000,000) = 100 sat/vB
```

This is a massive premium that would make the fork very attractive to profit-seeking miners.

#### Cost to Incentivize Miners

To attract miners away from the dominant fork, the manipulation premium must make the weaker fork's **total revenue** competitive. The miner sees:

```
revenue_per_block = (block_subsidy + fee_btc) x token_price
```

Where fee_btc includes the manipulation premium:
```
fee_btc = (total_fee_sats_per_vB x 1,000,000) / 100,000,000
```

If the dominant fork's token trades at $66,000 and the weaker fork at $54,000, the manipulator must compensate for both the 18% price disadvantage AND the lost fee revenue. With block subsidy at 3.125 BTC:

```
Dominant fork revenue = (3.125 + 0.018) x $66,000 = $207,313/block
Weak fork organic revenue = (3.125 + 0.040) x $54,000 = $170,910/block
Gap per block = $36,403
Required extra fee_btc = $36,403 / $54,000 = 0.674 BTC/block
Required fee rate = 0.674 x 100,000,000 / 1,000,000 = 67.4 sat/vB premium
```

At 0.6 blocks/hour (10% hashrate), this costs ~0.674 BTC per block, or about 0.4 BTC/hour.

### 3.3 Dual-Token Portfolio Economics

At the moment of a fork, all BTC holders automatically possess equal amounts of both fork tokens. This is critical for analyzing manipulation sustainability.

#### Portfolio Value Tracking

```
initial_total_value = 2 x holdings_btc x pre_fork_price
current_total_value = (v27_holdings x v27_price) + (v26_holdings x v26_price)
```

The manipulator's BTC spent on artificial fees **reduces their holdings** on that fork:

```
v26_holdings_after = v26_holdings_before - artificial_fee_spending_btc
```

#### Sustainability Analysis

Manipulation is sustainable when portfolio appreciation exceeds costs:

```
portfolio_appreciation = current_total_value - initial_total_value
sustainability_ratio = portfolio_appreciation / cumulative_costs_usd
```

| Ratio | Status | Recommendation |
|-------|--------|----------------|
| > 1.0 | Sustainable | Continue -- portfolio value increasing despite costs |
| 0.5 - 1.0 | Warning | Approaching break-even |
| < 0.5 | Unsustainable | Abort -- destroying portfolio value |

**The paradox of propping up a losing fork:** If a manipulator spends BTC to inflate fees on the weaker fork, they deplete their holdings on that fork. Meanwhile, the dominant fork's token appreciates. The manipulator's total portfolio may still increase (they hold tokens on both forks), but the cost must be justified by the strategic outcome (e.g., preventing the dominant fork from achieving unchallenged consensus).

### 3.4 Miner Profitability Calculation

The fee oracle provides a full miner profitability view used by pool strategy decisions:

```
fee_btc = (fee_rate_sats_per_vB x 1,000,000) / 100,000,000
total_reward_btc = block_subsidy + fee_btc
revenue_usd = total_reward_btc x token_price
profit_usd = revenue_usd - mining_cost_per_block
profit_margin_pct = (profit_usd / mining_cost) x 100
```

This feeds directly into the mining pool decision engine (Section 2.1), closing the loop between fees and hashrate allocation.

---

## 4. Feedback Loops

The three subsystems form interconnected feedback loops:

```
                    ┌──────────────────────┐
                    │    PRICE ORACLE       │
                    │  (token valuation)    │
                    └──┬───────────────┬────┘
                       │               │
            prices     │               │    prices
                       ▼               ▼
              ┌────────────┐   ┌───────────────┐
              │   MINING   │   │   ECONOMIC /  │
              │   POOLS    │   │   USER NODES  │
              └────┬───────┘   └───────┬───────┘
                   │                   │
         hashrate  │                   │  economic
         allocation│                   │  allocation
                   ▼                   ▼
              ┌──────────────────────────────┐
              │       PRICE ORACLE           │
              │  hashrate (20%) + economic   │
              │  (50%) + chain height (30%)  │
              └──────────────────────────────┘
                       │
                       │ prices
                       ▼
              ┌────────────────┐
              │   FEE ORACLE   │
              │  (fee market)  │
              └───────┬────────┘
                      │
                      │ fees (profitability)
                      ▼
              ┌────────────────┐
              │  MINING POOLS  │
              │  (re-evaluate) │
              └────────────────┘
```

### Loop 1: Price -> Miners -> Hashrate -> Price
Price divergence makes one fork more profitable. Miners shift hashrate. Hashrate shift affects price (20% weight). Dampened by: cooldowns, ideology, and the relatively low 20% coefficient.

### Loop 2: Price -> Economic Nodes -> Economic Weight -> Price
Price divergence signals which fork is "winning." Economic nodes shift their participation. Economic weight changes are the **strongest** price driver (50% weight). Dampened by: inertia, switching thresholds, cooldowns, and ideology.

### Loop 3: Economic Weight -> Fees -> Miner Profitability -> Hashrate -> Price
When economic activity concentrates on one fork, organic fees increase (more transactions). Higher fees make that fork more profitable for miners. Miners shift hashrate. Hashrate shift reinforces the price signal. This is the indirect but powerful pathway by which custody and volume affect mining decisions.

### Loop 4: Fee Manipulation -> Miner Incentives -> Hashrate -> Price
An actor spends BTC to inflate fees on a losing fork, attracting miners. More hashrate improves the fork's price (modestly, 20% weight) and block production (30% weight). If successful, the price improvement attracts economic nodes (50% weight), potentially turning the tide. If unsuccessful, the manipulator depletes their portfolio unsustainably.

---

## 5. Anti-Oscillation Mechanisms

Without damping, feedback loops could cause rapid, unrealistic oscillation. The model includes several mechanisms to prevent this:

| Mechanism | Where Applied | Effect |
|-----------|--------------|--------|
| **Cooldown timers** | All node types | Pools: 10 min, Economic: 30 min, Users: 60 min between re-evaluations |
| **Inertia** | Economic/User nodes | Must exceed `switching_threshold + inertia` to switch (e.g., 18% for exchanges) |
| **Ideology** | All node types | Some fraction of nodes never switch regardless of price signals |
| **Max divergence cap** | Price Oracle | Prices clamped to ±20% of base price |
| **Factor normalization** | Price Oracle | Each factor mapped to 0.8-1.2 range (max 20% swing per factor) |
| **Coefficient weighting** | Price Oracle | No single factor dominates completely (max is economic at 50%) |
| **Consensus weight disparity** | Economic Node Strategy | A few large exchanges provide stability; thousands of users provide noise absorption |
| **Min fork depth** | Price Oracle | Prices don't diverge until fork is 6+ blocks deep |

The result is a system where equilibrium shifts gradually over time, with node decisions responding to price changes at different rates and with different thresholds, rather than all actors switching simultaneously.

---

## Appendix: Default Configuration Values

### Price Oracle Defaults
| Parameter | Default | Description |
|-----------|---------|-------------|
| base_price | $60,000 | Pre-fork BTC price |
| max_divergence | 0.20 (20%) | Maximum price deviation |
| chain_weight_coef | 0.30 | Block production importance |
| economic_weight_coef | 0.50 | Economic activity importance |
| hashrate_weight_coef | 0.20 | Security premium importance |
| min_fork_depth | 6 blocks | Sustained fork threshold |

### Fee Oracle Defaults
| Parameter | Default | Description |
|-----------|---------|-------------|
| base_fee_rate | 1.0 sat/vB | Normal fee rate |
| vbytes_per_block | 1,000,000 | Full block size |
| block_subsidy | 3.125 BTC | Post-2024 halving |

### Mining Pool Decision Defaults
| Parameter | Default | Description |
|-----------|---------|-------------|
| decision_interval | 600s (10 min) | Re-evaluation cooldown |
| profitability_threshold | 0.05 (5%) | Min advantage to switch |
| max_loss_pct | 0.10 (10%) | Max revenue sacrifice |

### Economic Node Decision Defaults (realistic_current scenario)
| Parameter | Economic | User | Description |
|-----------|----------|------|-------------|
| ideology_strength | 0.10 | 0.30 | How much loss they'll accept for beliefs |
| switching_threshold | 0.03 | 0.08 | Min price advantage to consider switching |
| inertia | 0.15 | 0.05 | Resistance to switching (infrastructure cost) |
| switching_cooldown | 1800s | 3600s | Time between re-evaluations |
| max_loss_pct | 0.05 | 0.15 | Max acceptable price disadvantage |

### Simulation Update Intervals
| System | Default Interval | Description |
|--------|-----------------|-------------|
| Block mining | 10 seconds | New block on one fork |
| Price + Fee update | 60 seconds | Recalculate prices and fees |
| Economic node re-evaluation | 300 seconds (5 min) | Nodes reconsider fork choice |
| Mining pool re-evaluation | 600 seconds (10 min) | Pools reconsider fork choice |
