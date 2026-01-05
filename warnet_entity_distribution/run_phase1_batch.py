#!/usr/bin/env python3
"""
Phase 1 Batch Runner
Automates execution of Phase 1 coarse search (50 entity-based fork tests)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import time
from pathlib import Path
from typing import List, Dict
from datetime import datetime

from entity_database import EntityDatabase
from configuration_generator import ConfigurationGenerator
from warnet_network_builder import WarnetNetworkBuilder
from entity_test_runner import EntityTestRunner


class Phase1BatchRunner:
    """
    Runs Phase 1 coarse search batch tests
    """

    def __init__(
        self,
        entity_db: EntityDatabase,
        output_dir: str = None,
        warnet_root: str = "/home/pfoytik/bitcoinTools/warnet"
    ):
        self.entity_db = entity_db
        self.warnet_root = Path(warnet_root)

        if output_dir is None:
            output_dir = self.warnet_root / "warnet_entity_distribution" / "phase1_results"

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.generator = ConfigurationGenerator(entity_db)
        self.builder = WarnetNetworkBuilder()
        self.runner = EntityTestRunner(warnet_root=str(warnet_root))

    def run_phase1_batch(
        self,
        n_samples: int = 50,
        test_duration: int = 1800,  # 30 minutes per test
        start_from: int = 0,  # For resuming interrupted runs
        dry_run: bool = False
    ) -> Dict:
        """
        Run Phase 1 coarse search batch

        Args:
            n_samples: Number of diverse scenarios to test
            test_duration: Duration of each test in seconds
            start_from: Test index to start from (for resuming)
            dry_run: If True, only generate configs without running tests

        Returns:
            Dict with batch results summary
        """

        print("=" * 80)
        print("PHASE 1 COARSE SEARCH BATCH")
        print("=" * 80)
        print(f"Samples: {n_samples}")
        print(f"Test duration: {test_duration}s ({test_duration//60} minutes)")
        print(f"Total estimated time: {n_samples * (test_duration + 300) // 3600:.1f} hours")
        print(f"Start from: Test {start_from}")
        print(f"Mode: {'DRY RUN (configs only)' if dry_run else 'FULL TEST RUN'}")
        print("=" * 80)
        print()

        # Generate diverse configurations
        print("Generating diverse configurations...")
        configs = self.generator.generate_coarse_grid(n_samples=n_samples)
        print(f"✓ Generated {len(configs)} configurations")
        print()

        # Save configuration specs
        self._save_config_specs(configs)

        # Initialize batch results
        batch_results = {
            'phase': 'phase1_coarse_search',
            'timestamp': datetime.now().isoformat(),
            'n_samples': n_samples,
            'test_duration': test_duration,
            'configs': [],
            'results': [],
            'summary': {
                'total': len(configs),
                'completed': 0,
                'failed': 0,
                'errors': 0
            }
        }

        if dry_run:
            print("DRY RUN: Configuration specs saved, exiting without running tests")
            batch_results['dry_run'] = True
            self._save_batch_results(batch_results)
            return batch_results

        # Run tests
        for i, config in enumerate(configs):
            if i < start_from:
                print(f"Skipping test {i} (start_from={start_from})")
                continue

            print("\n" + "=" * 80)
            print(f"TEST {i+1}/{len(configs)}: {config.config_id}")
            print("=" * 80)

            test_start = time.time()

            try:
                # Generate network with moderate user aggregation
                # users_per_node=100 gives ~20-50 nodes for realistic block propagation
                print(f"Building network for {config.config_id}...")
                network_dir = self.builder.build_network_from_entity_config(
                    config,
                    users_per_node=100
                )
                print(f"✓ Network built at: {network_dir}")
                print()

                # Run test
                result = self.runner.run_entity_test(
                    network_dir=network_dir,
                    config=config,
                    duration=test_duration,
                    partition_mode="dynamic"
                )

                # Record result
                batch_results['results'].append(result)

                if result['status'] == 'success':
                    batch_results['summary']['completed'] += 1
                elif result['status'] == 'failed':
                    batch_results['summary']['failed'] += 1
                else:
                    batch_results['summary']['errors'] += 1

                # Cleanup network before next test
                print("\nCleaning up network...")
                self.runner.cleanup_network()

                test_elapsed = time.time() - test_start
                print(f"\n✓ Test {i+1} complete in {test_elapsed/60:.1f} minutes")
                print(f"  Status: {result['status']}")

                # Save incremental results
                self._save_batch_results(batch_results)

                # Pause between tests
                if i < len(configs) - 1:
                    pause_time = 30
                    print(f"\nPausing {pause_time}s before next test...")
                    time.sleep(pause_time)

            except Exception as e:
                print(f"\n✗ Test {i+1} failed with error: {e}")
                import traceback
                traceback.print_exc()

                batch_results['results'].append({
                    'config_id': config.config_id,
                    'status': 'error',
                    'error': str(e)
                })
                batch_results['summary']['errors'] += 1

                # Save results even after error
                self._save_batch_results(batch_results)

                # Try to cleanup anyway
                try:
                    self.runner.cleanup_network()
                except:
                    pass

        # Final summary
        print("\n" + "=" * 80)
        print("PHASE 1 BATCH COMPLETE")
        print("=" * 80)
        print(f"Total tests: {batch_results['summary']['total']}")
        print(f"Completed: {batch_results['summary']['completed']}")
        print(f"Failed: {batch_results['summary']['failed']}")
        print(f"Errors: {batch_results['summary']['errors']}")
        print()
        print(f"Results saved to: {self.output_dir / 'phase1_batch_results.json'}")
        print("=" * 80)

        return batch_results

    def _save_config_specs(self, configs: List):
        """Save configuration specifications to JSON"""

        specs = []
        for config in configs:
            summary = config.summary()
            specs.append(summary)

        output_file = self.output_dir / 'phase1_config_specifications.json'

        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'count': len(specs),
                'specifications': specs
            }, f, indent=2)

        print(f"✓ Configuration specs saved to: {output_file}")

    def _save_batch_results(self, batch_results: Dict):
        """Save batch results to JSON (incremental saves)"""

        output_file = self.output_dir / 'phase1_batch_results.json'

        with open(output_file, 'w') as f:
            json.dump(batch_results, f, indent=2)

    def generate_summary_report(self, batch_results: Dict = None) -> str:
        """Generate human-readable summary report"""

        if batch_results is None:
            # Load from file
            results_file = self.output_dir / 'phase1_batch_results.json'
            if not results_file.exists():
                return "No batch results found"

            with open(results_file, 'r') as f:
                batch_results = json.load(f)

        report = []
        report.append("=" * 80)
        report.append("PHASE 1 COARSE SEARCH - SUMMARY REPORT")
        report.append("=" * 80)
        report.append("")

        # Summary stats
        summary = batch_results['summary']
        report.append(f"Total tests: {summary['total']}")
        report.append(f"Completed: {summary['completed']}")
        report.append(f"Failed: {summary['failed']}")
        report.append(f"Errors: {summary['errors']}")
        report.append(f"Success rate: {summary['completed'] / summary['total'] * 100:.1f}%")
        report.append("")

        # Results by configuration
        report.append("=" * 80)
        report.append("RESULTS BY CONFIGURATION")
        report.append("=" * 80)
        report.append("")

        for i, result in enumerate(batch_results.get('results', []), 1):
            config_id = result.get('config_id', f'test-{i}')
            status = result.get('status', 'unknown')

            report.append(f"{i}. {config_id}: {status.upper()}")

            if status == 'success':
                splits = result.get('splits', {})
                econ = splits.get('economic', {})
                hashrate = splits.get('hashrate', {})
                heights = result.get('final_heights', {})
                fork_depth = result.get('fork_depth', 0)

                report.append(f"   Economic: v27={econ.get('v27', 'N/A'):.1f}%, v26={econ.get('v26', 'N/A'):.1f}%")
                report.append(f"   Hashrate: v27={hashrate.get('v27', 'N/A'):.1f}%, v26={hashrate.get('v26', 'N/A'):.1f}%")
                report.append(f"   Final heights: v27={heights.get('v27', 'N/A')}, v26={heights.get('v26', 'N/A')}")
                report.append(f"   Fork depth: {fork_depth} blocks")
            elif 'error' in result:
                report.append(f"   Error: {result['error']}")

            report.append("")

        # Save report
        report_text = "\n".join(report)
        report_file = self.output_dir / 'PHASE1_SUMMARY_REPORT.txt'

        with open(report_file, 'w') as f:
            f.write(report_text)

        print(f"✓ Summary report saved to: {report_file}")

        return report_text


# Main execution
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Run Phase 1 entity-based fork test batch')
    parser.add_argument('--samples', type=int, default=50, help='Number of test samples (default: 50)')
    parser.add_argument('--duration', type=int, default=1800, help='Test duration in seconds (default: 1800 = 30min)')
    parser.add_argument('--start-from', type=int, default=0, help='Start from test N (for resuming)')
    parser.add_argument('--dry-run', action='store_true', help='Generate configs only, do not run tests')
    parser.add_argument('--report-only', action='store_true', help='Generate summary report from existing results')

    args = parser.parse_args()

    print("=" * 80)
    print("PHASE 1 BATCH RUNNER")
    print("=" * 80)
    print()

    if args.report_only:
        # Just generate report from existing results
        print("Generating summary report from existing results...")
        batch_runner = Phase1BatchRunner(entity_db=None)
        report = batch_runner.generate_summary_report()
        print("\n" + report)
        sys.exit(0)

    # Load entity database
    db_path = Path(__file__).parent / 'entity_database.json'

    if not db_path.exists():
        print("ERROR: entity_database.json not found")
        print(f"Expected at: {db_path}")
        print("\nPlease run first:")
        print("  cd /home/pfoytik/bitcoinTools/warnet/warnet_entity_distribution")
        print("  python3 entity_database.py")
        sys.exit(1)

    print("Loading entity database...")
    db = EntityDatabase.load(str(db_path))
    print(f"✓ Loaded entity database")
    print(f"  Exchanges: {len(db.exchanges)}")
    print(f"  Mining pools: {len(db.mining_pools)}")
    print(f"  Users: {len(db.users)}")
    print()

    # Create batch runner
    batch_runner = Phase1BatchRunner(entity_db=db)

    # Run batch
    print("Starting Phase 1 batch run...")
    print()

    batch_results = batch_runner.run_phase1_batch(
        n_samples=args.samples,
        test_duration=args.duration,
        start_from=args.start_from,
        dry_run=args.dry_run
    )

    # Generate summary report
    if not args.dry_run:
        print("\nGenerating summary report...")
        report = batch_runner.generate_summary_report(batch_results)
        print("\n" + report)

    print("\n✓ Phase 1 batch complete!")
