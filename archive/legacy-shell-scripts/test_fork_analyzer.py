#!/usr/bin/env python3
"""
Test Suite for Economic Fork Analyzer

Tests the BCAP-aligned dual-metric fork analysis implementation.
"""

import sys
from economic_fork_analyzer import EconomicForkAnalyzer, EconomicNode, RiskLevel


def test_consensus_weight_calculation():
    """Test consensus weight calculation with dual metrics."""
    print("TEST 1: Consensus Weight Calculation")
    print("-" * 60)

    analyzer = EconomicForkAnalyzer()

    # Test case: Major exchange (high custody, high volume)
    node1 = EconomicNode("coinbase", "major_exchange", 2000000, 100000)
    result1 = analyzer.calculate_consensus_weight(node1)

    print(f"Major Exchange (Coinbase):")
    print(f"  Custody: 2M BTC ({result1['custody_weight']:.2f}% of supply)")
    print(f"  Volume: 100k BTC/day ({result1['volume_weight']:.2f}% of daily volume)")
    print(f"  Consensus Weight: {result1['consensus_weight']:.2f}")
    print(f"  Expected: ~17.18 (10.26*0.7 + 33.33*0.3)")
    assert 17.0 < result1['consensus_weight'] < 17.5, "Major exchange weight calculation failed"

    # Test case: Payment processor (low custody, high volume)
    node2 = EconomicNode("bitpay", "payment_processor", 30000, 10000)
    result2 = analyzer.calculate_consensus_weight(node2)

    print(f"\nPayment Processor (BitPay):")
    print(f"  Custody: 30k BTC ({result2['custody_weight']:.2f}% of supply)")
    print(f"  Volume: 10k BTC/day ({result2['volume_weight']:.2f}% of daily volume)")
    print(f"  Consensus Weight: {result2['consensus_weight']:.2f}")
    print(f"  Expected: ~1.11 (0.15*0.7 + 3.33*0.3)")
    assert 1.0 < result2['consensus_weight'] < 1.2, "Payment processor weight calculation failed"

    # Test case: Custody provider (high custody, low volume)
    node3 = EconomicNode("fidelity", "custody_provider", 700000, 3000)
    result3 = analyzer.calculate_consensus_weight(node3)

    print(f"\nCustody Provider (Fidelity):")
    print(f"  Custody: 700k BTC ({result3['custody_weight']:.2f}% of supply)")
    print(f"  Volume: 3k BTC/day ({result3['volume_weight']:.2f}% of daily volume)")
    print(f"  Consensus Weight: {result3['consensus_weight']:.2f}")
    print(f"  Expected: ~2.81 (3.59*0.7 + 1.0*0.3)")
    assert 2.5 < result3['consensus_weight'] < 3.0, "Custody provider weight calculation failed"

    print("\n✓ All consensus weight calculations passed\n")


def test_risk_scoring():
    """Test risk score calculation for various supply splits."""
    print("TEST 2: Risk Scoring")
    print("-" * 60)

    analyzer = EconomicForkAnalyzer()

    test_cases = [
        (50, 50, 100, RiskLevel.EXTREME, "Perfect 50/50 split"),
        (60, 40, 80, RiskLevel.EXTREME, "60/40 split"),
        (70, 30, 60, RiskLevel.HIGH, "70/30 split"),
        (75, 25, 50, RiskLevel.MODERATE, "75/25 split"),
        (85, 15, 30, RiskLevel.LOW, "85/15 split"),
        (95, 5, 10, RiskLevel.MINIMAL, "95/5 split"),
        (100, 0, 0, RiskLevel.MINIMAL, "100/0 split (complete dominance)"),
    ]

    for chain_a, chain_b, expected_score, expected_level, description in test_cases:
        score = analyzer.calculate_risk_score(chain_a, chain_b)
        level = analyzer.classify_risk(score)

        print(f"{description:35s}: Score {score:3.0f}/100, Level: {level.value:10s}", end="")

        # Validate score
        assert abs(score - expected_score) < 1, f"Score mismatch for {description}"
        assert level == expected_level, f"Level mismatch for {description}"

        print(" ✓")

    print("\n✓ All risk scoring tests passed\n")


def test_chain_analysis():
    """Test chain analysis with multiple economic nodes."""
    print("TEST 3: Chain Analysis")
    print("-" * 60)

    analyzer = EconomicForkAnalyzer()

    # Chain with multiple nodes
    nodes = [
        EconomicNode("coinbase", "major_exchange", 2000000, 100000),
        EconomicNode("kraken", "regional_exchange", 450000, 30000),
        EconomicNode("bitpay", "payment_processor", 30000, 10000)
    ]

    analysis = analyzer.analyze_chain(nodes)

    print(f"Chain with 3 economic nodes:")
    print(f"  Total Custody: {analysis['custody_btc']:,} BTC")
    print(f"  Supply %: {analysis['supply_percentage']:.2f}%")
    print(f"  Daily Volume: {analysis['daily_volume_btc']:,} BTC")
    print(f"  Volume %: {analysis['volume_percentage']:.2f}%")
    print(f"  Consensus Weight: {analysis['consensus_weight']:.2f}")
    print(f"  Node Count: {analysis['node_count']}")

    # Validate totals
    assert analysis['custody_btc'] == 2480000, "Custody total mismatch"
    assert analysis['daily_volume_btc'] == 140000, "Volume total mismatch"
    assert analysis['node_count'] == 3, "Node count mismatch"
    assert 22 < analysis['consensus_weight'] < 24, "Consensus weight total mismatch"

    # Test empty chain
    empty_analysis = analyzer.analyze_chain([])
    assert empty_analysis['custody_btc'] == 0, "Empty chain should have 0 custody"
    assert empty_analysis['consensus_weight'] == 0, "Empty chain should have 0 weight"

    print("\n✓ Chain analysis tests passed\n")


def test_fork_scenarios():
    """Test complete fork scenarios."""
    print("TEST 4: Fork Scenarios")
    print("-" * 60)

    analyzer = EconomicForkAnalyzer()

    # Scenario 1: Extreme risk (near 50/50 split of TOTAL SUPPLY)
    print("Scenario 1: Extreme Risk (50/50 custody split)")
    # To get ~50/50 split, we need nodes holding ~9.75M BTC each (50% of 19.5M)
    chain_a = [
        EconomicNode("coinbase", "major_exchange", 2000000, 100000),
        EconomicNode("kraken", "regional_exchange", 450000, 30000),
        EconomicNode("fidelity", "custody_provider", 700000, 3000),
        # Need more nodes to reach ~9.75M BTC
        EconomicNode("exchange-group-a", "major_exchange", 7_100_000, 200000)
    ]
    chain_b = [
        EconomicNode("binance", "major_exchange", 2200000, 110000),
        EconomicNode("exchange-group-b", "major_exchange", 7_300_000, 210000)
    ]

    result = analyzer.analyze_fork(chain_a, chain_b)

    print(f"  Chain A: {result['chains']['chain_a']['supply_percentage']:.1f}% of supply")
    print(f"  Chain B: {result['chains']['chain_b']['supply_percentage']:.1f}% of supply")
    print(f"  Risk: {result['risk_assessment']['score']:.1f}/100 ({result['risk_assessment']['level']})")

    # Should be near 50/50, so high/extreme risk
    assert result['risk_assessment']['score'] > 70, "Should be high risk for near 50/50 split"

    # Scenario 2: Clear majority (low risk)
    print("\nScenario 2: Clear Majority (overwhelming custody on one chain)")
    chain_a_majority = [
        EconomicNode("coinbase", "major_exchange", 2000000, 100000),
        EconomicNode("binance", "major_exchange", 2200000, 110000),
        EconomicNode("kraken", "regional_exchange", 450000, 30000),
        EconomicNode("fidelity", "custody_provider", 700000, 3000)
    ]
    chain_b_minority = [EconomicNode("bitpay", "payment_processor", 30000, 10000)]

    result2 = analyzer.analyze_fork(chain_a_majority, chain_b_minority)

    print(f"  Chain A: {result2['chains']['chain_a']['supply_percentage']:.1f}% of supply")
    print(f"  Chain B: {result2['chains']['chain_b']['supply_percentage']:.1f}% of supply")
    print(f"  Risk: {result2['risk_assessment']['score']:.1f}/100 ({result2['risk_assessment']['level']})")

    # Should be clear majority, so low/moderate risk
    assert result2['risk_assessment']['score'] < 70, "Should be lower risk for clear majority"
    assert result2['risk_assessment']['consensus_chain'] == 'A', "Chain A should have consensus"

    # Scenario 3: Custody vs Volume (realistic proportions)
    print("\nScenario 3: Volume vs Custody (payment processors vs custodians)")
    chain_a_volume = [
        # Payment processors: high volume but low custody
        EconomicNode("bitpay", "payment_processor", 30000, 15000),
        EconomicNode("strike", "payment_processor", 20000, 10000),
    ]
    chain_b_custody = [
        # Custody provider: high custody but low volume
        EconomicNode("fidelity", "custody_provider", 700000, 3000),
        EconomicNode("grayscale", "custody_provider", 500000, 2000)
    ]

    result3 = analyzer.analyze_fork(chain_a_volume, chain_b_custody)

    print(f"  Chain A (volume-heavy): {result3['chains']['chain_a']['volume_percentage']:.1f}% volume, "
          f"{result3['chains']['chain_a']['supply_percentage']:.1f}% custody")
    print(f"  Chain B (custody-heavy): {result3['chains']['chain_b']['volume_percentage']:.1f}% volume, "
          f"{result3['chains']['chain_b']['supply_percentage']:.1f}% custody")
    print(f"  Winner: Chain {result3['risk_assessment']['consensus_chain']} "
          f"(weight: {result3['chains']['chain_' + result3['risk_assessment']['consensus_chain'].lower()]['consensus_weight']:.2f})")

    # Chain B should win (custody is weighted 70%, and B has much more custody)
    assert result3['risk_assessment']['consensus_chain'] == 'B', "Custody should dominate over volume"

    print("\n✓ All fork scenario tests passed\n")


def test_edge_cases():
    """Test edge cases and boundary conditions."""
    print("TEST 5: Edge Cases")
    print("-" * 60)

    analyzer = EconomicForkAnalyzer()

    # Test 1: Zero custody node
    print("Edge Case 1: Zero custody node")
    node_zero = EconomicNode("test", "payment_processor", 0, 10000)
    result = analyzer.calculate_consensus_weight(node_zero)
    assert result['consensus_weight'] > 0, "Should have weight from volume even with 0 custody"
    assert result['custody_weight'] == 0, "Custody weight should be 0"
    print(f"  Node with 0 custody, 10k volume: weight = {result['consensus_weight']:.2f} ✓")

    # Test 2: Zero volume node
    print("\nEdge Case 2: Zero volume node")
    node_zero_vol = EconomicNode("test2", "custody_provider", 100000, 0)
    result2 = analyzer.calculate_consensus_weight(node_zero_vol)
    assert result2['consensus_weight'] > 0, "Should have weight from custody even with 0 volume"
    assert result2['volume_weight'] == 0, "Volume weight should be 0"
    print(f"  Node with 100k custody, 0 volume: weight = {result2['consensus_weight']:.2f} ✓")

    # Test 3: One-sided fork (all nodes on one chain)
    print("\nEdge Case 3: One-sided fork (all nodes on chain A)")
    chain_a_all = [
        EconomicNode("coinbase", "major_exchange", 2000000, 100000),
        EconomicNode("binance", "major_exchange", 2200000, 110000)
    ]
    chain_b_empty = []

    result3 = analyzer.analyze_fork(chain_a_all, chain_b_empty)
    assert result3['risk_assessment']['consensus_chain'] == 'A', "Chain A should win"
    assert result3['chains']['chain_b']['consensus_weight'] == 0, "Chain B should have 0 weight"
    print(f"  Chain A: {result3['chains']['chain_a']['consensus_weight']:.2f}, "
          f"Chain B: {result3['chains']['chain_b']['consensus_weight']:.2f} ✓")

    # Test 4: Custom supply parameters
    print("\nEdge Case 4: Custom circulating supply")
    custom_analyzer = EconomicForkAnalyzer(circulating_supply=20_000_000, daily_onchain_volume=400_000)
    node_custom = EconomicNode("test", "major_exchange", 2000000, 100000)
    result4 = custom_analyzer.calculate_consensus_weight(node_custom)
    print(f"  With 20M supply: custody weight = {result4['custody_weight']:.2f}% "
          f"(should be 10.0%) ✓")
    assert 9.9 < result4['custody_weight'] < 10.1, "Custom supply calculation incorrect"

    print("\n✓ All edge case tests passed\n")


def run_all_tests():
    """Run all test suites."""
    print("=" * 80)
    print("ECONOMIC FORK ANALYZER - TEST SUITE")
    print("=" * 80)
    print()

    try:
        test_consensus_weight_calculation()
        test_risk_scoring()
        test_chain_analysis()
        test_fork_scenarios()
        test_edge_cases()

        print("=" * 80)
        print("✓ ALL TESTS PASSED")
        print("=" * 80)
        return 0

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
