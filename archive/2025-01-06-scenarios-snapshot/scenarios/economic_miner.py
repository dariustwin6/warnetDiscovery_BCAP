#!/usr/bin/env python3

"""
Economic Mining Scenario for Bitcoin Fork Testing

This scenario simulates realistic pool-based mining where:
1. Mining pools generate blocks based on real-world hashrate distribution
2. Pools choose which fork to mine based on economic signals from connected nodes
3. Economic nodes (exchanges, payment processors) influence pool decisions

Pool distribution based on real Bitcoin network data (1-month sample).
"""

from time import sleep, time
from random import random, choices
import logging

from commander import Commander


# Real-world mining pool distribution (1-month Bitcoin network data)
POOL_DISTRIBUTION = [
    ("Foundry USA", 26.89),
    ("AntPool", 19.25),
    ("ViaBTC", 11.39),
    ("F2Pool", 11.25),
    ("SpiderPool", 9.09),
    ("MARA Pool", 5.00),
    ("SECPOOL", 4.18),
    ("Luxor", 3.21),
    ("Binance Pool", 2.49),
    ("OCEAN", 1.42),
    ("SBI Crypto", 1.26),
    ("Braiins Pool", 1.07),
    ("WhitePool", 0.74),
    ("Mining Squared", 0.74),
    ("BTC.com", 0.44),
    ("Poolin", 0.40),
    ("luckyPool", 0.37),
    ("Innopolis Tech", 0.26),
    ("Unknown", 0.21),
    ("ULTIMUSPOOL", 0.21),
    ("NiceHash", 0.07),
    ("Solo CK", 0.05),
    ("Public Pool", 0.02),
]


class MiningPool:
    """Represents a mining pool with realistic hashrate and fork choice logic"""

    def __init__(self, name, hashrate_percent, connected_nodes, logger, commander):
        self.name = name
        self.hashrate = hashrate_percent / 100.0  # Convert to probability
        self.connected_nodes = connected_nodes  # List of economic nodes this pool listens to
        self.logger = logger
        self.commander = commander  # Commander instance for mining
        self.blocks_mined = 0
        self.wallet = None
        self.addr = None

    def initialize_wallet(self, node):
        """Initialize wallet on the first connected node"""
        if not self.wallet:
            self.wallet = Commander.ensure_miner(node)
            self.addr = self.wallet.getnewaddress()

    def choose_mining_target(self):
        """
        Decide which fork to mine based on economic signals from connected nodes.

        In a fork scenario:
        - Pools query their connected economic nodes
        - Choose the fork that their connected nodes are on
        - If nodes are split, choose based on economic weight
        """
        fork_info = {}

        for node in self.connected_nodes:
            try:
                best_hash = node.getbestblockhash()
                height = node.getblockcount()

                if best_hash not in fork_info:
                    fork_info[best_hash] = {
                        'nodes': [],
                        'height': height,
                        'node_obj': node
                    }
                fork_info[best_hash]['nodes'].append(node)
            except Exception as e:
                self.logger.warning(f"Pool {self.name}: Error querying node {node.index}: {e}")

        if not fork_info:
            return None

        # If single chain, mine on it
        if len(fork_info) == 1:
            return list(fork_info.values())[0]['node_obj']

        # Fork detected - choose based on number of connected nodes on each fork
        # (simulating economic influence - more connections = more economic pressure)
        best_fork = max(fork_info.values(), key=lambda x: len(x['nodes']))

        self.logger.info(
            f"Pool {self.name}: Fork detected! "
            f"{len(fork_info)} chains. Mining on fork with {len(best_fork['nodes'])} connected nodes"
        )

        return best_fork['node_obj']

    def attempt_mine(self):
        """
        Attempt to mine a block based on pool's hashrate.
        Returns True if block was mined, False otherwise.
        """
        # Probability-based mining: higher hashrate = higher chance
        if random() < self.hashrate:
            target_node = self.choose_mining_target()

            if target_node:
                try:
                    # Initialize wallet if needed
                    self.initialize_wallet(target_node)

                    # Mine one block using Commander's method
                    self.commander.generatetoaddress(target_node, 1, self.addr, sync_fun=self.commander.no_op)
                    height = target_node.getblockcount()
                    self.blocks_mined += 1

                    self.logger.info(
                        f"⛏  Pool {self.name} mined block #{height} "
                        f"on node-{target_node.index:04d} (total: {self.blocks_mined})"
                    )
                    return True
                except Exception as e:
                    self.logger.error(f"Pool {self.name}: Mining error: {e}")

        return False


class EconomicMiner(Commander):
    """
    Economic Mining Scenario

    Simulates realistic pool-based mining with economic node influence.
    """

    def set_test_params(self):
        self.num_nodes = 0
        self.pools = []
        self.mining_interval = 10  # Average time between mining attempts (seconds)
        self.pool_count = 10  # Number of top pools to simulate

    def add_options(self, parser):
        parser.description = "Economic mining scenario with realistic pool distribution"
        parser.usage = "warnet run /path/to/economic_miner.py [options]"

        parser.add_argument(
            "--interval",
            dest="interval",
            default=10,
            type=int,
            help="Average seconds between mining attempts across all pools (default: 10)",
        )

        parser.add_argument(
            "--pools",
            dest="pool_count",
            default=10,
            type=int,
            help="Number of top mining pools to simulate (default: 10, max: 23)",
        )

        parser.add_argument(
            "--duration",
            dest="duration",
            default=0,
            type=int,
            help="Duration to run in seconds (0 = run indefinitely)",
        )

        parser.add_argument(
            "--mature",
            dest="mature",
            action="store_true",
            help="Generate 101 mature blocks at startup on node-0000",
        )

    def setup_pools(self):
        """
        Initialize mining pools with realistic hashrate distribution.
        Connect pools to economic nodes based on network metadata or random distribution.
        """
        self.log.info("=" * 80)
        self.log.info("ECONOMIC MINING SCENARIO - Pool-Based Bitcoin Mining Simulation")
        self.log.info("=" * 80)

        # Try to find pool nodes with metadata in the network
        pool_nodes_with_metadata = []
        for node in self.nodes:
            # Check if node has pool metadata
            if hasattr(node, 'metadata') and isinstance(node.metadata, dict):
                if 'pool_name' in node.metadata and 'hashrate_pct' in node.metadata:
                    pool_nodes_with_metadata.append(node)

        # If we have pool nodes with metadata, use them
        if pool_nodes_with_metadata:
            self.log.info(f"Found {len(pool_nodes_with_metadata)} pool nodes with metadata in network config")
            self._setup_pools_from_metadata(pool_nodes_with_metadata)
        else:
            # Fallback to random distribution
            self.log.info("No pool metadata found, using random connection distribution")
            self._setup_pools_random()

        self.log.info("=" * 80)

    def _setup_pools_from_metadata(self, pool_nodes):
        """Setup pools using metadata from network configuration"""
        self.log.info("Setting up pools from network metadata:")

        for pool_node in pool_nodes:
            metadata = pool_node.metadata
            pool_name = metadata['pool_name']
            hashrate = metadata['hashrate_pct']

            self.log.info(f"  - {pool_name}: {hashrate:.2f}% hashrate")

            # Get connected nodes from metadata
            connected_node_indices = metadata.get('connected_to', [])

            if connected_node_indices:
                # Map indices to actual node objects
                connected_nodes = []
                for idx in connected_node_indices:
                    # Find node with this index
                    for node in self.nodes:
                        if node.index == idx:
                            connected_nodes.append(node)
                            break

                if not connected_nodes:
                    self.log.warning(f"Pool {pool_name}: No valid connected nodes found, using all nodes")
                    connected_nodes = self.nodes
            else:
                # No specific connections, connect to all nodes
                self.log.info(f"Pool {pool_name}: No specific connections, using all nodes")
                connected_nodes = self.nodes

            pool = MiningPool(pool_name, hashrate, connected_nodes, self.log, self)
            self.pools.append(pool)

            self.log.info(
                f"  Pool {pool_name} connected to {len(connected_nodes)} nodes: "
                f"{[f'node-{n.index:04d}' for n in connected_nodes[:5]]}{'...' if len(connected_nodes) > 5 else ''}"
            )

    def _setup_pools_random(self):
        """Setup pools with random connections (fallback/legacy behavior)"""
        # Determine pool count
        pool_count = min(self.options.pool_count, len(POOL_DISTRIBUTION))

        # Get top N pools
        pools_to_simulate = POOL_DISTRIBUTION[:pool_count]

        self.log.info(f"Simulating {pool_count} mining pools (random distribution):")
        for name, hashrate in pools_to_simulate:
            self.log.info(f"  - {name}: {hashrate:.2f}% hashrate")

        # Distribute node connections across pools
        # Each pool connects to subset of nodes (simulating their customer/partner relationships)
        num_nodes = len(self.nodes)

        for pool_name, hashrate in pools_to_simulate:
            # Each pool connects to 30-70% of nodes (random distribution)
            connection_ratio = 0.3 + random() * 0.4
            num_connections = max(1, int(num_nodes * connection_ratio))

            # Randomly select nodes for this pool
            import random as rand
            connected_nodes = rand.sample(self.nodes, num_connections)

            pool = MiningPool(pool_name, hashrate, connected_nodes, self.log, self)
            self.pools.append(pool)

            self.log.info(
                f"Pool {pool_name} connected to {num_connections} nodes: "
                f"{[f'node-{n.index:04d}' for n in connected_nodes[:3]]}..."
            )

    def run_test(self):
        """Run the economic mining scenario"""

        # Mature blocks if requested
        if self.options.mature:
            self.log.info("Generating 101 mature blocks on node-0000...")
            wallet = Commander.ensure_miner(self.nodes[0])
            addr = wallet.getnewaddress()
            self.generatetoaddress(self.nodes[0], 101, addr, sync_fun=self.no_op)
            self.log.info(f"Mature blocks generated. Height: {self.nodes[0].getblockcount()}")

        # Setup mining pools
        self.setup_pools()

        # Mining loop
        start_time = time()
        iteration = 0
        total_blocks = 0

        self.log.info("Starting economic mining simulation...")
        self.log.info(f"Mining interval: {self.options.interval}s between attempts")

        if self.options.duration > 0:
            self.log.info(f"Will run for {self.options.duration} seconds")
        else:
            self.log.info("Running indefinitely (Ctrl+C to stop)")

        self.log.info("=" * 80)

        try:
            while True:
                iteration += 1

                # Check duration limit
                if self.options.duration > 0:
                    elapsed = time() - start_time
                    if elapsed >= self.options.duration:
                        self.log.info(f"Duration limit reached ({self.options.duration}s). Stopping.")
                        break

                # Each iteration, all pools attempt to mine
                blocks_this_round = 0
                for pool in self.pools:
                    if pool.attempt_mine():
                        blocks_this_round += 1
                        total_blocks += 1

                # Log summary periodically
                if iteration % 10 == 0:
                    elapsed = time() - start_time
                    blocks_per_min = (total_blocks / elapsed) * 60 if elapsed > 0 else 0
                    self.log.info(
                        f"[{iteration} iterations, {elapsed:.0f}s elapsed] "
                        f"Total blocks: {total_blocks}, Rate: {blocks_per_min:.2f} blocks/min"
                    )

                # Sleep between mining attempts
                sleep(self.options.interval)

        except KeyboardInterrupt:
            self.log.info("\nMining stopped by user")

        # Final statistics
        elapsed = time() - start_time
        self.log.info("=" * 80)
        self.log.info("MINING STATISTICS")
        self.log.info("=" * 80)
        self.log.info(f"Total runtime: {elapsed:.1f}s")
        self.log.info(f"Total blocks mined: {total_blocks}")
        self.log.info(f"Average rate: {(total_blocks / elapsed * 60):.2f} blocks/min")
        self.log.info("\nBlocks per pool:")
        for pool in self.pools:
            percentage = (pool.blocks_mined / total_blocks * 100) if total_blocks > 0 else 0
            self.log.info(f"  {pool.name}: {pool.blocks_mined} blocks ({percentage:.1f}%)")
        self.log.info("=" * 80)


def main():
    EconomicMiner().main()


if __name__ == "__main__":
    main()
