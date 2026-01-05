#!/usr/bin/env python3
"""
Critical Scenario Discovery - Master Orchestrator
Coordinates the complete search process: coarse → analyze → converge
"""

import json
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
import numpy as np

from entity_database import EntityDatabase
from configuration_generator import ConfigurationGenerator, NetworkConfiguration
from criticality_scorer import CriticalityScorer, TestOutcome

class ScenarioDiscoveryOrchestrator:
    """
    Master coordinator for multi-dimensional critical scenario discovery
    
    Process:
    1. Phase 1: Coarse search (50 diverse scenarios)
    2. Phase 2: Analyze results, identify critical regions
    3. Phase 3: Convergence (dense sampling around critical areas)
    4. Phase 4: Validation
    """
    
    def __init__(self, entity_db: EntityDatabase, output_dir: str = './discovery_results'):
        self.entity_db = entity_db
        self.generator = ConfigurationGenerator(entity_db)
        self.scorer = CriticalityScorer()
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.phase1_results = []
        self.phase2_critical_regions = []
        self.phase3_results = []
    
    def run_phase1_coarse_search(self, n_samples: int = 50) -> List[Dict]:
        """
        Phase 1: Coarse exploration of parameter space
        
        Returns:
            List of test specifications (not actual test results - those come from Warnet)
        """
        print("="*80)
        print("PHASE 1: COARSE SEARCH")
        print("="*80)
        print(f"\nGenerating {n_samples} diverse network configurations...")
        
        # Generate diverse configurations
        configs = self.generator.generate_coarse_grid(n_samples=n_samples)
        
        print(f"✓ Generated {len(configs)} configurations\n")
        
        # Create test specifications
        test_specs = []
        
        for i, config in enumerate(configs, 1):
            summary = config.summary()
            
            test_spec = {
                'phase': 'phase1',
                'test_number': i,
                'config_id': config.config_id,
                'config_summary': summary,
                'test_duration_minutes': 30,
                'short_description': config.to_short_string()
            }
            
            test_specs.append(test_spec)
            
            # Print summary
            if i <= 10 or i % 10 == 0:
                splits = summary['splits']
                print(f"{i:3d}. {config.config_id:30s} - {config.to_short_string()}")
        
        # Save test specifications
        phase1_file = self.output_dir / 'phase1_test_specifications.json'
        with open(phase1_file, 'w') as f:
            json.dump(test_specs, f, indent=2)
        
        print(f"\n✓ Saved test specifications to: {phase1_file}")
        print(f"\n📋 NEXT STEP: Run these {len(test_specs)} tests in Warnet")
        print(f"   Then call: orchestrator.analyze_phase1_results(results_file)")
        
        return test_specs
    
    def analyze_phase1_results(self, results_file: str) -> List[Dict]:
        """
        Phase 2: Analyze Phase 1 results to identify critical regions
        
        Args:
            results_file: JSON file with test outcomes from Warnet
        
        Returns:
            List of critical regions for Phase 3
        """
        print("\n" + "="*80)
        print("PHASE 2: CRITICAL REGION IDENTIFICATION")
        print("="*80)
        
        # Load results
        with open(results_file, 'r') as f:
            results_data = json.load(f)
        
        print(f"\n✓ Loaded {len(results_data)} test results")
        
        # Score all scenarios
        scored_results = []
        
        for result in results_data:
            config_summary = result['config_summary']
            
            # Convert to TestOutcome
            outcome = TestOutcome(
                config_id=result['config_id'],
                fork_a_blocks=result.get('fork_a_blocks', 0),
                fork_b_blocks=result.get('fork_b_blocks', 0),
                fork_a_weight=result.get('fork_a_weight', 0),
                fork_b_weight=result.get('fork_b_weight', 0),
                weight_ratio=result.get('weight_ratio', 1.0),
                risk_score=result.get('risk_score', 50),
                risk_level=result.get('risk_level', 'UNKNOWN'),
                converged=result.get('converged', True),
                resolution_time_minutes=result.get('resolution_time_minutes', 30),
                economic_winner=result.get('economic_winner', 'unknown'),
                protocol_winner=result.get('protocol_winner', 'unknown')
            )
            
            # Calculate criticality
            score, components = self.scorer.score(config_summary, outcome)
            classification = self.scorer.classify_criticality(score)
            research_q = self.scorer.identify_research_question(config_summary, outcome, components)
            
            scored_results.append({
                'config_id': result['config_id'],
                'config_summary': config_summary,
                'outcome': outcome.to_dict(),
                'criticality_score': score,
                'criticality_classification': classification,
                'score_components': components,
                'research_question': research_q
            })
        
        # Sort by criticality
        scored_results.sort(key=lambda x: x['criticality_score'], reverse=True)
        
        # Identify top critical scenarios
        print("\n### TOP 10 CRITICAL SCENARIOS ###\n")
        
        for i, result in enumerate(scored_results[:10], 1):
            print(f"{i}. {result['config_id']}")
            print(f"   Score: {result['criticality_score']:.1f} - {result['criticality_classification']}")
            print(f"   {result['research_question']}")
            
            # Show key components
            components = result['score_components']
            if components:
                print(f"   Components: {', '.join(components.keys())}")
            print()
        
        # Cluster critical scenarios to find regions
        critical_scenarios = [r for r in scored_results if r['criticality_score'] >= 40]
        
        print(f"✓ Identified {len(critical_scenarios)} critical scenarios (score ≥40)")
        
        # Group by research question
        regions = {}
        for scenario in critical_scenarios:
            rq = scenario['research_question']
            if rq not in regions:
                regions[rq] = []
            regions[rq].append(scenario)
        
        print(f"\n### CRITICAL REGIONS BY RESEARCH QUESTION ###\n")
        
        for rq, scenarios in regions.items():
            print(f"{rq}")
            print(f"  {len(scenarios)} scenarios, avg score: {np.mean([s['criticality_score'] for s in scenarios]):.1f}")
        
        # Save analysis
        analysis_file = self.output_dir / 'phase2_critical_region_analysis.json'
        with open(analysis_file, 'w') as f:
            json.dump({
                'all_scored_results': scored_results,
                'critical_scenarios': critical_scenarios,
                'regions': {rq: [s['config_id'] for s in scenarios] 
                           for rq, scenarios in regions.items()}
            }, f, indent=2)
        
        print(f"\n✓ Saved analysis to: {analysis_file}")
        
        self.phase2_critical_regions = regions
        
        return list(regions.values())
    
    def generate_phase3_convergence_tests(
        self, 
        n_per_region: int = 20
    ) -> List[Dict]:
        """
        Phase 3: Generate convergence tests around critical regions
        
        Dense sampling around the most interesting scenarios
        """
        print("\n" + "="*80)
        print("PHASE 3: CONVERGENCE TEST GENERATION")
        print("="*80)
        
        if not self.phase2_critical_regions:
            print("⚠️  No critical regions identified yet!")
            print("   Run analyze_phase1_results() first")
            return []
        
        convergence_specs = []
        
        for rq, scenarios in self.phase2_critical_regions.items():
            print(f"\n### {rq} ###")
            print(f"  Generating {n_per_region} variations...")
            
            # Get the highest-scoring scenario as template
            template = max(scenarios, key=lambda s: s['criticality_score'])
            template_config = template['config_summary']
            
            # Generate variations
            for i in range(n_per_region):
                # Perturb the configuration slightly
                # (Simplified - in real implementation, would vary entity allocations)
                
                variation_spec = {
                    'phase': 'phase3',
                    'region': rq,
                    'template': template['config_id'],
                    'variation_number': i,
                    'config_id': f"{template['config_id']}-var{i:02d}",
                    'test_duration_minutes': 30,
                    'note': 'Dense sampling around critical region'
                }
                
                convergence_specs.append(variation_spec)
        
        # Save specifications
        phase3_file = self.output_dir / 'phase3_convergence_specifications.json'
        with open(phase3_file, 'w') as f:
            json.dump(convergence_specs, f, indent=2)
        
        print(f"\n✓ Generated {len(convergence_specs)} convergence tests")
        print(f"✓ Saved to: {phase3_file}")
        
        return convergence_specs
    
    def generate_summary_report(self) -> str:
        """
        Generate final summary report of all discoveries
        """
        print("\n" + "="*80)
        print("GENERATING FINAL SUMMARY REPORT")
        print("="*80)
        
        report = []
        report.append("# Critical Scenario Discovery - Summary Report")
        report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        report.append("## Overview")
        report.append(f"- Phase 1 tests: {len(self.phase1_results)}")
        report.append(f"- Critical regions identified: {len(self.phase2_critical_regions)}")
        report.append(f"- Phase 3 convergence tests: {len(self.phase3_results)}\n")
        
        report.append("## Critical Regions\n")
        for rq, scenarios in self.phase2_critical_regions.items():
            report.append(f"### {rq}")
            report.append(f"- Scenarios: {len(scenarios)}")
            report.append(f"- Avg criticality: {np.mean([s['criticality_score'] for s in scenarios]):.1f}")
            report.append("")
        
        report_text = "\n".join(report)
        
        # Save report
        report_file = self.output_dir / 'DISCOVERY_SUMMARY_REPORT.md'
        with open(report_file, 'w') as f:
            f.write(report_text)
        
        print(report_text)
        print(f"\n✓ Report saved to: {report_file}")
        
        return report_text

# === EXAMPLE USAGE ===

if __name__ == "__main__":
    print("="*80)
    print("CRITICAL SCENARIO DISCOVERY - MASTER ORCHESTRATOR")
    print("="*80)
    
    # Load entity database
    db = EntityDatabase.load('entity_database.json')
    
    # Create orchestrator
    orchestrator = ScenarioDiscoveryOrchestrator(db, output_dir='./test_discovery')
    
    # Phase 1: Generate coarse search tests
    print("\n" + "="*80)
    print("DEMO: PHASE 1 - COARSE SEARCH")
    print("="*80)
    
    phase1_specs = orchestrator.run_phase1_coarse_search(n_samples=10)
    
    print("\n" + "="*80)
    print("✓ PHASE 1 COMPLETE")
    print("="*80)
    print("\n📋 Next steps:")
    print("1. Run the generated tests in Warnet")
    print("2. Collect results in JSON format")
    print("3. Call: orchestrator.analyze_phase1_results('results.json')")
    print("\n" + "="*80)
