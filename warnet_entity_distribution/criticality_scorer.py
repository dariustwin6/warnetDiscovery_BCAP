#!/usr/bin/env python3
"""
Criticality Scorer - Identifies "interesting" network configurations
Scores scenarios based on uncertainty, conflict, and research value
"""

from typing import Dict, List
from dataclasses import dataclass
import math

@dataclass
class TestOutcome:
    """Results from testing a configuration"""
    config_id: str
    
    # Block production
    fork_a_blocks: int
    fork_b_blocks: int
    
    # Economic analysis
    fork_a_weight: float
    fork_b_weight: float
    weight_ratio: float
    risk_score: float
    risk_level: str
    
    # Convergence
    converged: bool
    resolution_time_minutes: float
    
    # Economic vs Protocol
    economic_winner: str  # 'fork_a' or 'fork_b'
    protocol_winner: str  # 'fork_a' or 'fork_b' (more blocks)
    
    def to_dict(self) -> dict:
        return self.__dict__

class CriticalityScorer:
    """
    Scores scenarios based on how "interesting" or "critical" they are
    High criticality = worth deeper exploration
    """
    
    def __init__(self):
        # Scoring weights (can be tuned)
        self.weights = {
            'economic_protocol_disagreement': 40,
            'close_block_production': 30,
            'risk_in_uncertain_zone': 20,
            'long_resolution_time': 15,
            'high_variance': 25,
            'conflicting_indicators': 30
        }
    
    def score(
        self, 
        config_summary: dict,
        outcome: TestOutcome,
        variance_data: dict = None
    ) -> float:
        """
        Calculate criticality score for a scenario
        
        Returns:
            Score from 0-200+ (higher = more critical/interesting)
        """
        score = 0.0
        components = {}
        
        # === Component 1: Economic vs Protocol Disagreement ===
        if outcome.economic_winner != outcome.protocol_winner:
            points = self.weights['economic_protocol_disagreement']
            score += points
            components['economic_protocol_disagreement'] = points
        
        # === Component 2: Close Block Production ===
        # Closer to 50/50 = more interesting
        total_blocks = outcome.fork_a_blocks + outcome.fork_b_blocks
        if total_blocks > 0:
            balance = min(outcome.fork_a_blocks, outcome.fork_b_blocks) / total_blocks
            
            # Perfect balance (0.5) gets full points
            # Decreases as it gets more lopsided
            balance_score = 1 - abs(0.5 - balance) * 2  # 0 at extremes, 1 at 0.5
            
            if balance > 0.4:  # Within 60/40
                points = balance_score * self.weights['close_block_production']
                score += points
                components['close_block_production'] = points
        
        # === Component 3: Risk in Uncertain Zone ===
        # Risk scores in the middle range (30-70) are most uncertain
        if 30 < outcome.risk_score < 70:
            # Maximum uncertainty at 50
            uncertainty = 1 - abs(outcome.risk_score - 50) / 20
            points = uncertainty * self.weights['risk_in_uncertain_zone']
            score += points
            components['risk_in_uncertain_zone'] = points
        
        # === Component 4: Long Resolution Time ===
        # Longer forks are more interesting
        if outcome.resolution_time_minutes > 30:  # >30 minutes
            # Logarithmic scaling
            time_factor = min(math.log(outcome.resolution_time_minutes / 30 + 1), 2.0)
            points = time_factor * self.weights['long_resolution_time']
            score += points
            components['long_resolution_time'] = points
        
        # === Component 5: High Variance ===
        # If we ran this multiple times and got different results
        if variance_data and 'block_variance' in variance_data:
            if variance_data['block_variance'] > 10:  # >10% variance
                variance_factor = min(variance_data['block_variance'] / 50, 1.0)
                points = variance_factor * self.weights['high_variance']
                score += points
                components['high_variance'] = points
        
        # === Component 6: Conflicting Economic Indicators ===
        # When custody, volume, hashrate point different ways
        splits = config_summary['splits']
        
        custody_a = splits['custody']['v27']
        volume_a = splits['volume']['v27']
        hashrate_a = splits['hashrate']['v27']
        
        # Check if indicators disagree significantly (>10% difference)
        indicators = [custody_a, volume_a, hashrate_a]
        max_diff = max(indicators) - min(indicators)
        
        if max_diff > 10:
            conflict_factor = min(max_diff / 50, 1.0)
            points = conflict_factor * self.weights['conflicting_indicators']
            score += points
            components['conflicting_indicators'] = points
        
        return score, components
    
    def classify_criticality(self, score: float) -> str:
        """
        Classify criticality level
        """
        if score >= 100:
            return "VERY HIGH - Priority exploration"
        elif score >= 70:
            return "HIGH - Strong candidate"
        elif score >= 40:
            return "MEDIUM - Worth investigating"
        elif score >= 20:
            return "LOW - Standard scenario"
        else:
            return "MINIMAL - Not particularly interesting"
    
    def identify_research_question(
        self, 
        config_summary: dict,
        outcome: TestOutcome,
        components: dict
    ) -> str:
        """
        Infer what research question this scenario addresses
        """
        
        splits = config_summary['splits']
        fork_a_exchanges = config_summary['fork_a']['exchanges']
        fork_b_exchanges = config_summary['fork_b']['exchanges']
        
        # Pattern matching to identify research questions
        
        # Perfect balance scenarios
        if 'close_block_production' in components:
            if abs(splits['hashrate']['v27'] - 50) < 5:
                return "Q: Does perfect hashrate balance create maximum instability?"
        
        # David vs Goliath
        if fork_a_exchanges == 0 and config_summary['fork_a']['users'] > 500:
            return "Q: Can user numbers overcome exchange custody?"
        
        # Economic vs miners
        if 'economic_protocol_disagreement' in components:
            if splits['economic']['v27'] > 60 and splits['hashrate']['v27'] < 40:
                return "Q: Can economic majority override hashrate majority?"
        
        # Conflicting indicators
        if 'conflicting_indicators' in components:
            return "Q: What happens when custody, volume, and hashrate disagree?"
        
        # Exchange fragmentation
        if fork_a_exchanges == 1 and fork_b_exchanges == 2:
            return "Q: Can 2 smaller exchanges resist 1 major exchange?"
        
        return "Q: General threshold exploration"
    
    def explain_criticality(
        self, 
        score: float,
        components: dict,
        config_summary: dict
    ) -> str:
        """
        Human-readable explanation of why scenario is critical
        """
        explanations = []
        
        if 'economic_protocol_disagreement' in components:
            explanations.append("✓ Economic and protocol winners disagree")
        
        if 'close_block_production' in components:
            explanations.append("✓ Close block production (near 50/50)")
        
        if 'risk_in_uncertain_zone' in components:
            explanations.append("✓ Risk score in uncertain zone (30-70)")
        
        if 'long_resolution_time' in components:
            explanations.append("✓ Long-lasting fork (>30 minutes)")
        
        if 'high_variance' in components:
            explanations.append("✓ High variance across trials")
        
        if 'conflicting_indicators' in components:
            explanations.append("✓ Economic indicators conflict")
        
        if not explanations:
            explanations.append("Standard scenario, no特別 features")
        
        return "\n".join(explanations)

# === EXAMPLE USAGE ===

if __name__ == "__main__":
    print("="*80)
    print("CRITICALITY SCORER - IDENTIFY INTERESTING SCENARIOS")
    print("="*80)
    
    # Example 1: High criticality scenario
    print("\n### EXAMPLE 1: High Criticality Scenario ###\n")
    
    config_summary = {
        'config_id': 'perfect-split',
        'fork_a': {'exchanges': 1, 'mining_pools': 2, 'users': 0},
        'fork_b': {'exchanges': 2, 'mining_pools': 4, 'users': 1000},
        'splits': {
            'economic': {'v27': 48, 'v26': 52},
            'hashrate': {'v27': 50, 'v26': 50},
            'custody': {'v27': 48, 'v26': 52},
            'volume': {'v27': 48, 'v26': 52}
        }
    }
    
    outcome = TestOutcome(
        config_id='perfect-split',
        fork_a_blocks=148,
        fork_b_blocks=152,
        fork_a_weight=1100000,
        fork_b_weight=1210000,
        weight_ratio=0.91,
        risk_score=55,
        risk_level='MEDIUM',
        converged=False,
        resolution_time_minutes=45,
        economic_winner='fork_b',
        protocol_winner='fork_b'
    )
    
    scorer = CriticalityScorer()
    score, components = scorer.score(config_summary, outcome)
    classification = scorer.classify_criticality(score)
    research_q = scorer.identify_research_question(config_summary, outcome, components)
    explanation = scorer.explain_criticality(score, components, config_summary)
    
    print(f"Config: {config_summary['config_id']}")
    print(f"Criticality Score: {score:.1f}")
    print(f"Classification: {classification}")
    print(f"\nResearch Question: {research_q}")
    print(f"\nWhy Critical:")
    print(explanation)
    print(f"\nScore Breakdown:")
    for component, points in components.items():
        print(f"  - {component}: {points:.1f}")
    
    # Example 2: Low criticality scenario
    print("\n" + "="*80)
    print("### EXAMPLE 2: Low Criticality Scenario ###\n")
    
    config_summary_2 = {
        'config_id': 'lopsided',
        'fork_a': {'exchanges': 3, 'mining_pools': 6, 'users': 1000},
        'fork_b': {'exchanges': 0, 'mining_pools': 0, 'users': 0},
        'splits': {
            'economic': {'v27': 100, 'v26': 0},
            'hashrate': {'v27': 100, 'v26': 0},
            'custody': {'v27': 100, 'v26': 0},
            'volume': {'v27': 100, 'v26': 0}
        }
    }
    
    outcome_2 = TestOutcome(
        config_id='lopsided',
        fork_a_blocks=300,
        fork_b_blocks=0,
        fork_a_weight=2200000,
        fork_b_weight=0,
        weight_ratio=float('inf'),
        risk_score=5,
        risk_level='MINIMAL',
        converged=True,
        resolution_time_minutes=5,
        economic_winner='fork_a',
        protocol_winner='fork_a'
    )
    
    score_2, components_2 = scorer.score(config_summary_2, outcome_2)
    classification_2 = scorer.classify_criticality(score_2)
    
    print(f"Config: {config_summary_2['config_id']}")
    print(f"Criticality Score: {score_2:.1f}")
    print(f"Classification: {classification_2}")
    print(f"\nWhy Not Critical:")
    print("  - Overwhelming majority on one fork")
    print("  - No disagreement between indicators")
    print("  - Quick convergence")
    print("  - Predictable outcome")
    
    print("\n" + "="*80)
    print("✓ Criticality scorer ready!")
    print("="*80)
