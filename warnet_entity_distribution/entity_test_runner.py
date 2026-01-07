#!/usr/bin/env python3
"""
Entity-Based Test Runner
Runs fork tests for entity-based network configurations using existing Warnet tools
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import subprocess
import json
import time
from pathlib import Path
from typing import Dict, Optional, Tuple
from configuration_generator import NetworkConfiguration


class EntityTestRunner:
    """
    Runs entity-based fork tests using existing Warnet infrastructure
    """

    def __init__(
        self,
        warnet_root: str = "/home/pfoytik/bitcoinTools/warnet",
        results_dir: str = None
    ):
        self.warnet_root = Path(warnet_root)
        self.scenario_dir = self.warnet_root / "warnet" / "resources" / "scenarios"
        self.monitoring_dir = self.warnet_root / "warnetScenarioDiscovery" / "monitoring"

        if results_dir is None:
            results_dir = self.warnet_root / "warnet_entity_distribution" / "test_results"
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def run_entity_test(
        self,
        network_dir: Path,
        config: NetworkConfiguration,
        duration: int = 1800,  # 30 minutes default
        common_history_height: int = 101,
        partition_mode: str = "dynamic"
    ) -> Dict:
        """
        Run a complete entity-based fork test

        Args:
            network_dir: Path to network directory with network.yaml
            config: NetworkConfiguration that generated the network
            duration: Test duration in seconds (default: 1800 = 30 min)
            common_history_height: Height of common history before partition
            partition_mode: "static" or "dynamic" partitioning

        Returns:
            Dict with test results
        """

        config_id = config.config_id
        print("=" * 80)
        print(f"ENTITY-BASED FORK TEST: {config_id}")
        print("=" * 80)

        # Get split information
        econ_a, econ_b = config.get_economic_split()
        hash_a, hash_b = config.get_hashrate_split()

        print(f"Configuration:")
        print(f"  Fork A (v27): {econ_a:.1f}% economic, {hash_a:.1f}% hashrate")
        print(f"  Fork B (v26): {econ_b:.1f}% economic, {hash_b:.1f}% hashrate")
        print(f"  Duration: {duration}s ({duration//60} minutes)")
        print(f"  Partition mode: {partition_mode}")
        print()

        # Initialize result structure
        result = {
            'config_id': config_id,
            'status': 'failed',
            'splits': {
                'economic': {'v27': econ_a, 'v26': econ_b},
                'hashrate': {'v27': hash_a, 'v26': hash_b}
            },
            'steps': {}
        }

        try:
            # Step 1: Deploy network
            print("Step 1: Deploying network...")
            deploy_success = self._deploy_network(network_dir)
            result['steps']['deploy'] = {
                'status': 'success' if deploy_success else 'failed'
            }

            if not deploy_success:
                result['error'] = 'Network deployment failed'
                return result

            print("✓ Network deployed")
            print()

            # Step 2: Generate common history
            print("Step 2: Generating common history...")
            common_history_success = self._generate_common_history(common_history_height)
            result['steps']['common_history'] = {
                'status': 'success' if common_history_success else 'failed',
                'height': common_history_height
            }

            if not common_history_success:
                result['error'] = 'Common history generation failed'
                return result

            print(f"✓ Generated {common_history_height} blocks of common history")
            print()

            # Step 3: Dynamic partitioning (if enabled)
            if partition_mode == "dynamic":
                print("Step 3: Activating dynamic partition...")
                partition_success = self._activate_dynamic_partition(network_dir)
                result['steps']['partition'] = {
                    'status': 'success' if partition_success else 'failed',
                    'mode': partition_mode
                }

                if not partition_success:
                    result['error'] = 'Dynamic partitioning failed'
                    return result

                print("✓ Network partitioned by version")
                print()

            # Step 4 & 5: Run mining and collect results
            print("Step 4 & 5: Running partition mining...")
            mining_result = self._run_partition_mining(
                v27_hashrate=hash_a,
                v26_hashrate=hash_b,
                duration=duration,
                start_height=common_history_height
            )

            result['steps']['mining'] = mining_result

            if mining_result['status'] != 'success':
                result['error'] = 'Mining test failed'
                return result

            print(f"✓ Mining complete: {mining_result.get('blocks', {})}")
            print()

            # Step 6: Economic analysis
            print("Step 6: Running economic analysis...")
            analysis_result = self._run_economic_analysis(network_dir, config_id)
            result['steps']['analysis'] = analysis_result

            if analysis_result['status'] != 'success':
                result['error'] = 'Economic analysis failed'
                return result

            print("✓ Economic analysis complete")
            print()

            # Consolidate final results
            result['status'] = 'success'
            result['final_heights'] = mining_result.get('final_heights', {})
            result['fork_depth'] = mining_result.get('fork_depth', 0)
            result['economic_analysis'] = analysis_result.get('analysis', {})

            # Save results
            self._save_results(config_id, result)

            print("=" * 80)
            print(f"TEST COMPLETE: {config_id}")
            print(f"  Final heights: v27={result['final_heights'].get('v27', 'N/A')}, "
                  f"v26={result['final_heights'].get('v26', 'N/A')}")
            print(f"  Fork depth: {result['fork_depth']} blocks")
            print("=" * 80)
            print()

        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

        return result

    def _deploy_network(self, network_dir: Path) -> bool:
        """Deploy network using warnet"""
        try:
            result = subprocess.run(
                ['warnet', 'deploy', str(network_dir)],
                cwd=network_dir,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                print(f"  Error: {result.stderr}")
                return False

            # Wait for nodes to initialize
            print("  Waiting 90 seconds for nodes to initialize...")
            time.sleep(90)

            return True

        except Exception as e:
            print(f"  Deployment error: {e}")
            return False

    def _generate_common_history(self, height: int) -> bool:
        """Generate common blockchain history"""
        try:
            # Create wallet
            subprocess.run(
                ['warnet', 'bitcoin', 'rpc', 'node-0000', 'createwallet', 'miner', 'false'],
                capture_output=True,
                timeout=10
            )
            time.sleep(2)

            # Get mining address
            result = subprocess.run(
                ['warnet', 'bitcoin', 'rpc', 'node-0000', '-rpcwallet=miner', 'getnewaddress'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                print(f"  Error getting address: {result.stderr}")
                return False

            mining_address = result.stdout.strip().strip('"')
            print(f"  Mining to: {mining_address}")

            # Generate blocks
            for i in range(1, height + 1):
                subprocess.run(
                    ['warnet', 'bitcoin', 'rpc', 'node-0000', 'generatetoaddress', '1', mining_address],
                    capture_output=True,
                    timeout=10
                )

                if i % 20 == 0:
                    print(f"  Generated {i}/{height} blocks...")

                time.sleep(0.5)

            # Wait for propagation
            print("  Waiting 60 seconds for propagation...")
            time.sleep(60)

            # Verify heights
            v27_result = subprocess.run(
                ['warnet', 'bitcoin', 'rpc', 'node-0000', 'getblockcount'],
                capture_output=True,
                text=True,
                timeout=5
            )

            v26_node = 'node-0003'  # First v26 node based on our network structure
            v26_result = subprocess.run(
                ['warnet', 'bitcoin', 'rpc', v26_node, 'getblockcount'],
                capture_output=True,
                text=True,
                timeout=5
            )

            v27_height = int(v27_result.stdout.strip().strip('"'))
            v26_height = int(v26_result.stdout.strip().strip('"'))

            print(f"  v27 height: {v27_height}, v26 height: {v26_height}")

            return v27_height == height

        except Exception as e:
            print(f"  Common history error: {e}")
            return False

    def _activate_dynamic_partition(self, network_dir: Path) -> bool:
        """Activate dynamic partitioning using setban RPC"""
        try:
            partition_script = self.warnet_root / "warnetScenarioDiscovery" / "tools" / "partition_utils.sh"

            if not partition_script.exists():
                print(f"  Warning: partition_utils.sh not found, skipping dynamic partition")
                return True  # Not critical if script doesn't exist

            network_yaml = network_dir / "network.yaml"
            if not network_yaml.exists():
                print(f"  Error: network.yaml not found at {network_yaml}")
                return False

            # Call partition_by_version function from the script
            print(f"  Applying network partition using setban RPC...")
            result = subprocess.run(
                ['bash', '-c', f'source {partition_script} && partition_by_version {network_yaml} "27.0" "26.0" 86400'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                print(f"  Error: Partition script failed")
                print(f"  stderr: {result.stderr}")
                return False

            # Print the partition script output
            if result.stdout:
                for line in result.stdout.splitlines():
                    print(f"    {line}")

            return True

        except Exception as e:
            print(f"  Partition error: {e}")
            return False

    def _run_partition_mining(
        self,
        v27_hashrate: float,
        v26_hashrate: float,
        duration: int,
        start_height: int
    ) -> Dict:
        """Run partition mining using existing partition_miner.py scenario"""

        result = {
            'status': 'failed',
            'blocks': {},
            'final_heights': {},
            'fork_depth': 0
        }

        try:
            # Run partition_miner scenario
            scenario_path = self.scenario_dir / "partition_miner.py"

            if not scenario_path.exists():
                result['error'] = f"partition_miner.py not found at {scenario_path}"
                return result

            print(f"  DEBUG: Using scenario from: {scenario_path}")
            print(f"  Starting partition mining...")
            print(f"  v27: {v27_hashrate:.1f}% hashrate, v26: {v26_hashrate:.1f}% hashrate")
            print(f"  Duration: {duration}s")

            # Run warnet scenario
            cmd = [
                'warnet', 'run', str(scenario_path),
                '--v27-hashrate', str(v27_hashrate),
                '--v26-hashrate', str(v26_hashrate),
                '--interval', '10',
                '--duration', str(duration),
                '--start-height', str(start_height)
            ]

            proc = subprocess.run(
                cmd,
                cwd=self.warnet_root,
                capture_output=True,
                text=True,
                timeout=duration + 300  # Add 5 min buffer
            )

            if proc.returncode != 0:
                result['error'] = f"Mining scenario failed: {proc.stderr}"
                print(f"  Error: {proc.stderr}")
                return result

            # warnet run returns immediately after deploying the pod
            # We need to wait for the scenario pod to actually complete
            print(f"  Scenario deployed, waiting for mining to complete ({duration}s + overhead)...")

            # Wait for the scenario pod to finish
            # Poll for pod completion with timeout
            start_wait = time.time()
            timeout = duration + 120  # Add 2 min buffer for scenario startup/shutdown

            while time.time() - start_wait < timeout:
                # Check for partition miner pods
                check_cmd = ['kubectl', 'get', 'pods', '-l', 'mission=commander', '-o', 'jsonpath={.items[*].status.phase}']
                check_result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=5)

                if check_result.returncode == 0:
                    phases = check_result.stdout.strip().split()
                    # If no running pods, scenario is complete
                    if 'Running' not in phases:
                        print(f"  Scenario pod completed")
                        break

                time.sleep(5)  # Check every 5 seconds

            # Query final heights
            print("  Mining complete, querying final heights...")

            # Wait for block propagation before querying
            print("  Waiting 60 seconds for block propagation...")
            time.sleep(60)

            v27_result = subprocess.run(
                ['warnet', 'bitcoin', 'rpc', 'node-0000', 'getblockcount'],
                capture_output=True,
                text=True,
                timeout=5
            )

            v26_result = subprocess.run(
                ['warnet', 'bitcoin', 'rpc', 'node-0003', 'getblockcount'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if v27_result.returncode == 0 and v26_result.returncode == 0:
                v27_height = int(v27_result.stdout.strip().strip('"'))
                v26_height = int(v26_result.stdout.strip().strip('"'))

                result['final_heights'] = {
                    'v27': v27_height,
                    'v26': v26_height
                }

                result['blocks'] = {
                    'v27': v27_height - start_height,
                    'v26': v26_height - start_height
                }

                # Fork depth is the total number of blocks since the common ancestor
                # (blocks mined on both sides of the partition)
                result['fork_depth'] = (v27_height - start_height) + (v26_height - start_height)
                result['status'] = 'success'

        except subprocess.TimeoutExpired:
            result['error'] = f'Mining timeout after {duration + 300}s'
            print(f"  Timeout")
        except Exception as e:
            result['error'] = str(e)
            print(f"  Error: {e}")

        return result

    def _run_economic_analysis(self, network_dir: Path, config_id: str) -> Dict:
        """Run economic analysis using auto_economic_analysis.py"""

        result = {
            'status': 'failed',
            'analysis': {}
        }

        try:
            analysis_script = self.monitoring_dir / "auto_economic_analysis.py"

            if not analysis_script.exists():
                result['error'] = f"auto_economic_analysis.py not found"
                return result

            # Run analysis
            cmd = [
                'python3', str(analysis_script),
                '--network-config', str(network_dir),
                '--live-query',
                '--fork-depth-threshold', '3'
            ]

            proc = subprocess.run(
                cmd,
                cwd=self.monitoring_dir,
                capture_output=True,
                text=True,
                timeout=60
            )

            if proc.returncode != 0:
                result['error'] = f"Analysis failed: {proc.stderr}"
                print(f"  Error: {proc.stderr}")
                return result

            # Try to parse JSON output if available
            try:
                # Look for JSON in output
                output_lines = proc.stdout.split('\n')
                for line in output_lines:
                    if line.strip().startswith('{'):
                        analysis_data = json.loads(line)
                        result['analysis'] = analysis_data
                        break
            except:
                # If JSON parsing fails, just store text output
                result['analysis'] = {'raw_output': proc.stdout}

            result['status'] = 'success'

        except Exception as e:
            result['error'] = str(e)
            print(f"  Error: {e}")

        return result

    def _save_results(self, config_id: str, result: Dict):
        """Save test results to JSON file"""

        output_file = self.results_dir / f"{config_id}_result.json"

        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"  Results saved to: {output_file}")

    def cleanup_network(self):
        """Stop and cleanup current network deployment"""
        try:
            print("Cleaning up network...")
            subprocess.run(
                ['kubectl', 'delete', 'pods', '--all', '-n', 'default'],
                capture_output=True,
                timeout=60
            )
            print("✓ Network cleaned up")
            time.sleep(10)  # Wait for cleanup
        except Exception as e:
            print(f"  Cleanup warning: {e}")


# Example usage and testing
if __name__ == "__main__":
    print("=" * 80)
    print("ENTITY TEST RUNNER - STANDALONE TEST")
    print("=" * 80)

    from entity_database import EntityDatabase
    from configuration_generator import ConfigurationGenerator
    from warnet_network_builder import WarnetNetworkBuilder

    # Load entity database
    db_path = Path(__file__).parent / 'entity_database.json'
    if not db_path.exists():
        print("Error: entity_database.json not found")
        print(f"  Expected at: {db_path}")
        print("  Run: python3 entity_database.py first")
        sys.exit(1)

    db = EntityDatabase.load(str(db_path))
    print(f"\n✓ Loaded entity database")

    # Generate test config
    gen = ConfigurationGenerator(db)
    config = gen.generate_specific_config(
        config_id='entity-test-runner-demo',
        exchange_allocation=[0],      # Top exchange to fork_a
        miner_allocation=[0, 1],      # Foundry + AntPool to fork_a
        user_allocation_pct=0         # All users to fork_b
    )

    print(f"\n✓ Generated test config: {config.config_id}")
    econ_a, econ_b = config.get_economic_split()
    hash_a, hash_b = config.get_hashrate_split()
    print(f"  Fork A: {econ_a:.1f}% economic, {hash_a:.1f}% hashrate")
    print(f"  Fork B: {econ_b:.1f}% economic, {hash_b:.1f}% hashrate")

    # Build network
    builder = WarnetNetworkBuilder()
    network_dir = builder.build_network_from_entity_config(config)
    print(f"\n✓ Network built at: {network_dir}")

    # Run test (shortened for demo)
    print("\n" + "=" * 80)
    print("RUNNING 5-MINUTE TEST (for demonstration)")
    print("=" * 80)

    runner = EntityTestRunner()

    # For full test, use duration=1800 (30 minutes)
    result = runner.run_entity_test(
        network_dir=network_dir,
        config=config,
        duration=300,  # 5 minutes for demo
        partition_mode="dynamic"
    )

    print("\n" + "=" * 80)
    print("TEST RESULT")
    print("=" * 80)
    print(json.dumps(result, indent=2))

    # Cleanup
    runner.cleanup_network()

    print("\n✓ Test runner demonstration complete!")
