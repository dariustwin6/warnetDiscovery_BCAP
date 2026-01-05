# CLAUDE CODE INTEGRATION PROMPT
## Integrate Entity-Based Framework with Existing Warnet Project

---

## CONTEXT

I have built a **multi-dimensional entity-based critical scenario discovery framework** for Bitcoin network fork analysis. This framework needs to be integrated with my existing Warnet testing infrastructure.

**Existing Project Location:**
- Base: `~/bitcoinTools/warnet/`
- Scenarios: `~/bitcoinTools/warnet/test-networks/`
- Discovery code: `~/bitcoinTools/warnet/warnetScenarioDiscovery/`
- Monitoring: `~/bitcoinTools/warnet/warnetScenarioDiscovery/monitoring/`
- Tools: `~/bitcoinTools/warnet/warnetScenarioDiscovery/tools/`

**New Framework Location:**
- `~bitcoinTools/warnet/warnet_entity_distribution/`
- Contains: 4 Python modules + entity database + README

**Existing Components:**
- `partition_network_generator.py` - Creates network.yaml with v27/v26 partitions
- `partition_miner.py` - Manages mining on partitions
- `auto_economic_analysis.py` - BCAP economic analysis
- `analyze_all_scenarios.py` - Batch analysis
- Test scenarios in `test-networks/` (e.g., `test-2.15-E45-H45-dynamic/`)

---

## OBJECTIVE

Integrate the new entity-based framework with the existing Warnet infrastructure to enable:

1. **Generate network configurations** from entity allocations (not just percentages)
2. **Create Warnet-compatible network.yaml** files from entity configs
3. **Run Phase 1 coarse search** (50 diverse entity-based scenarios)
4. **Collect and analyze results** with criticality scoring
5. **Generate Phase 3 convergence tests** around critical regions

---

## INTEGRATION TASKS

### TASK 1: check Framework

**Expected Output:**
- `entity_database.py`
- `configuration_generator.py`
- `criticality_scorer.py`
- `scenario_discovery_orchestrator.py`
- `entity_database.json`
- `README.md`

---

### TASK 2: Create Network Generator Bridge

**Create:** `~/bitcoinTools/warnet/warnetScenarioDiscovery/warnet_entity_distribution/warnet_network_builder.py`

**Purpose:** Convert entity-based configurations to Warnet network.yaml files

**Requirements:**

```python
#!/usr/bin/env python3
"""
Warnet Network Builder - Converts entity configs to network.yaml
Bridges entity_framework with existing partition_network_generator.py
"""

from pathlib import Path
from configuration_generator import NetworkConfiguration, ForkPartition
from entity_database import Exchange, MiningPool, User
import yaml

class WarnetNetworkBuilder:
    """
    Builds Warnet-compatible network.yaml from entity allocations
    """
    
    def __init__(self, base_networks_dir: str = "~/bitcoinTools/warnet/test-networks"):
        self.base_networks_dir = Path(base_networks_dir).expanduser()
    
    def build_network_from_entity_config(
        self, 
        config: NetworkConfiguration,
        output_dir: str = None
    ) -> Path:
        """
        Generate network.yaml from entity configuration
        
        Args:
            config: NetworkConfiguration with entity allocations
            output_dir: Where to save network directory
        
        Returns:
            Path to generated network directory
        
        Process:
        1. Create directory: test-networks/{config_id}/
        2. Generate network.yaml with nodes for each entity
        3. Assign entities to v27 vs v26 based on fork allocation
        4. Set custody/volume per node based on entity values
        5. Set mining hashrate per pool
        6. Generate node-defaults.yaml
        """
        
        # Create output directory
        if output_dir is None:
            output_dir = self.base_networks_dir / config.config_id
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Build network structure
        network_data = self._build_network_yaml(config)
        
        # Save network.yaml
        network_file = output_dir / 'network.yaml'
        with open(network_file, 'w') as f:
            yaml.dump(network_data, f, default_flow_style=False)
        
        # Generate node-defaults.yaml
        defaults_data = self._build_node_defaults()
        defaults_file = output_dir / 'node-defaults.yaml'
        with open(defaults_file, 'w') as f:
            yaml.dump(defaults_data, f, default_flow_style=False)
        
        print(f"✓ Generated network: {output_dir}")
        
        return output_dir
    
    def _build_network_yaml(self, config: NetworkConfiguration) -> dict:
        """
        Build network.yaml structure from entity config
        
        Format should match existing test-networks/ scenarios
        """
        
        nodes = []
        node_counter = 0
        
        # === FORK A (v27) NODES ===
        
        # Exchanges on Fork A
        for exchange in config.fork_a.exchanges:
            nodes.append({
                'name': f'node-{node_counter:04d}',
                'version': 'v27.0',
                'role': 'exchange',
                'metadata': {
                    'custody_btc': exchange.custody_btc,
                    'daily_volume_btc': exchange.daily_volume_btc,
                    'entity_id': exchange.id,
                    'entity_name': exchange.name
                },
                'bitcoin_config': {
                    'maxconnections': 125
                }
            })
            node_counter += 1
        
        # Mining pools on Fork A
        for pool in config.fork_a.mining_pools:
            nodes.append({
                'name': f'node-{node_counter:04d}',
                'version': 'v27.0',
                'role': 'mining_pool',
                'metadata': {
                    'hashrate_pct': pool.hashrate_pct,
                    'entity_id': pool.id,
                    'entity_name': pool.name
                },
                'bitcoin_config': {
                    'maxconnections': 125
                }
            })
            node_counter += 1
        
        # Users on Fork A (sample - don't create 1000 individual nodes!)
        # Instead: Create representative user nodes
        if len(config.fork_a.users) > 0:
            # Top 10 users
            for user in config.fork_a.users[:10]:
                nodes.append({
                    'name': f'node-{node_counter:04d}',
                    'version': 'v27.0',
                    'role': 'user_node',
                    'metadata': {
                        'custody_btc': user.custody_btc,
                        'daily_volume_btc': user.daily_volume_btc,
                        'user_type': user.user_type,
                        'entity_id': user.id
                    }
                })
                node_counter += 1
            
            # Aggregate remaining users into single node
            if len(config.fork_a.users) > 10:
                remaining_users = config.fork_a.users[10:]
                total_custody = sum(u.custody_btc for u in remaining_users)
                total_volume = sum(u.daily_volume_btc for u in remaining_users)
                
                nodes.append({
                    'name': f'node-{node_counter:04d}',
                    'version': 'v27.0',
                    'role': 'user_node',
                    'metadata': {
                        'custody_btc': total_custody,
                        'daily_volume_btc': total_volume,
                        'user_type': 'aggregated',
                        'represents': len(remaining_users)
                    }
                })
                node_counter += 1
        
        # === FORK B (v26) NODES ===
        # Same process for Fork B
        
        # Exchanges on Fork B
        for exchange in config.fork_b.exchanges:
            nodes.append({
                'name': f'node-{node_counter:04d}',
                'version': 'v22.0',  # Use v22 for v26 partition
                'role': 'exchange',
                'metadata': {
                    'custody_btc': exchange.custody_btc,
                    'daily_volume_btc': exchange.daily_volume_btc,
                    'entity_id': exchange.id,
                    'entity_name': exchange.name
                }
            })
            node_counter += 1
        
        # Mining pools on Fork B
        for pool in config.fork_b.mining_pools:
            nodes.append({
                'name': f'node-{node_counter:04d}',
                'version': 'v22.0',
                'role': 'mining_pool',
                'metadata': {
                    'hashrate_pct': pool.hashrate_pct,
                    'entity_id': pool.id,
                    'entity_name': pool.name
                }
            })
            node_counter += 1
        
        # Users on Fork B
        if len(config.fork_b.users) > 0:
            for user in config.fork_b.users[:10]:
                nodes.append({
                    'name': f'node-{node_counter:04d}',
                    'version': 'v22.0',
                    'role': 'user_node',
                    'metadata': {
                        'custody_btc': user.custody_btc,
                        'daily_volume_btc': user.daily_volume_btc,
                        'user_type': user.user_type,
                        'entity_id': user.id
                    }
                })
                node_counter += 1
            
            if len(config.fork_b.users) > 10:
                remaining_users = config.fork_b.users[10:]
                total_custody = sum(u.custody_btc for u in remaining_users)
                total_volume = sum(u.daily_volume_btc for u in remaining_users)
                
                nodes.append({
                    'name': f'node-{node_counter:04d}',
                    'version': 'v22.0',
                    'role': 'user_node',
                    'metadata': {
                        'custody_btc': total_custody,
                        'daily_volume_btc': total_volume,
                        'user_type': 'aggregated',
                        'represents': len(remaining_users)
                    }
                })
                node_counter += 1
        
        return {'nodes': nodes}
    
    def _build_node_defaults(self) -> dict:
        """Standard node-defaults.yaml"""
        return {
            'bitcoin_config': {
                'regtest': 1,
                'dnsseed': 0,
                'txindex': 1,
                'fallbackfee': '0.00001'
            }
        }

# Example usage
if __name__ == "__main__":
    from entity_database import EntityDatabase
    from configuration_generator import ConfigurationGenerator
    
    # Load database
    db = EntityDatabase.load('entity_database.json')
    
    # Generate a test config
    gen = ConfigurationGenerator(db)
    config = gen.generate_specific_config(
        config_id='test-entity-perfect-split',
        exchange_allocation=[0],
        miner_allocation=[0, 1],
        user_allocation_pct=0
    )
    
    # Build network
    builder = WarnetNetworkBuilder()
    network_dir = builder.build_network_from_entity_config(config)
    
    print(f"\n✓ Network ready at: {network_dir}")
```

**Key Points:**
- Creates network.yaml compatible with existing test-networks/ format
- Each entity becomes a node with metadata (custody, volume, hashrate)
- Aggregates 1000 users into ~10-20 representative nodes (to keep network manageable)
- Assigns v27.0 to fork_a, v22.0 to fork_b (for version difference)

---

### TASK 3: Create Test Runner

**Create:** `~/bitcoinTools/warnet/warnetScenarioDiscovery/warnet_entity_distribution/entity_test_runner.py`

**Purpose:** Run entity-based tests using existing Warnet tools

**Requirements:**

```python
#!/usr/bin/env python3
"""
Entity Test Runner - Executes entity-based scenarios using Warnet
"""

import subprocess
import json
import time
from pathlib import Path
from datetime import datetime

class EntityTestRunner:
    """
    Runs entity-based tests using existing Warnet infrastructure
    """
    
    def __init__(
        self, 
        warnet_dir: str = "~/bitcoinTools/warnet",
        tools_dir: str = "~/bitcoinTools/warnet/warnetScenarioDiscovery/tools",
        monitoring_dir: str = "~/bitcoinTools/warnet/warnetScenarioDiscovery/monitoring"
    ):
        self.warnet_dir = Path(warnet_dir).expanduser()
        self.tools_dir = Path(tools_dir).expanduser()
        self.monitoring_dir = Path(monitoring_dir).expanduser()
    
    def run_test(
        self, 
        network_dir: Path,
        test_duration_minutes: int = 30,
        output_dir: Path = None
    ) -> dict:
        """
        Run a single entity-based test
        
        Process:
        1. Deploy network (warnet deploy)
        2. Start mining on partitions (partition_miner.py)
        3. Monitor fork progression (continuous_mining_test.sh)
        4. Run economic analysis (auto_economic_analysis.py)
        5. Collect results
        6. Cleanup (warnet down)
        
        Returns:
            Test outcome data (blocks, weights, risk score, etc.)
        """
        
        if output_dir is None:
            output_dir = network_dir / 'results'
        output_dir.mkdir(exist_ok=True)
        
        test_start = datetime.now()
        
        print(f"\n{'='*80}")
        print(f"Running test: {network_dir.name}")
        print(f"Duration: {test_duration_minutes} minutes")
        print(f"{'='*80}\n")
        
        try:
            # 1. Deploy network
            print("1. Deploying network...")
            self._deploy_network(network_dir)
            
            # 2. Start partition mining
            print("2. Starting partition mining...")
            self._start_partition_mining()
            
            # 3. Monitor fork progression
            print(f"3. Monitoring fork for {test_duration_minutes} minutes...")
            timeline_file = self._monitor_fork(
                duration_seconds=test_duration_minutes * 60,
                output_dir=output_dir
            )
            
            # 4. Run economic analysis
            print("4. Running economic analysis...")
            analysis_file = self._run_economic_analysis(
                network_dir=network_dir,
                output_dir=output_dir
            )
            
            # 5. Collect results
            print("5. Collecting results...")
            outcome = self._parse_results(
                timeline_file=timeline_file,
                analysis_file=analysis_file,
                network_dir=network_dir
            )
            
            # Save outcome
            outcome_file = output_dir / 'test_outcome.json'
            with open(outcome_file, 'w') as f:
                json.dump(outcome, f, indent=2)
            
            print(f"\n✓ Test complete! Results saved to {output_dir}")
            
            return outcome
            
        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            raise
        
        finally:
            # Cleanup
            print("\n6. Cleaning up...")
            self._cleanup()
    
    def _deploy_network(self, network_dir: Path):
        """Deploy network using warnet"""
        cmd = ['warnet', 'deploy', str(network_dir)]
        subprocess.run(cmd, cwd=self.warnet_dir, check=True)
        time.sleep(30)  # Wait for network to stabilize
    
    def _start_partition_mining(self):
        """Start mining on both partitions"""
        # Use existing partition_miner.py
        cmd = ['python3', 'partition_miner.py', '--start']
        subprocess.run(cmd, cwd=self.tools_dir, check=True)
    
    def _monitor_fork(self, duration_seconds: int, output_dir: Path) -> Path:
        """Monitor fork progression"""
        # Use existing continuous_mining_test.sh
        timeline_file = output_dir / 'timeline.csv'
        
        cmd = [
            'bash', 'continuous_mining_test.sh',
            '--interval', '30',
            '--duration', str(duration_seconds),
            '--output', str(timeline_file)
        ]
        
        subprocess.run(cmd, cwd=self.tools_dir, check=True)
        
        return timeline_file
    
    def _run_economic_analysis(self, network_dir: Path, output_dir: Path) -> Path:
        """Run BCAP economic analysis"""
        analysis_file = output_dir / 'economic_analysis.txt'
        
        cmd = [
            'python3', 'auto_economic_analysis.py',
            '--network-config', str(network_dir),
            '--output', str(analysis_file)
        ]
        
        subprocess.run(cmd, cwd=self.monitoring_dir, check=True)
        
        return analysis_file
    
    def _parse_results(
        self, 
        timeline_file: Path, 
        analysis_file: Path,
        network_dir: Path
    ) -> dict:
        """
        Parse timeline and analysis files into test outcome
        
        Should match TestOutcome format from criticality_scorer.py
        """
        
        # Parse timeline
        import pandas as pd
        timeline = pd.read_csv(timeline_file)
        last_row = timeline.iloc[-1]
        
        fork_a_blocks = int(last_row['v27_height'])
        fork_b_blocks = int(last_row['v22_height'])
        
        # Parse economic analysis
        import re
        with open(analysis_file, 'r') as f:
            analysis_text = f.read()
        
        # Extract risk score
        risk_match = re.search(r'Risk Score:\s+(\d+\.?\d*)/100', analysis_text)
        risk_score = float(risk_match.group(1)) if risk_match else 50.0
        
        # Extract risk level
        risk_level_match = re.search(r'Risk Level:\s+(\w+)', analysis_text)
        risk_level = risk_level_match.group(1) if risk_level_match else 'UNKNOWN'
        
        # Extract weights
        weight_a_match = re.search(r'### CHAIN A ###.*?Consensus Weight:\s+([\d,]+\.?\d*)', 
                                   analysis_text, re.DOTALL)
        weight_b_match = re.search(r'### CHAIN B ###.*?Consensus Weight:\s+([\d,]+\.?\d*)', 
                                   analysis_text, re.DOTALL)
        
        fork_a_weight = float(weight_a_match.group(1).replace(',', '')) if weight_a_match else 0
        fork_b_weight = float(weight_b_match.group(1).replace(',', '')) if weight_b_match else 0
        
        # Determine winners
        protocol_winner = 'fork_a' if fork_a_blocks > fork_b_blocks else 'fork_b'
        economic_winner = 'fork_a' if fork_a_weight > fork_b_weight else 'fork_b'
        
        return {
            'config_id': network_dir.name,
            'fork_a_blocks': fork_a_blocks,
            'fork_b_blocks': fork_b_blocks,
            'fork_a_weight': fork_a_weight,
            'fork_b_weight': fork_b_weight,
            'weight_ratio': fork_a_weight / fork_b_weight if fork_b_weight > 0 else float('inf'),
            'risk_score': risk_score,
            'risk_level': risk_level,
            'converged': abs(fork_a_blocks - fork_b_blocks) < 10,  # Simple heuristic
            'resolution_time_minutes': timeline.shape[0] * 0.5,  # Assuming 30s intervals
            'economic_winner': economic_winner,
            'protocol_winner': protocol_winner
        }
    
    def _cleanup(self):
        """Stop network"""
        cmd = ['warnet', 'down']
        subprocess.run(cmd, cwd=self.warnet_dir)
        time.sleep(10)

# Example usage
if __name__ == "__main__":
    runner = EntityTestRunner()
    
    # Test a network
    network_dir = Path("~/bitcoinTools/warnet/test-networks/test-entity-perfect-split").expanduser()
    
    if network_dir.exists():
        outcome = runner.run_test(network_dir, test_duration_minutes=1)
        print("\nTest Outcome:")
        print(json.dumps(outcome, indent=2))
    else:
        print(f"Network not found: {network_dir}")
```

---

### TASK 4: Create Phase 1 Batch Runner

**Create:** `~/bitcoinTools/warnet/warnetScenarioDiscovery/warnet_entity_distribution/run_phase1_batch.py`

**Purpose:** Run all 50 Phase 1 tests automatically

```python
#!/usr/bin/env python3
"""
Phase 1 Batch Runner - Runs all coarse search tests
"""

import json
from pathlib import Path
from entity_database import EntityDatabase
from scenario_discovery_orchestrator import ScenarioDiscoveryOrchestrator
from warnet_network_builder import WarnetNetworkBuilder
from entity_test_runner import EntityTestRunner

def run_phase1_batch(n_samples: int = 50):
    """
    Complete Phase 1 pipeline:
    1. Generate test specs
    2. Build networks
    3. Run tests
    4. Collect results
    5. Analyze for critical regions
    """
    
    print("="*80)
    print("PHASE 1: COARSE SEARCH - BATCH EXECUTION")
    print("="*80)
    
    # Load database
    db = EntityDatabase.load('entity_database.json')
    
    # Initialize components
    orchestrator = ScenarioDiscoveryOrchestrator(db, output_dir='./phase1_results')
    builder = WarnetNetworkBuilder()
    runner = EntityTestRunner()
    
    # Step 1: Generate test specifications
    print("\n### STEP 1: Generating test specifications ###")
    specs = orchestrator.run_phase1_coarse_search(n_samples=n_samples)
    
    # Step 2: Build networks for each spec
    print("\n### STEP 2: Building Warnet networks ###")
    from configuration_generator import ConfigurationGenerator
    generator = ConfigurationGenerator(db)
    
    networks_built = []
    for i, spec in enumerate(specs, 1):
        print(f"\n[{i}/{len(specs)}] Building: {spec['config_id']}")
        
        # Recreate config from spec
        # (Simplified - in practice, would save/load configs)
        config = generator.generate_random_config(spec['config_id'])
        
        # Build network
        network_dir = builder.build_network_from_entity_config(config)
        networks_built.append(network_dir)
    
    # Step 3: Run all tests
    print("\n### STEP 3: Running tests ###")
    all_outcomes = []
    
    for i, network_dir in enumerate(networks_built, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}/{len(networks_built)}")
        print(f"{'='*80}")
        
        try:
            outcome = runner.run_test(
                network_dir=network_dir,
                test_duration_minutes=30
            )
            
            all_outcomes.append(outcome)
            
        except Exception as e:
            print(f"✗ Test {i} failed: {e}")
            # Continue with next test
    
    # Step 4: Save all results
    print("\n### STEP 4: Saving results ###")
    results_file = Path('./phase1_results/all_test_outcomes.json')
    with open(results_file, 'w') as f:
        json.dump(all_outcomes, f, indent=2)
    
    print(f"✓ Saved {len(all_outcomes)} test outcomes to {results_file}")
    
    # Step 5: Analyze results
    print("\n### STEP 5: Analyzing results ###")
    critical_regions = orchestrator.analyze_phase1_results(str(results_file))
    
    print("\n" + "="*80)
    print("✓ PHASE 1 COMPLETE!")
    print("="*80)
    print(f"\nTests run: {len(all_outcomes)}/{len(specs)}")
    print(f"Critical regions identified: {len(critical_regions)}")
    print(f"\nNext: Review analysis and generate Phase 3 convergence tests")

if __name__ == "__main__":
    run_phase1_batch(n_samples=10)  # Start with 10 for testing
```

---

## DELIVERABLES

After completing these tasks, you should have:

1. ✅ Entity framework integrated into existing project structure
2. ✅ `warnet_network_builder.py` - Converts entity configs to network.yaml
3. ✅ `entity_test_runner.py` - Runs tests using existing Warnet tools
4. ✅ `run_phase1_batch.py` - Automated batch testing
5. ✅ 50 Phase 1 test networks generated
6. ✅ Test results with criticality scores
7. ✅ Critical regions identified for Phase 3

---

## TESTING PLAN

**Test 1: Single Network Build**
```bash
cd ~/bitcoinTools/warnet/warnetScenarioDiscovery/warnet_entity_distribution
python3 warnet_network_builder.py
# Should create test-entity-perfect-split network
```

**Test 2: Single Test Run**
```bash
python3 entity_test_runner.py
# Should run the test and produce outcome.json
```

**Test 3: Small Batch (5 tests)**
```python
# Modify run_phase1_batch.py to use n_samples=5
python3 run_phase1_batch.py
# Should complete 5 tests in ~2.5 hours
```

**Test 4: Full Phase 1 (50 tests)**
```python
# Run overnight
python3 run_phase1_batch.py
# Should complete 50 tests in ~25 hours
```

---

## KEY INTEGRATION POINTS

1. **Entity Database → Network.yaml**
   - Each entity becomes a node
   - Metadata includes custody/volume/hashrate
   - User aggregation (1000 → ~20 nodes)

2. **Network.yaml → Warnet Deploy**
   - Compatible with existing `warnet deploy` command
   - Uses existing node-defaults.yaml format

3. **Partition Mining**
   - Reuse existing `partition_miner.py`
   - Assign hashrate based on entity allocations

4. **Economic Analysis**
   - Reuse existing `auto_economic_analysis.py`
   - Reads metadata from network config

5. **Results → Criticality Scoring**
   - Parse timeline.csv + analysis.txt
   - Feed into criticality scorer
   - Identify critical regions

---

## QUESTIONS TO RESOLVE

1. **User node aggregation:** How to handle 1000 users in network?
   - Proposal: Top 10 individual + 1 aggregated node for rest

2. **Mining simulation:** How to assign hashrate to pools?
   - Proposal: Use existing partition_miner with hashrate metadata

3. **Test duration:** 30 minutes sufficient?
   - Proposal: Start with 30min, extend to 60min if needed

4. **Network size:** How many total nodes?
   - Current: ~20-30 nodes per test (manageable)

5. **Results storage:** Where to save 50+ test results?
   - Proposal: `~/bitcoinTools/warnet/warnetScenarioDiscovery/warnet_entity_distribution/phase1_results/`

---

## SUCCESS CRITERIA

✅ Can generate network.yaml from entity config  
✅ Can deploy entity-based network with Warnet  
✅ Can run fork test and collect results  
✅ Can score scenario criticality  
✅ Can batch process 50 scenarios  
✅ Can identify critical regions for Phase 3  

---

## TIMELINE

**Week 2 (This week):**
- Tasks 1-2: Copy framework + build network builder (1-2 days)
- Test network building (1 day)

**Week 3:**
- Tasks 3-4: Build test runner + batch processor (2 days)
- Run 5-10 test scenarios (1 day)
- Debug and validate (2 days)

**Week 4:**
- Run full Phase 1 (50 tests, 1-2 days compute time)
- Analyze results (1 day)
- Generate Phase 3 specs (1 day)

---

This integration connects your novel entity-based framework with the existing Warnet infrastructure, enabling systematic discovery of critical scenarios at scale.
