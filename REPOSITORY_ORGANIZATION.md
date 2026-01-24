# Warnet Bitcoin Fork Testing Repository Organization

**Last Updated**: 2026-01-24

This document describes the organization of the warnet repository, including all working components, their locations, and recommendations for cleanup.

---

## Table of Contents

1. [Core Warnet Installation](#core-warnet-installation)
2. [Testing Infrastructure](#testing-infrastructure)
3. [Scenarios and Scripts](#scenarios-and-scripts)
4. [Test Networks](#test-networks)
5. [Analysis Tools](#analysis-tools)
6. [Documentation](#documentation)
7. [Redundant/Archive Candidates](#redundantarchive-candidates)
8. [Recommended Cleanup Actions](#recommended-cleanup-actions)

---

## Core Warnet Installation

### `/warnet/` - Official Warnet Package
**Purpose**: Core warnet installation (forked/cloned from official repo)

**Key Components**:
- `src/warnet/` - Python package source code
- `resources/` - Warnet resources (charts, images, networks, plugins)
- `resources/scenarios/` - **ACTIVE** Official warnet scenarios + custom scenarios
- `test/` - Warnet unit tests
- `.venv/` - Python virtual environment

**Status**: ✅ Active - Core infrastructure

**Recent Additions**:
- `resources/scenarios/partition_miner.py` - Partition mining scenario (updated with price tracking)
- `resources/scenarios/partition_miner_price_test.py` - Standalone price test version
- `resources/scenarios/price_oracle.py` - Price tracking module
- `resources/scenarios/price_model_config.yaml` - Price model configuration
- `resources/scenarios/economic_miner.py` - Economic-based mining scenario

---

## Testing Infrastructure

### `/warnet_entity_distribution/` - Entity-Based Test Runner
**Purpose**: BCAP-based entity distribution testing infrastructure

**Key Files**:
- ✅ `entity_test_runner.py` - Main test orchestration engine
- ✅ `run_phase1_batch.py` - Batch test runner
- ✅ `entity_database.json` - Real Bitcoin entity data (exchanges, pools, users)
- ✅ `warnet_network_builder.py` - Network configuration generator
- ✅ `configuration_generator.py` - Test configuration generation
- ✅ `criticality_scorer.py` - Entity criticality scoring

**Subdirectories**:
- `phase1_results/` - Results from 50-sample Phase 1 tests
- `test_results/` - Individual test run results

**Status**: ✅ Active - Primary testing infrastructure

---

### `/warnetScenarioDiscovery/` - Legacy Test Infrastructure
**Purpose**: Original testing infrastructure (being superseded by `/warnet_entity_distribution/`)

**Key Components**:

#### `/warnetScenarioDiscovery/tools/` - Analysis and Utilities
**Status**: 🟡 Partially Active - Some tools still in use

**Active Tools**:
- ✅ `temporal_analyzer.py` - Time-series fork analysis (NEW - Jan 8)
- ✅ `weight_optimizer.py` - Custody/volume weight optimization (NEW - Jan 8)

**Legacy Tools** (Candidates for Archive):
- 🗄️ `analyze_fork_depth.py` - Superseded by economic_fork_analyzer.py
- 🗄️ `continuous_mining_test.sh` - Old shell-based testing
- 🗄️ `natural_fork_test.sh` - Replaced by entity_test_runner.py
- 🗄️ Various partition/monitoring shell scripts

#### `/warnetScenarioDiscovery/monitoring/` - Economic Analysis
**Status**: ✅ Active - Core analysis components

**Key Files**:
- ✅ `auto_economic_analysis.py` - BCAP economic impact analyzer
- ✅ `economic_fork_analyzer.py` - Fork criticality analysis
- ✅ `validate_dual_metric_model.py` - BCAP model validation

**Legacy Files**:
- 🗄️ `analyze_all_scenarios.py` - Old batch analyzer

#### `/warnetScenarioDiscovery/test_results/` - Historical Results
**Status**: 🗄️ Archive - Contains old test results
- `continuous_mining_20251228_*/` - Results from Dec 2025 tests

---

## Scenarios and Scripts

### Current Scenario Locations

#### 1. `/warnet/resources/scenarios/` ✅ PRIMARY LOCATION
**Official warnet scenarios + custom scenarios**

**Active Custom Scenarios**:
- `partition_miner.py` - Partition mining with price tracking support
- `partition_miner_price_test.py` - Standalone price test version
- `price_oracle.py` - Price tracking module (Phase 1 implementation)
- `price_model_config.yaml` - Price model configuration
- `economic_miner.py` - Economic-based mining scenario

**Warnet Built-in**:
- `commander.py` - Base scenario framework
- `miner_std.py`, `signet_miner.py` - Basic mining scenarios
- `ln_init.py` - Lightning network scenarios
- `tx_flood.py` - Transaction flooding

#### 2. `/scenarios/` 🗄️ REDUNDANT
**Duplicate of `/warnet/resources/scenarios/` from Jan 6 snapshot**

Contains older versions of scenarios that are now in `/warnet/resources/scenarios/`

**Action**: Move to archive

#### 3. `/discovery/scenarios/` 🗄️ LEGACY
**Very old discovery scenarios**

**Action**: Move to archive or delete if no longer needed

---

## Test Networks

### `/test-networks/` - Network Configurations
**Purpose**: Warnet network configurations for various test scenarios

**Organization by Type**:

#### Critical Scenarios (Hand-crafted, High-value)
- `critical-50-50-split/` - 50/50 economic split
- `custody-volume-conflict/` - Custody/volume conflict test
- `david-vs-goliath/` - Large vs small entity test
- `economic-vs-miners/` - Economic weight vs hashrate
- `single-major-exchange-fork/` - Single dominant exchange

#### Baseline Tests
- `baseline-all-v27/` - All nodes v27 (control test)
- `perfect-split-50-50/` - Perfect 50/50 split

#### Random Generated Tests (45 networks)
- `random-000/` through `random-044/` - Randomly generated entity distributions

#### Systematic Test Series

**Series 1: Economic Dominance vs Low Hashrate**
- `test-1.1-E95-H10-dynamic/` - 95% economic, 10% hashrate
- `test-1.2-E10-H95-dynamic/` - 10% economic, 95% hashrate (inverted)
- `test-1.3-E90-H90-dynamic/` - Both high

**Series 2: Economic Variations (Constant E/H=40%)**
- `test-2.1-E50-H40-dynamic/` through `test-2.15-E45-H45-dynamic/`
- Testing various economic/hashrate combinations

**Series 3-5: Additional systematic tests**
- `test-3.5-economic-30-hashrate-70/`
- `test-4.4-economic-50-hashrate-50/`
- `test-5.3-economic-70-hashrate-30/`

#### Aggregation Level Tests
- `test-max-aggregation/` - Minimal nodes, high aggregation
- `test-moderate-aggregation/` - Moderate aggregation
- `test-high-granularity/` - Many nodes, low aggregation
- `test-max-realism/` - Maximum realistic complexity

**Total**: 85 test network configurations

**Status**: ✅ Active - Used by entity_test_runner.py

**Shared Configuration**:
- `node-defaults.yaml` - Common node configuration
- `BCAP_QUICK_REFERENCE.md` - BCAP methodology reference

---

## Analysis Tools

### Active Tools

#### `/warnetScenarioDiscovery/tools/`
- ✅ `temporal_analyzer.py` - Analyze fork dynamics over time
- ✅ `weight_optimizer.py` - Optimize custody/volume weights

#### `/warnet_entity_distribution/`
- ✅ `entity_test_runner.py` - Test orchestration
- ✅ `run_phase1_batch.py` - Batch test execution

#### `/warnetScenarioDiscovery/monitoring/`
- ✅ `auto_economic_analysis.py` - Economic impact analysis
- ✅ `economic_fork_analyzer.py` - Fork criticality scoring

### Utility Scripts

#### Root Directory
- ✅ `validate_infrastructure.py` - Infrastructure validation script

---

## Documentation

### Current Documentation Files

#### Root Directory - High-Level Docs
- ✅ `README.md` - Repository overview
- ✅ `BCAP_IMPLEMENTATION_SUMMARY.md` - BCAP framework implementation
- ✅ `INFRASTRUCTURE_STATUS.md` - Infrastructure status (Dec 21, 2025)
- ✅ `CRITICAL_SCENARIOS_SUMMARY.md` - Critical test scenarios
- ✅ `FORK_DEPTH_ANALYSIS.md` - Fork depth calculation analysis
- ✅ `POOL_MINING_IMPLEMENTATION.md` - Pool mining feature docs

#### Phase Documentation
- ✅ `PHASE_1_WORKSHOP_PLAN.md` - Original Phase 1 planning
- ✅ `PHASE_2_COMPLETION_SUMMARY.md` - Phase 2 results

#### Session Notes
- 🗄️ `SESSION_SUMMARY_2025-12-28.md` - Session from Dec 28
- 🗄️ `SESSION_SUMMARY_2025-12-29_FORK_DEPTH.md` - Fork depth session

#### Network Generation
- ✅ `CONFIGURABLE_NETWORK_GENERATOR.md` - Network generator docs

#### Task Documentation
- 🗄️ `TASK_0.1_VALIDATION_REPORT.md` - Early validation report

#### Tool-Specific Docs
- `/warnetScenarioDiscovery/tools/`:
  - ✅ `USAGE_GUIDE.md` - Tool usage guide
  - ✅ `AUTOMATED_TEST_EXECUTION.md` - Automated testing guide
  - ✅ `MANUAL_TEST_EXECUTION_GUIDE.md` - Manual testing guide
  - 🗄️ `SUSTAINED_FORK_DEMO.md` - Old demo documentation

- `/warnet_entity_distribution/`:
  - ✅ `README.md` - Entity distribution system readme
  - ✅ `CLAUDE_CODE_INTEGRATION_PROMPT.md` - Claude Code integration guide

#### New Documentation (Not Yet Created)
- ⚠️ **MISSING**: `DYNAMIC_ECONOMIC_IMPLEMENTATION_PLAN.md` - Phase 1-5 implementation plan
  - **Location**: Should be in `/warnetScenarioDiscovery/tools/` or root
  - **Status**: Created in conversation but not written to disk yet

---

## Redundant/Archive Candidates

### Directories to Archive

#### 1. `/scenarios/` 🗄️
**Reason**: Complete duplicate of `/warnet/resources/scenarios/` from Jan 6
**Action**: Move to `/archive/2025-01-06-scenarios-snapshot/`

#### 2. `/discovery/` 🗄️
**Reason**: Very old legacy discovery infrastructure
**Contents**:
- `networks/` - Old network configs
- `scenarios/` - Old scenarios
- `plugins/` - Old plugins

**Action**: Move to `/archive/legacy-discovery/`

#### 3. `/warnetScenarioDiscovery/test_results/continuous_mining_*/` 🗄️
**Reason**: Historical test results from Dec 2025
**Action**: Move to `/archive/test-results-dec-2025/`

#### 4. `/warnet-economic-implementation/` 🗄️
**Reason**: Appears to be early implementation attempt
**Action**: Review contents, then archive or delete

### Files to Archive

#### Session Summaries
- `SESSION_SUMMARY_2025-12-28.md`
- `SESSION_SUMMARY_2025-12-29_FORK_DEPTH.md`

**Action**: Move to `/archive/session-notes/`

#### Old Task Reports
- `TASK_0.1_VALIDATION_REPORT.md`

**Action**: Move to `/archive/early-reports/`

#### Deprecated Scripts in `/warnetScenarioDiscovery/tools/`
- `continuous_mining_test.sh`
- `natural_fork_test.sh`
- `demo_sustained_fork.sh`
- `partition_5node_network.sh`
- Various old monitoring scripts

**Action**: Move to `/archive/legacy-shell-scripts/`

---

## Recommended Cleanup Actions

### Phase 1: Create Archive Structure

```bash
mkdir -p archive/
mkdir -p archive/2025-01-06-scenarios-snapshot/
mkdir -p archive/legacy-discovery/
mkdir -p archive/test-results-dec-2025/
mkdir -p archive/session-notes/
mkdir -p archive/early-reports/
mkdir -p archive/legacy-shell-scripts/
```

### Phase 2: Move Redundant Directories

```bash
# Move duplicate scenarios
mv scenarios/ archive/2025-01-06-scenarios-snapshot/

# Move old discovery infrastructure
mv discovery/ archive/legacy-discovery/

# Move old test results
mv warnetScenarioDiscovery/test_results/continuous_mining_* archive/test-results-dec-2025/

# Review and archive warnet-economic-implementation
# (Review first - may want to delete entirely)
mv warnet-economic-implementation/ archive/
```

### Phase 3: Move Old Documentation

```bash
# Session notes
mv SESSION_SUMMARY_*.md archive/session-notes/

# Old task reports
mv TASK_0.1_VALIDATION_REPORT.md archive/early-reports/
```

### Phase 4: Archive Legacy Scripts

```bash
cd warnetScenarioDiscovery/tools/
mv continuous_mining_test.sh archive/legacy-shell-scripts/
mv natural_fork_test.sh archive/legacy-shell-scripts/
mv demo_sustained_fork.sh archive/legacy-shell-scripts/
mv partition_5node_network.sh archive/legacy-shell-scripts/
mv reconnect_5node_network.sh archive/legacy-shell-scripts/
mv sustained_fork_monitor.sh archive/legacy-shell-scripts/
mv SUSTAINED_FORK_DEMO.md archive/legacy-shell-scripts/
# ... and other deprecated shell scripts
```

### Phase 5: Update README

Update `README.md` to reflect new organization and point to this organization document.

---

## Active Development Areas

### Current Work (Phase 1: Price Model)

**Location**: `/warnet/resources/scenarios/`

**Files**:
- ✅ `price_oracle.py` - Complete
- ✅ `price_model_config.yaml` - Complete
- ✅ `partition_miner.py` - Updated with price tracking
- ✅ `partition_miner_price_test.py` - Standalone test version

**Status**: Phase 1 complete, validated 2026-01-24

### Upcoming Work (Phase 2-5)

**Phase 2**: Fee Market Dynamics (Weeks 4-6)
**Phase 3**: Dynamic Node Choice (Weeks 7-10)
**Phase 4**: Integration (Weeks 11-12)
**Phase 5**: Validation (Weeks 13-14)

**Documentation**: See `DYNAMIC_ECONOMIC_IMPLEMENTATION_PLAN.md` (when created)

---

## Directory Structure Summary

### Active Directories (Keep as-is)

```
warnet/
├── resources/scenarios/         ← PRIMARY scenario location
├── src/warnet/                  ← Core warnet source
└── test/                        ← Unit tests

warnet_entity_distribution/      ← Primary testing infrastructure
├── entity_test_runner.py
├── run_phase1_batch.py
├── entity_database.json
├── phase1_results/
└── test_results/

test-networks/                   ← All test network configs (85 networks)

warnetScenarioDiscovery/
├── monitoring/                  ← Economic analysis tools
│   ├── auto_economic_analysis.py
│   └── economic_fork_analyzer.py
└── tools/                       ← Analysis utilities
    ├── temporal_analyzer.py
    └── weight_optimizer.py
```

### Archive Candidates

```
scenarios/                       → archive/2025-01-06-scenarios-snapshot/
discovery/                       → archive/legacy-discovery/
warnet-economic-implementation/  → archive/ (or delete)
warnetScenarioDiscovery/test_results/continuous_mining_*/ → archive/test-results-dec-2025/
SESSION_SUMMARY_*.md            → archive/session-notes/
```

---

## Quick Reference: Where to Find Things

### Scenarios
- **Official + Custom**: `/warnet/resources/scenarios/`
- **Price tracking**: `price_oracle.py`, `partition_miner_price_test.py`

### Testing Infrastructure
- **Test runner**: `/warnet_entity_distribution/entity_test_runner.py`
- **Batch runner**: `/warnet_entity_distribution/run_phase1_batch.py`

### Test Networks
- **All configs**: `/test-networks/` (85 networks)

### Analysis
- **Economic analysis**: `/warnetScenarioDiscovery/monitoring/auto_economic_analysis.py`
- **Temporal analysis**: `/warnetScenarioDiscovery/tools/temporal_analyzer.py`
- **Weight optimization**: `/warnetScenarioDiscovery/tools/weight_optimizer.py`

### Documentation
- **Overview**: `README.md`
- **Organization**: `REPOSITORY_ORGANIZATION.md` (this file)
- **BCAP**: `BCAP_IMPLEMENTATION_SUMMARY.md`
- **Infrastructure**: `INFRASTRUCTURE_STATUS.md`

### Results
- **Phase 1 results**: `/warnet_entity_distribution/phase1_results/`
- **Recent test results**: `/warnet_entity_distribution/test_results/`

---

## Maintenance Schedule

### Weekly
- Review and clean up `/warnet_entity_distribution/test_results/` (keep only recent)
- Check for new redundant files

### Monthly
- Review archive directory size
- Compress old test results
- Update this document if structure changes

### Per-Phase
- Document new components in this file
- Archive old phase materials
- Update README.md

---

**Document Version**: 1.0
**Created**: 2026-01-24
**Last Review**: 2026-01-24
**Next Review**: 2026-02-24
