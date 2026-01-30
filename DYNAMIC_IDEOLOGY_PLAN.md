# Plan: Dynamic Ideology for All Node Types

## Goal
Make ALL nodes (economic, user, pool) have ideology values and the ability to dynamically choose their fork. Currently only mining pools (100% of hashrate) switch forks, and `v27_economic_pct` is static. This causes rapid 100%/0% equilibrium. After this change, `v27_economic_pct` becomes dynamic -- driven by economic/user node decisions -- creating a realistic feedback loop.

## How Economic Weight Affects Token Valuation

The price oracle uses three factors to determine fork token prices:

```
price = base_price x (chain_factor x 0.3 + economic_factor x 0.5 + hashrate_factor x 0.2)
```

**Economic weight is the dominant factor at 50% of price determination.** When economic nodes switch forks, their aggregate weight shifts `v27_economic_pct`, which moves the token price more than hashrate changes do.

## Feedback Loop
```
Price Oracle (prices) --> Pool decisions (hashrate changes)
      ^                   Economic/User decisions (economic weight changes)
      |                         |
      +-------------------------+
```

---

## Files to Create

### 1. `warnet/resources/scenarios/lib/economic_node_strategy.py` (NEW)

Core new module, mirroring `mining_pool_strategy.py` structure:

- **`EconomicNodeProfile`** dataclass: `node_id`, `node_type` (ECONOMIC/USER), `fork_preference`, `ideology_strength`, `switching_threshold`, `custody_btc`, `daily_volume_btc`, `consensus_weight`, `switching_cooldown`, `max_loss_pct`, `inertia`
- **`EconomicDecision`** dataclass: records each node's decision with reasoning
- **`EconomicNodeStrategy`** class:
  - `make_decision(node_id, current_time, price_oracle)` -- decides fork based on: price advantage (rational) + ideology override + inertia (stay on current fork unless advantage exceeds threshold)
  - `calculate_economic_allocation(current_time, price_oracle)` -> `(v27_economic_pct, v26_economic_pct)` -- aggregates all node decisions weighted by `consensus_weight`
  - `print_allocation_summary()`, `export_to_json()`
- **`load_economic_nodes_from_network(node_metadata, config, scenario_name)`** -- merges network.yaml metadata (economic data) with config.yaml (ideology data) to build profiles

**Key differences from pool decisions:**
- No fee oracle needed (not mining, just choosing which economy to participate in)
- Higher inertia (switching costs) -- especially for economic nodes (exchanges)
- Consensus weight determines influence (major exchange >> user node by 5+ orders of magnitude)

**Anti-oscillation mechanisms:**
- Inertia + switching_threshold create a "dead zone" where small price changes don't trigger switches
- Cooldowns prevent rapid flip-flopping (30min economic, 60min user)
- Ideology makes some nodes "sticky" on their preferred fork
- Price oracle's existing `max_divergence=20%` caps the feedback loop

### 2. `warnet/resources/scenarios/config/economic_nodes_config.yaml` (NEW)

Defines ideology scenarios for economic/user nodes (parallel to `mining_pools_config.yaml`):

- **`realistic_current`**: Exchanges mostly rational (ideology_strength=0.1, inertia=0.15), users more ideological (ideology_strength=0.3, inertia=0.05). Per-role overrides: major_exchange (purely rational), payment_processor (slight v26 preference)
- **`ideological_split`**: Strong division -- 40%/40%/20% v27/v26/neutral among economic nodes; 50%/30%/20% among users. Uses `distribution_pattern` to assign ideologies by proportion
- **`purely_rational`**: All nodes purely profit-driven (baseline comparison)

Structure: `economic_defaults`, `user_defaults`, optional `overrides` by role, optional `distribution_pattern`

---

## Files to Modify

### 3. `warnet/resources/scenarios/partition_miner_with_pools.py`

**New imports:** `EconomicNodeStrategy`, `EconomicNodeProfile`, `load_economic_nodes_from_network`

**New instance vars in `set_test_params()`:**
- `self.economic_strategy = None`
- `self.current_v27_economic = 0.0` / `self.current_v26_economic = 0.0`

**New CLI args in `add_options()`:**
- `--economic-scenario` (default: `realistic_current`)
- `--economic-update-interval` (default: 300 seconds)

**In `run_test()` initialization** (after pool strategy init):
- Load `economic_nodes_config.yaml` via pkgutil
- Build `EconomicNodeProfile` list from network metadata + config
- Create `EconomicNodeStrategy` instance
- Calculate initial economic allocation (nodes start on their partition's fork)
- Fallback: if loading fails, use static `--v27-economic` value (backward compatible)

**In main loop** -- add economic update cycle:
```
Every 10s:   Mine block (unchanged)
Every 60s:   Update prices + fees (NOW uses self.current_v27_economic instead of self.options.v27_economic)
Every 300s:  Economic nodes re-evaluate fork choice (NEW)
Every 600s:  Mining pools re-evaluate fork choice (unchanged)
```

- Replace `self.options.v27_economic` with `self.current_v27_economic` in price_oracle and fee_oracle calls
- Log economic reallocation events when changes exceed 0.5%
- Export economic strategy results at end

### 4. `warnetScenarioDiscovery/networkGen/partition_network_generator.py`

Add ideology metadata fields to ALL node types in generated network.yaml:

- **Economic nodes**: Add `node_type: "economic"`, `entity_id`, `fork_preference: "neutral"`, `ideology_strength: 0.1`, `switching_threshold: 0.03`, `inertia: 0.15`
- **User/network nodes**: Add `entity_id`, `fork_preference: "neutral"`, `ideology_strength: random(0.1-0.7)`, `switching_threshold: random(0.05-0.15)`, `inertia: random(0.02-0.08)`
- **Pool nodes**: Add `fork_preference: "neutral"`, `ideology_strength: 0.3` (defaults; config overrides)

These are defaults -- the `economic_nodes_config.yaml` overrides them per-scenario.

### 5. `warnet/resources/scenarios/lib/__init__.py`

Add `economic_node_strategy` to exports.

### 6. `warnet/src/warnet/control.py`

Add `"lib/economic_node_strategy"` and `"config/economic_nodes_config"` to the zipapp filter function so the new files get bundled.

---

## Backward Compatibility

- If `economic_nodes_config.yaml` is missing or fails to load, falls back to static `--v27-economic` (exact current behavior)
- All new CLI args have defaults
- Existing `mining_pools_config.yaml` scenarios unchanged
- Existing network YAML files without ideology fields work (loader applies defaults)

---

## Verification

1. **Regenerate network**: Run `partition_network_generator.py` and verify new ideology fields in output YAML
2. **Unit test**: Run `economic_node_strategy.py` standalone (add `__main__` test block like in `mining_pool_strategy.py`)
3. **Integration test**: Run preflight test with new `--economic-scenario realistic_current` flag
4. **Verify dynamic behavior**: Check logs for "ECONOMIC REALLOCATION" messages showing `v27_economic_pct` changing over time
5. **Verify feedback loop**: Confirm that economic weight changes feed back into price changes (price should respond to both hashrate AND economic shifts)
6. **Verify no rapid oscillation**: Economic weight should shift gradually, not flip 100%/0%
7. **Verify backward compat**: Run without `--economic-scenario` flag and confirm static behavior still works
