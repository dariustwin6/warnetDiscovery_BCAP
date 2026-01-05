# Multi-Dimensional Critical Scenario Discovery Framework
## Entity-Based Bitcoin Network Fork Analysis

**Created:** January 1, 2026  
**Purpose:** Systematic exploration of high-dimensional fork configuration space  
**Research Goal:** Discover non-obvious critical scenarios through coarse search + convergence

---

## 🎯 Overview

This framework enables systematic discovery of critical Bitcoin network fork scenarios by exploring the **multi-dimensional parameter space** of entity allocations and values.

### Key Innovation

**Traditional approach:** Test simple percentages (E50/H40, E60/H30, etc.)
**Our approach:** Test entity-specific allocations with individual values

**Why better:**
- Same percentages can have completely different outcomes depending on WHICH entities and their VALUES
- Discovers non-obvious critical scenarios invisible to percentage-based analysis
- Maps entity-specific thresholds (e.g., "Top exchange alone needs >1.8M custody + >180K volume for stability")

---

## 📊 The Parameter Space

### Dimensions

**Not 2D (Economic % × Hashrate %):**

```
❌ E50/H40 = 50% economic, 40% hashrate
   → Crude, misses which entities
```

**But N-Dimensional (20-30 dimensions!):**

```
✅ Exchange 1: {custody: 2.0M BTC, volume: 200K BTC/day, fork: A/B}
   Exchange 2: {custody: 1.2M BTC, volume: 120K BTC/day, fork: A/B}
   Exchange 3: {custody: 0.8M BTC, volume: 80K BTC/day, fork: A/B}
   
   Pool Foundry: {hashrate: 27%, fork: A/B}
   Pool AntPool: {hashrate: 23%, fork: A/B}
   ... (6 pools total)
   
   Users: {count: 1000, distribution: power-law, fork_A_pct: 0-100}
```

**Total:** ~20-30 dimensional parameter space

---

## 🔬 Discovery Process

### Phase 1: Coarse Search (50 tests)
- Sample broadly across parameter space
- Cover diverse entity allocations
- Identify "interesting" regions

### Phase 2: Critical Region Identification (Analysis)
- Score all scenarios by "criticality"
- Cluster critical scenarios
- Identify research questions

### Phase 3: Convergence (100 tests)
- Dense sampling around critical regions
- Map exact boundaries and thresholds
- Discover precise entity-specific thresholds

### Phase 4: Validation
- Verify reproducibility
- Test predictions
- Document findings

---

## 🏗️ Framework Components

### 1. Entity Database (`entity_database.py`)

**Purpose:** Realistic Bitcoin network composition

**Contains:**
- 3 major exchanges (4M BTC total custody, 400K BTC/day volume)
- 6 mining pools (100% hashrate, realistic distribution)
- 1000 users (200K BTC custody, power-law distribution)

**Usage:**
```python
from entity_database import EntityDatabase

db = EntityDatabase()
db.save('entity_database.json')

# Load existing database
db = EntityDatabase.load('entity_database.json')

# Get summary
print(db.summary())
```

### 2. Configuration Generator (`configuration_generator.py`)

**Purpose:** Create network configurations by allocating entities to forks

**Usage:**
```python
from configuration_generator import ConfigurationGenerator

generator = ConfigurationGenerator(entity_db)

# Generate specific configuration
config = generator.generate_specific_config(
    config_id='test-perfect-split',
    exchange_allocation=[0],      # Exchange 0 to fork_a
    miner_allocation=[0, 1],      # Pools 0,1 to fork_a
    user_allocation_pct=0         # 0% users to fork_a (all to fork_b)
)

# Generate coarse grid for Phase 1
configs = generator.generate_coarse_grid(n_samples=50)
```

**Key Methods:**
- `generate_specific_config()` - Precise control over entity allocation
- `generate_random_config()` - Random allocation
- `generate_coarse_grid()` - Diverse sampling for Phase 1

### 3. Criticality Scorer (`criticality_scorer.py`)

**Purpose:** Identify "interesting" scenarios worth deeper exploration

**Scoring Factors:**
- Economic vs protocol disagreement (40 points)
- Close block production (30 points)
- Conflicting economic indicators (30 points)
- Risk in uncertain zone (20 points)
- Long resolution time (15 points)
- High variance across trials (25 points)

**Usage:**
```python
from criticality_scorer import CriticalityScorer

scorer = CriticalityScorer()

# Score a scenario
score, components = scorer.score(config_summary, test_outcome)
classification = scorer.classify_criticality(score)

# Score ≥100: VERY HIGH - Priority exploration
# Score ≥70:  HIGH - Strong candidate
# Score ≥40:  MEDIUM - Worth investigating
# Score <40:  LOW - Not particularly interesting
```

### 4. Master Orchestrator (`scenario_discovery_orchestrator.py`)

**Purpose:** Coordinate the entire discovery process

**Usage:**
```python
from scenario_discovery_orchestrator import ScenarioDiscoveryOrchestrator

orchestrator = ScenarioDiscoveryOrchestrator(
    entity_db, 
    output_dir='./discovery_results'
)

# Phase 1: Generate test specifications
phase1_specs = orchestrator.run_phase1_coarse_search(n_samples=50)

# After running tests in Warnet...
# Phase 2: Analyze results
critical_regions = orchestrator.analyze_phase1_results('results.json')

# Phase 3: Generate convergence tests
phase3_specs = orchestrator.generate_phase3_convergence_tests(n_per_region=20)

# Generate final report
orchestrator.generate_summary_report()
```

---

## 🚀 Quick Start

### Step 1: Create Entity Database

```bash
python3 entity_database.py
```

**Output:** `entity_database.json` with realistic network composition

### Step 2: Generate Phase 1 Test Specifications

```python
from entity_database import EntityDatabase
from scenario_discovery_orchestrator import ScenarioDiscoveryOrchestrator

# Load database
db = EntityDatabase.load('entity_database.json')

# Create orchestrator
orchestrator = ScenarioDiscoveryOrchestrator(db)

# Generate 50 diverse test specifications
specs = orchestrator.run_phase1_coarse_search(n_samples=50)
```

**Output:** `phase1_test_specifications.json`

### Step 3: Run Tests in Warnet

(Integration with existing Warnet infrastructure needed)

For each test spec:
1. Create network with specified entity allocation
2. Run fork test (30 minutes)
3. Collect outcomes (blocks, weights, timing, etc.)

### Step 4: Analyze Results

```python
# After collecting test results in JSON format
orchestrator.analyze_phase1_results('warnet_results.json')
```

**Output:** 
- `phase2_critical_region_analysis.json`
- Top 10 critical scenarios identified
- Research questions inferred
- Regions for Phase 3 exploration

### Step 5: Convergence

```python
# Generate Phase 3 convergence tests
convergence_specs = orchestrator.generate_phase3_convergence_tests(n_per_region=20)
```

**Output:** `phase3_convergence_specifications.json`

---

## 📋 Example Scenarios

### Critical Scenario 1: Perfect 50/50 Split

```python
config = generator.generate_specific_config(
    config_id='perfect-split',
    exchange_allocation=[0],      # Top exchange (50% custody)
    miner_allocation=[0, 1],      # Foundry + AntPool (50% hashrate)
    user_allocation_pct=0         # All users to other fork
)

# Result: E48/H50 split
# Hypothesis: Maximum instability!
```

### Critical Scenario 2: David vs Goliath

```python
config = generator.generate_specific_config(
    config_id='david-vs-goliath',
    exchange_allocation=[],       # No exchanges to fork_a
    miner_allocation=[2, 3, 4],  # Some pools
    user_allocation_pct=100       # ALL users to fork_a
)

# Research Q: Can user numbers overcome exchange custody?
```

### Critical Scenario 3: Economic vs Miners

```python
config = generator.generate_specific_config(
    config_id='economic-vs-miners',
    exchange_allocation=[0, 1, 2],  # All exchanges
    miner_allocation=[],             # NO miners
    user_allocation_pct=100
)

# Research Q: Can 90% custody survive 0% hashrate?
```

---

## 🎯 Expected Contributions

### 1. Non-Obvious Critical Scenarios

**Example:**
> "Exchange A (2M custody, 200K volume) alone beats 2 exchanges (combined 2M, 200K) + 60% hashrate"

Why surprising: 33% custody beats 67% + hashrate majority!  
Why true: Concentrated custody + volume > distributed custody

### 2. Entity-Specific Thresholds

**Example:**
> "Top exchange alone maintains stability if: custody >1.8M AND volume >180K AND hashrate >35%"

Practical value: Operators monitor THE TOP EXCHANGE, predict splits based on its behavior

### 3. Combination Effects

**Example:**
> "Users can tip balance ONLY when: Exchange split <55/45 AND Users >85% concentrated AND User-aligned hashrate >50%"

Explains: Why user campaigns rarely work, shows exact conditions needed

---

## 📊 File Structure

```
warnet_entity_distribution/
├── entity_database.py              # Entity database with realistic values
├── configuration_generator.py      # Network configuration generator
├── criticality_scorer.py          # Criticality scoring
├── scenario_discovery_orchestrator.py  # Master coordinator
├── entity_database.json           # Database (generated)
└── discovery_results/             # Output directory
    ├── phase1_test_specifications.json
    ├── phase2_critical_region_analysis.json
    ├── phase3_convergence_specifications.json
    └── DISCOVERY_SUMMARY_REPORT.md
```

---

## 🔗 Integration with Warnet

### Required Integration Points

**1. Network Generation from Config:**
```python
def create_warnet_network_from_entity_config(config: NetworkConfiguration):
    """
    Convert entity-based config to Warnet network.yaml
    """
    # Assign entities to v27 vs v26 partitions
    # Set custody/volume/hashrate per node
    # Generate network.yaml
```

**2. Test Execution:**
```python
def run_entity_based_test(config_spec: dict):
    """
    Run fork test based on entity configuration
    Duration: 30 minutes
    """
    # Deploy network
    # Run partition_miner
    # Monitor with auto_economic_analysis
    # Collect outcomes
```

**3. Results Collection:**
```python
def collect_test_outcomes(test_id: str) -> dict:
    """
    Gather results from Warnet test
    """
    return {
        'config_id': test_id,
        'fork_a_blocks': ...,
        'fork_b_blocks': ...,
        'fork_a_weight': ...,
        'risk_score': ...,
        # ... all required fields
    }
```

---

## 🎓 Research Applications

### For July 2026 Workshop Paper

**Title:**
> "Critical Scenario Discovery in Heterogeneous Bitcoin Networks: A Multi-Dimensional Entity-Based Analysis"

**Abstract:**
> We systematically explore the high-dimensional configuration space of Bitcoin network forks, discovering non-obvious critical scenarios invisible to percentage-based analysis...

**Contributions:**
1. Multi-dimensional framework for fork analysis
2. Critical scenario discovery methodology
3. Entity-specific threshold identification
4. Combination effect characterization

**Timeline:**
- Week 2 (Jan): Build framework ✓
- Week 3-4 (Jan): Phase 1 tests (50 scenarios)
- Week 5-6 (Feb): Phase 2 analysis + Phase 3 generation
- Week 7-8 (Feb): Phase 3 convergence tests (100 scenarios)
- Week 9-12 (Mar): Analysis, validation, writing
- July: Workshop presentation!

---

## 📚 References

### Related Work
- BCAP (Bitcoin Consensus Analysis Protocol)
- Warnet (Bitcoin network testing framework)
- Network fork analysis literature

### Novel Contributions
- First entity-specific fork threshold analysis
- Multi-dimensional critical scenario discovery
- Non-obvious combination effect identification

---

## 🤝 Contributing

This is research-in-progress for the July 2026 UW BRI Workshop.

**Contact:** [Your info here]

---

## ✅ Status

**Current:** Framework complete, ready for Phase 1 testing  
**Next:** Integrate with Warnet and run coarse search  
**Target:** July 13-17, 2026 workshop presentation

---

**Built with:** Python 3, NumPy, JSON  
**License:** [TBD]  
**Version:** 1.0.0  
