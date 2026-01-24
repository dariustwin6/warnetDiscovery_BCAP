#!/usr/bin/env python3
"""
Analyze All Critical Fork Scenarios

Runs economic fork analysis on all test scenarios and generates
a comparison table ranking them by risk score.

Usage:
    python3 analyze_all_scenarios.py
"""

import sys
import os
from pathlib import Path
import yaml
from economic_fork_analyzer import EconomicForkAnalyzer, EconomicNode


def load_and_analyze_scenario(scenario_path):
    """
    Load a scenario network config and run fork analysis.

    Returns:
        (scenario_name, analysis_result)
    """
    network_yaml = os.path.join(scenario_path, 'network.yaml')

    if not os.path.exists(network_yaml):
        print(f"✗ Network config not found: {network_yaml}")
        return None, None

    with open(network_yaml, 'r') as f:
        config = yaml.safe_load(f)

    scenario_name = config.get('network', {}).get('name', 'unknown')
    description = config.get('network', {}).get('description', '')

    print(f"\nAnalyzing: {scenario_name}")
    print(f"  {description}")

    # Extract nodes and group by version
    nodes_by_version = {}

    for node_config in config.get('nodes', []):
        metadata = node_config.get('metadata', {})

        # Skip non-economic nodes
        if 'custody_btc' not in metadata:
            continue

        # Extract version
        image = node_config.get('image', '')
        version = image.split(':')[-1] if ':' in image else 'unknown'

        # Create EconomicNode
        economic_node = EconomicNode(
            name=node_config['name'],
            node_type=metadata.get('node_type', 'unknown'),
            custody_btc=metadata.get('custody_btc', 0),
            daily_volume_btc=metadata.get('daily_volume_btc', 0),
            metadata={'version': version}
        )

        if version not in nodes_by_version:
            nodes_by_version[version] = []
        nodes_by_version[version].append(economic_node)

    # Analyze fork (assuming v26 vs v27 split)
    versions = sorted(nodes_by_version.keys())

    if len(versions) < 2:
        print(f"  Warning: Only {len(versions)} version(s) found - cannot analyze fork")
        return scenario_name, None

    # Use first two versions for analysis
    chain_a = nodes_by_version[versions[0]]
    chain_b = nodes_by_version[versions[1]]

    analyzer = EconomicForkAnalyzer()
    result = analyzer.analyze_fork(chain_a, chain_b)

    # Add scenario metadata
    result['scenario_name'] = scenario_name
    result['scenario_description'] = description
    result['version_a'] = versions[0]
    result['version_b'] = versions[1]

    return scenario_name, result


def print_summary_table(all_results):
    """Print comparison table of all scenarios ranked by risk score."""
    print("\n" + "=" * 100)
    print("CRITICAL FORK SCENARIOS - COMPARISON TABLE")
    print("=" * 100)

    # Sort by risk score (descending)
    sorted_results = sorted(
        all_results,
        key=lambda x: x[1]['risk_assessment']['score'] if x[1] else 0,
        reverse=True
    )

    print("\n{:<30} {:<12} {:<12} {:<15} {:<15} {:<10}".format(
        "Scenario", "Risk Score", "Risk Level", "Chain A", "Chain B", "Winner"
    ))
    print("-" * 100)

    for scenario_name, result in sorted_results:
        if not result:
            continue

        risk = result['risk_assessment']
        chain_a = result['chains']['chain_a']
        chain_b = result['chains']['chain_b']

        print("{:<30} {:>5.1f}/100   {:<12} {:>6.1f}% supply {:>6.1f}% supply Chain {}".format(
            scenario_name[:29],
            risk['score'],
            risk['level'],
            chain_a['supply_percentage'],
            chain_b['supply_percentage'],
            risk['consensus_chain']
        ))

    print("\n" + "=" * 100)


def print_detailed_results(scenario_name, result):
    """Print detailed analysis for one scenario."""
    if not result:
        return

    print("\n" + "=" * 100)
    print(f"SCENARIO: {scenario_name}")
    print("=" * 100)

    print(f"\nDescription: {result.get('scenario_description', 'N/A')}")

    risk = result['risk_assessment']
    chain_a = result['chains']['chain_a']
    chain_b = result['chains']['chain_b']
    metrics = result['metrics_breakdown']

    print(f"\n### FORK ANALYSIS ###")
    print(f"  Version split: {result.get('version_a', '?')} vs {result.get('version_b', '?')}")
    print(f"  Risk Score: {risk['score']:.1f}/100 ({risk['level']})")
    print(f"  Consensus Chain: Chain {risk['consensus_chain']} (margin: {risk['consensus_margin']:.2f})")

    print(f"\n### METRICS ###")
    print(f"  Supply Split: {metrics['supply_split']}")
    print(f"  Volume Split: {metrics['volume_split']}")
    print(f"  Weight Split: {metrics['weight_split']}")

    print(f"\n### CHAIN A ({result.get('version_a', '?')}) ###")
    print(f"  Nodes: {chain_a['node_count']}")
    print(f"  Custody: {chain_a['custody_btc']:,} BTC ({chain_a['supply_percentage']:.2f}%)")
    print(f"  Volume: {chain_a['daily_volume_btc']:,} BTC/day ({chain_a['volume_percentage']:.1f}%)")
    print(f"  Weight: {chain_a['consensus_weight']:.2f}")

    print(f"\n### CHAIN B ({result.get('version_b', '?')}) ###")
    print(f"  Nodes: {chain_b['node_count']}")
    print(f"  Custody: {chain_b['custody_btc']:,} BTC ({chain_b['supply_percentage']:.2f}%)")
    print(f"  Volume: {chain_b['daily_volume_btc']:,} BTC/day ({chain_b['volume_percentage']:.1f}%)")
    print(f"  Weight: {chain_b['consensus_weight']:.2f}")


def main():
    """Run analysis on all critical scenarios."""
    print("=" * 100)
    print("CRITICAL FORK SCENARIO ANALYSIS - All Scenarios")
    print("=" * 100)

    # Find all scenario directories
    test_networks_dir = Path(__file__).parent.parent.parent / 'test-networks'

    scenarios = [
        'dual-metric-test',  # Original baseline
        'critical-50-50-split',  # Scenario 1
        'custody-volume-conflict',  # Scenario 2
        'single-major-exchange-fork',  # Scenario 3
    ]

    all_results = []

    for scenario in scenarios:
        scenario_path = test_networks_dir / scenario

        if not scenario_path.exists():
            print(f"\n✗ Scenario not found: {scenario}")
            continue

        scenario_name, result = load_and_analyze_scenario(str(scenario_path))

        if result:
            all_results.append((scenario_name, result))
            print_detailed_results(scenario_name, result)

    # Print comparison table
    if all_results:
        print_summary_table(all_results)

    print("\n✓ Analysis complete")
    return 0


if __name__ == '__main__':
    sys.exit(main())
