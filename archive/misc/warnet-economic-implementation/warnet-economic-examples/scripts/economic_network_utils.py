#!/usr/bin/env python3
"""
Economic Node Network Generator and Analyzer for Warnet

This script helps generate Warnet network configurations with Economic Nodes
and provides analysis utilities for testing BCAP scenarios.

Usage:
    # Generate network
    python economic_network_utils.py generate --nodes 100 --output my_network.yaml
    
    # Analyze existing network
    python economic_network_utils.py analyze --config network.yaml
    
    # Calculate metrics
    python economic_network_utils.py metrics --config network.yaml
"""

import yaml
import random
import argparse
from typing import List, Dict, Tuple
from collections import defaultdict


class EconomicNode:
    """
    Represents an Economic Node configuration aligned with BCAP framework.

    BCAP Definition:
    "Economic Nodes are full nodes that not only validate and relay transactions,
     but also receive and send substantial amounts of bitcoin payments. Economic
     Nodes have power and influence which is proportional to the frequency and
     volume of payments received."

    Economic power is measured by:
    - PRIMARY: Custody (% of BTC supply under validation)
    - SECONDARY: Payment volume (daily transaction flow)
    """

    # Node type configurations (BCAP-aligned)
    TYPES = {
        'major_exchange': {
            'consensus_weight': 10.3,
            'custody_btc': 2000000,
            'supply_percentage': 10.3,
            'daily_volume_btc': 100000,
            'connections': 2000,
            'mempool': 10000,
            'cpu': '8000m',
            'memory': '32Gi',
            'entity_type': 'major_exchange',
            'adoption_speed': 'fast',
        },
        'regional_exchange': {
            'consensus_weight': 2.3,
            'custody_btc': 450000,
            'supply_percentage': 2.3,
            'daily_volume_btc': 30000,
            'connections': 1000,
            'mempool': 5000,
            'cpu': '4000m',
            'memory': '16Gi',
            'entity_type': 'regional_exchange',
            'adoption_speed': 'medium',
        },
        'payment_processor': {
            'consensus_weight': 1.0,
            'custody_btc': 30000,
            'supply_percentage': 0.15,
            'daily_volume_btc': 10000,
            'connections': 500,
            'mempool': 2000,
            'cpu': '4000m',
            'memory': '8Gi',
            'entity_type': 'payment_processor',
            'adoption_speed': 'medium',
        },
        'custody_provider': {
            'consensus_weight': 3.6,
            'custody_btc': 700000,
            'supply_percentage': 3.6,
            'daily_volume_btc': 3000,
            'connections': 300,
            'mempool': 3000,
            'cpu': '2000m',
            'memory': '12Gi',
            'entity_type': 'custody_provider',
            'adoption_speed': 'slow',
        },
    }

    def __init__(self, name: str, node_type: str, version: str = "27.0",
                 custody_btc: int = None, daily_volume_btc: int = None):
        """
        Initialize an Economic Node.

        Args:
            name: Node identifier
            node_type: One of 'major_exchange', 'regional_exchange', 'payment_processor', 'custody_provider'
            version: Bitcoin Core version (default "27.0")
            custody_btc: Optional override for BTC in custody
            daily_volume_btc: Optional override for daily payment volume
        """
        self.name = name
        self.node_type = node_type
        self.version = version
        self.config = self.TYPES[node_type].copy()

        # Allow custom custody and volume overrides
        if custody_btc is not None:
            self.config['custody_btc'] = custody_btc
            # Recalculate supply percentage assuming 19.5M circulating
            self.config['supply_percentage'] = round(custody_btc / 19_500_000 * 100, 2)
            self.config['consensus_weight'] = self.config['supply_percentage']

        if daily_volume_btc is not None:
            self.config['daily_volume_btc'] = daily_volume_btc
    
    def to_dict(self) -> Dict:
        """Convert to Warnet YAML structure with BCAP-aligned metrics."""
        # Determine tags based on entity type
        tags = ['economic_node', self.node_type]
        if 'exchange' in self.node_type:
            tags.extend(['exchange', 'high_volume'])
        elif self.node_type == 'payment_processor':
            tags.extend(['medium_volume', 'operational_chokepoint'])
        elif self.node_type == 'custody_provider':
            tags.extend(['high_security', 'institutional'])

        # Calculate daily deposits/withdrawals (assume 95% withdrawal ratio)
        daily_volume = self.config['daily_volume_btc']
        daily_deposits = daily_volume
        daily_withdrawals = int(daily_volume * 0.95)

        return {
            'name': self.name,
            'image': f"bitcoindevproject/bitcoin:{self.version}",
            'tags': tags,
            'metadata': {
                'node_type': self.config['entity_type'],
                'entity_name': f"{self.node_type.replace('_', ' ').title()}",
                'adoption_speed': self.config['adoption_speed'],

                # PRIMARY METRIC: Supply Validation (Custody)
                'custody_btc': self.config['custody_btc'],
                'supply_percentage': self.config['supply_percentage'],
                'custody_notes': self._get_custody_notes(),

                # SECONDARY METRIC: Payment Flow (Daily)
                'daily_deposits_btc': daily_deposits,
                'daily_withdrawals_btc': daily_withdrawals,
                'daily_volume_btc': daily_volume,
                'payment_notes': self._get_payment_notes(),

                # DERIVED: Consensus Weight
                'consensus_weight': self.config['consensus_weight'],
                'weight_calculation': 'custody_primary_flow_secondary',
                'economic_influence': self._get_influence_level(),
            },
            'bitcoin_config': {
                'maxconnections': self.config['connections'],
                'maxmempool': self.config['mempool'],
                'rpcthreads': 32 if 'major' in self.node_type else 16,
                'txindex': 1 if 'exchange' in self.node_type else 0,
            },
            'resources': {
                'requests': {
                    'cpu': self.config['cpu'],
                    'memory': self.config['memory'],
                },
                'limits': {
                    'cpu': str(int(self.config['cpu'].replace('m', '')) * 2) + 'm',
                    'memory': self.config['memory'],
                },
            },
            'connections': [],  # To be populated later
        }

    def _get_custody_notes(self) -> str:
        """Generate custody notes based on node type."""
        notes = {
            'major_exchange': "Hot wallets + cold storage",
            'regional_exchange': "Regional focus, strong security practices",
            'payment_processor': "Operational wallets, minimal custody",
            'custody_provider': "Institutional custody, cold storage dominant",
        }
        return notes.get(self.config['entity_type'], "Standard custody configuration")

    def _get_payment_notes(self) -> str:
        """Generate payment flow notes based on node type."""
        notes = {
            'major_exchange': "High-frequency retail + institutional",
            'regional_exchange': "Medium-volume regional trading",
            'payment_processor': "High-frequency merchant payments, operational chokepoint",
            'custody_provider': "Low-frequency institutional movements",
        }
        return notes.get(self.config['entity_type'], "Standard payment flow")

    def _get_influence_level(self) -> str:
        """Determine influence level based on consensus weight."""
        weight = self.config['consensus_weight']
        if weight >= 5.0:
            return 'critical'
        elif weight >= 2.0:
            return 'significant'
        elif weight >= 0.5:
            return 'moderate'
        else:
            return 'minor'


class NetworkGenerator:
    """Generate Warnet networks with Economic Nodes."""
    
    def __init__(self, total_nodes: int, economic_pct: float = 0.15):
        self.total_nodes = total_nodes
        self.economic_pct = economic_pct
        self.relay_pct = 0.65
        self.constrained_pct = 0.20
        
        self.num_economic = int(total_nodes * economic_pct)
        self.num_relay = int(total_nodes * self.relay_pct)
        self.num_constrained = total_nodes - self.num_economic - self.num_relay
        
        self.nodes = []
    
    def generate(self) -> Dict:
        """Generate complete network configuration."""
        self.nodes = []
        
        # Generate Economic Nodes
        self._generate_economic_nodes()
        
        # Generate Relay Nodes
        self._generate_relay_nodes()
        
        # Generate Constrained Nodes
        self._generate_constrained_nodes()
        
        # Assign connections
        self._assign_connections()
        
        return {
            'network': {
                'name': f'economic-network-{self.total_nodes}',
                'description': f'Network with {self.num_economic} Economic Nodes',
                'nodes': self.nodes
            }
        }
    
    def _generate_economic_nodes(self):
        """Generate Economic Node configurations with BCAP-aligned metrics."""
        # Distribution of Economic Node types (BCAP-aligned)
        type_distribution = [
            ('major_exchange', 0.20),  # 20% are major exchanges
            ('regional_exchange', 0.30),  # 30% are regional exchanges
            ('payment_processor', 0.30),  # 30% are payment processors
            ('custody_provider', 0.20),  # 20% are custody providers
        ]

        for i in range(self.num_economic):
            # Select type based on distribution
            rand = random.random()
            cumulative = 0
            for node_type, pct in type_distribution:
                cumulative += pct
                if rand < cumulative:
                    break

            node_name = f"economic-{node_type}-{i}"
            economic_node = EconomicNode(node_name, node_type, version="27.0")
            self.nodes.append(economic_node.to_dict())
    
    def _generate_relay_nodes(self):
        """Generate standard relay nodes."""
        # Version distribution (simulate real-world upgrade patterns)
        version_distribution = [
            ('27.0', 0.50),  # 50% on latest
            ('26.0', 0.30),  # 30% on previous
            ('25.0', 0.15),  # 15% on older
            ('24.0', 0.05),  # 5% on very old
        ]
        
        for i in range(self.num_relay):
            # Select version
            rand = random.random()
            cumulative = 0
            for version, pct in version_distribution:
                cumulative += pct
                if rand < cumulative:
                    break
            
            version_tag = 'version_latest' if version == '27.0' else f'version_{version.replace(".", "_")}'
            
            node = {
                'name': f'relay-node-{i}',
                'image': f'bitcoindevproject/bitcoin:{version}',
                'tags': ['relay_node', 'standard', version_tag],
                'metadata': {
                    'weight': 1,
                    'node_type': 'relay',
                },
                'bitcoin_config': {
                    'maxconnections': 125,
                    'maxmempool': 300,
                },
                'resources': {
                    'requests': {
                        'cpu': '500m',
                        'memory': '2Gi',
                    },
                    'limits': {
                        'cpu': '1000m',
                        'memory': '4Gi',
                    },
                },
                'connections': [],
            }
            self.nodes.append(node)
    
    def _generate_constrained_nodes(self):
        """Generate resource-constrained nodes."""
        for i in range(self.num_constrained):
            # Constrained nodes typically on older versions
            version = random.choice(['25.0', '24.0', '23.0'])
            
            node = {
                'name': f'constrained-node-{i}',
                'image': f'bitcoindevproject/bitcoin:{version}',
                'tags': ['constrained_node', 'resource_limited', f'version_{version.replace(".", "_")}'],
                'metadata': {
                    'weight': 0.5,
                    'node_type': 'constrained',
                },
                'bitcoin_config': {
                    'maxconnections': 8,
                    'maxmempool': 50,
                },
                'resources': {
                    'requests': {
                        'cpu': '125m',
                        'memory': '512Mi',
                    },
                    'limits': {
                        'cpu': '250m',
                        'memory': '1Gi',
                    },
                },
                'connections': [],
            }
            self.nodes.append(node)
    
    def _assign_connections(self):
        """Assign connections between nodes (topology)."""
        node_names = [n['name'] for n in self.nodes]
        
        for node in self.nodes:
            node_type = node['metadata']['node_type']
            
            # Determine number of connections based on node type
            if node_type == 'economic_node' or 'economic_node' in node.get('tags', []):
                # Economic nodes are hubs - connect to many peers
                num_connections = random.randint(15, 30)
                # Prioritize connecting to other economic nodes
                other_economic = [n['name'] for n in self.nodes 
                                 if 'economic_node' in n.get('tags', []) and n['name'] != node['name']]
                connections = other_economic[:min(len(other_economic), 5)]
                
                # Fill remaining with random nodes
                remaining = num_connections - len(connections)
                available = [n for n in node_names if n != node['name'] and n not in connections]
                connections.extend(random.sample(available, min(remaining, len(available))))
                
            elif node_type == 'relay':
                # Relay nodes - moderate connectivity
                num_connections = random.randint(8, 15)
                # Connect to at least one economic node
                economic_nodes = [n['name'] for n in self.nodes if 'economic_node' in n.get('tags', [])]
                connections = [random.choice(economic_nodes)] if economic_nodes else []
                
                # Fill remaining with random nodes
                remaining = num_connections - len(connections)
                available = [n for n in node_names if n != node['name'] and n not in connections]
                connections.extend(random.sample(available, min(remaining, len(available))))
                
            else:  # constrained
                # Constrained nodes - minimal connectivity
                num_connections = random.randint(2, 5)
                available = [n for n in node_names if n != node['name']]
                connections = random.sample(available, min(num_connections, len(available)))
            
            node['connections'] = connections


class NetworkAnalyzer:
    """Analyze Economic Node networks."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.nodes = config.get('network', {}).get('nodes', [])
    
    def analyze(self) -> Dict:
        """Perform comprehensive analysis."""
        return {
            'network_summary': self._network_summary(),
            'economic_distribution': self._economic_distribution(),
            'version_distribution': self._version_distribution(),
            'resource_distribution': self._resource_distribution(),
            'topology_analysis': self._topology_analysis(),
            'economic_metrics': self._economic_metrics(),
        }
    
    def _network_summary(self) -> Dict:
        """Basic network statistics."""
        economic = [n for n in self.nodes if 'economic_node' in n.get('tags', [])]
        relay = [n for n in self.nodes if 'relay_node' in n.get('tags', [])]
        constrained = [n for n in self.nodes if 'constrained_node' in n.get('tags', [])]
        
        return {
            'total_nodes': len(self.nodes),
            'economic_nodes': len(economic),
            'relay_nodes': len(relay),
            'constrained_nodes': len(constrained),
            'economic_percentage': f"{len(economic) / len(self.nodes) * 100:.1f}%",
        }
    
    def _economic_distribution(self) -> Dict:
        """Distribution of Economic Node types."""
        economic = [n for n in self.nodes if 'economic_node' in n.get('tags', [])]
        
        type_counts = defaultdict(int)
        for node in economic:
            node_type = node.get('metadata', {}).get('node_type', 'unknown')
            type_counts[node_type] += 1
        
        return dict(type_counts)
    
    def _version_distribution(self) -> Dict:
        """Distribution of Bitcoin Core versions."""
        version_counts = defaultdict(int)
        
        for node in self.nodes:
            image = node.get('image', '')
            # Extract version from image tag
            if ':' in image:
                version = image.split(':')[1]
                version_counts[version] += 1
        
        return dict(version_counts)
    
    def _resource_distribution(self) -> Dict:
        """Resource allocation across node types."""
        resources = defaultdict(lambda: {'cpu': 0, 'memory': 0, 'count': 0})
        
        for node in self.nodes:
            node_type = node.get('metadata', {}).get('node_type', 'unknown')
            req = node.get('resources', {}).get('requests', {})
            
            # Parse CPU (convert to millicores)
            cpu_str = req.get('cpu', '0m')
            cpu = int(cpu_str.replace('m', '')) if 'm' in cpu_str else int(cpu_str) * 1000
            
            # Parse memory (convert to Gi)
            mem_str = req.get('memory', '0Gi')
            memory = float(mem_str.replace('Gi', '')) if 'Gi' in mem_str else float(mem_str.replace('Mi', '')) / 1024
            
            resources[node_type]['cpu'] += cpu
            resources[node_type]['memory'] += memory
            resources[node_type]['count'] += 1
        
        return {k: {
            'total_cpu_millicores': v['cpu'],
            'total_memory_gi': round(v['memory'], 2),
            'avg_cpu_per_node': round(v['cpu'] / v['count'], 0),
            'avg_memory_per_node_gi': round(v['memory'] / v['count'], 2),
            'node_count': v['count'],
        } for k, v in resources.items()}
    
    def _topology_analysis(self) -> Dict:
        """Analyze network topology."""
        connection_counts = defaultdict(int)
        
        for node in self.nodes:
            node_type = node.get('metadata', {}).get('node_type', 'unknown')
            num_connections = len(node.get('connections', []))
            connection_counts[node_type] += num_connections
        
        # Build adjacency for degree centrality
        adjacency = defaultdict(set)
        for node in self.nodes:
            for peer in node.get('connections', []):
                adjacency[node['name']].add(peer)
                adjacency[peer].add(node['name'])
        
        # Find most connected nodes
        degrees = [(name, len(peers)) for name, peers in adjacency.items()]
        degrees.sort(key=lambda x: x[1], reverse=True)
        
        return {
            'avg_connections_by_type': {k: v / sum(1 for n in self.nodes if n.get('metadata', {}).get('node_type') == k) 
                                        for k, v in connection_counts.items()},
            'most_connected_nodes': degrees[:10],
            'average_degree': sum(len(p) for p in adjacency.values()) / len(adjacency) if adjacency else 0,
        }
    
    def _economic_metrics(self) -> Dict:
        """Calculate BCAP-relevant metrics."""
        economic = [n for n in self.nodes if 'economic_node' in n.get('tags', [])]
        
        total_weight = sum(n.get('metadata', {}).get('weight', 0) for n in self.nodes)
        economic_weight = sum(n.get('metadata', {}).get('weight', 0) for n in economic)
        
        # Version uniformity among economic nodes
        economic_versions = [n.get('image', '').split(':')[1] for n in economic]
        version_counts = defaultdict(int)
        for v in economic_versions:
            version_counts[v] += 1
        
        most_common_version = max(version_counts.items(), key=lambda x: x[1]) if version_counts else ('unknown', 0)
        version_uniformity = most_common_version[1] / len(economic) if economic else 0
        
        return {
            'total_network_weight': total_weight,
            'economic_node_weight': economic_weight,
            'economic_weight_percentage': f"{economic_weight / total_weight * 100:.1f}%",
            'economic_version_uniformity': f"{version_uniformity * 100:.1f}%",
            'most_common_economic_version': most_common_version[0],
            'economic_consensus_threshold_60pct': economic_weight * 0.6,
            'economic_consensus_threshold_80pct': economic_weight * 0.8,
        }
    
    def print_analysis(self):
        """Print formatted analysis."""
        analysis = self.analyze()
        
        print("=" * 80)
        print("WARNET ECONOMIC NODE NETWORK ANALYSIS")
        print("=" * 80)
        
        print("\n### NETWORK SUMMARY ###")
        for key, value in analysis['network_summary'].items():
            print(f"  {key:25s}: {value}")
        
        print("\n### ECONOMIC NODE DISTRIBUTION ###")
        for node_type, count in analysis['economic_distribution'].items():
            print(f"  {node_type:25s}: {count}")
        
        print("\n### VERSION DISTRIBUTION ###")
        for version, count in analysis['version_distribution'].items():
            print(f"  Bitcoin Core {version:15s}: {count} nodes")
        
        print("\n### RESOURCE ALLOCATION ###")
        for node_type, resources in analysis['resource_distribution'].items():
            print(f"\n  {node_type}:")
            for metric, value in resources.items():
                print(f"    {metric:30s}: {value}")
        
        print("\n### TOPOLOGY ANALYSIS ###")
        print(f"  Average degree: {analysis['topology_analysis']['average_degree']:.2f}")
        print("\n  Most connected nodes:")
        for name, degree in analysis['topology_analysis']['most_connected_nodes']:
            print(f"    {name:30s}: {degree} connections")
        
        print("\n### ECONOMIC METRICS (BCAP) ###")
        for metric, value in analysis['economic_metrics'].items():
            print(f"  {metric:35s}: {value}")
        
        print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(description='Economic Node Network Utilities for Warnet')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate network configuration')
    gen_parser.add_argument('--nodes', type=int, default=30, help='Total number of nodes')
    gen_parser.add_argument('--economic-pct', type=float, default=0.15, help='Percentage of Economic Nodes')
    gen_parser.add_argument('--output', type=str, required=True, help='Output YAML file')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze network configuration')
    analyze_parser.add_argument('--config', type=str, required=True, help='Network YAML file to analyze')
    
    args = parser.parse_args()
    
    if args.command == 'generate':
        print(f"Generating network with {args.nodes} nodes ({args.economic_pct*100:.0f}% Economic)...")
        generator = NetworkGenerator(args.nodes, args.economic_pct)
        config = generator.generate()
        
        with open(args.output, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        print(f"Network configuration written to {args.output}")
        
        # Also print analysis
        analyzer = NetworkAnalyzer(config)
        analyzer.print_analysis()
        
    elif args.command == 'analyze':
        print(f"Analyzing network configuration: {args.config}")
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
        
        analyzer = NetworkAnalyzer(config)
        analyzer.print_analysis()
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
