#!/usr/bin/env python3
"""
Analyze a complete test run and generate summary report
"""

import json
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime

class TestAnalyzer:
    def __init__(self, monitoring_dir: str = "test_results/live_monitoring"):
        self.monitoring_dir = Path(monitoring_dir)
    
    def analyze_full_run(self):
        """Analyze all iterations from a test run"""
        iter_dirs = sorted(self.monitoring_dir.glob("iter_*"), key=lambda p: p.name)
        
        if not iter_dirs:
            print("No test data found")
            return
        
        print(f"Analyzing {len(iter_dirs)} iterations...")
        print("")
        
        fork_events = []
        height_history = defaultdict(list)
        
        for iter_dir in iter_dirs:
            iteration_num = iter_dir.name.split("_")[1]
            
            # Load blockchain data for each node
            for node_file in iter_dir.glob("tank-*_blockchain.json"):
                node_name = node_file.stem.replace("_blockchain", "")
                try:
                    with open(node_file) as f:
                        data = json.load(f)
                        if "blocks" in data:
                            height_history[node_name].append({
                                "iteration": int(iteration_num),
                                "height": data["blocks"],
                                "tip": data.get("bestblockhash", "")[:16]
                            })
                except:
                    continue
            
            # Check for forks in this iteration
            tips = set()
            for node_file in iter_dir.glob("tank-*_blockchain.json"):
                try:
                    with open(node_file) as f:
                        data = json.load(f)
                        if "bestblockhash" in data:
                            tips.add(data["bestblockhash"])
                except:
                    continue
            
            if len(tips) > 1:
                fork_events.append(int(iteration_num))
        
        # Generate report
        print("=" * 70)
        print("TEST RUN ANALYSIS REPORT")
        print("=" * 70)
        print(f"Total iterations: {len(iter_dirs)}")
        print(f"Fork events detected: {len(fork_events)}")
        
        if fork_events:
            print(f"Fork iterations: {fork_events}")
            print(f"Fork percentage: {len(fork_events)/len(iter_dirs)*100:.1f}%")
        
        print("")
        print("Node Height Progression:")
        print("-" * 70)
        
        for node in sorted(height_history.keys()):
            history = height_history[node]
            if history:
                start_height = history[0]["height"]
                end_height = history[-1]["height"]
                blocks_mined = end_height - start_height
                print(f"{node}: {start_height} → {end_height} ({blocks_mined:+d} blocks)")
        
        print("")
        
        # Check for divergence patterns
        print("Checking for divergence patterns...")
        max_divergence = 0
        divergence_iteration = None
        
        for iter_dir in iter_dirs:
            heights = []
            for node_file in iter_dir.glob("tank-*_blockchain.json"):
                try:
                    with open(node_file) as f:
                        data = json.load(f)
                        if "blocks" in data:
                            heights.append(data["blocks"])
                except:
                    continue
            
            if heights:
                divergence = max(heights) - min(heights)
                if divergence > max_divergence:
                    max_divergence = divergence
                    divergence_iteration = int(iter_dir.name.split("_")[1])
        
        print(f"Maximum height divergence: {max_divergence} blocks (iteration {divergence_iteration})")
        
        print("=" * 70)
        
        # Save detailed report
        report_file = self.monitoring_dir / f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "total_iterations": len(iter_dirs),
                "fork_events": fork_events,
                "fork_count": len(fork_events),
                "max_divergence": max_divergence,
                "height_history": dict(height_history)
            }, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_file}")

if __name__ == "__main__":
    analyzer = TestAnalyzer()
    analyzer.analyze_full_run()
