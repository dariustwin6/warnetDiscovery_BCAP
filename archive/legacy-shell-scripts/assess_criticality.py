#!/usr/bin/env python3
"""
Automated criticality assessment for Warnet test scenarios
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

class CriticalityAssessor:
    def __init__(self, data_dir: str = "test_results/live_monitoring"):
        self.data_dir = Path(data_dir)
        
    def assess_network_state(self, iteration_dir: Path) -> Tuple[int, str, Dict]:
        """
        Assess criticality of a network state snapshot
        Returns: (score, classification, details)
        """
        score = 0
        details = {
            "fork_detected": False,
            "height_divergence": 0,
            "isolated_nodes": 0,
            "consensus_issues": [],
            "warnings": []
        }
        
        # Load data from all nodes
        nodes_data = {}
        for node_file in iteration_dir.glob("tank-*_blockchain.json"):
            node_name = node_file.stem.replace("_blockchain", "")
            try:
                with open(node_file) as f:
                    nodes_data[node_name] = json.load(f)
            except:
                continue
        
        if len(nodes_data) == 0:
            return 0, "NO_DATA", details
        
        # Extract heights and tips
        heights = {}
        tips = {}
        for node, data in nodes_data.items():
            if "blocks" in data:
                heights[node] = data["blocks"]
            if "bestblockhash" in data:
                tips[node] = data["bestblockhash"]
        
        # Check for fork (different tips)
        unique_tips = set(tips.values())
        if len(unique_tips) > 1:
            details["fork_detected"] = True
            score += 100
            details["consensus_issues"].append(f"Chain fork: {len(unique_tips)} different tips")
        
        # Check height divergence
        if heights:
            max_height = max(heights.values())
            min_height = min(heights.values())
            height_diff = max_height - min_height
            details["height_divergence"] = height_diff
            
            if height_diff > 0:
                score += min(height_diff * 10, 50)  # Cap at 50 points
                if height_diff > 1:
                    details["warnings"].append(f"Height divergence: {min_height}-{max_height}")
        
        # Check for isolated nodes (based on peer count)
        for node_file in iteration_dir.glob("tank-*_peers.json"):
            node_name = node_file.stem.replace("_peers", "")
            try:
                with open(node_file) as f:
                    peers = json.load(f)
                    if len(peers) == 0:
                        details["isolated_nodes"] += 1
                        score += 30
                        details["warnings"].append(f"{node_name} has no peers")
            except:
                continue
        
        # Classify based on score
        if score >= 80:
            classification = "CRITICAL"
        elif score >= 40:
            classification = "HIGH_RISK"
        elif score >= 20:
            classification = "MEDIUM_RISK"
        else:
            classification = "LOW_RISK"
        
        return score, classification, details
    
    def analyze_latest(self) -> Dict:
        """Analyze the most recent iteration"""
        # Find latest iteration directory
        iter_dirs = sorted(self.data_dir.glob("iter_*"), key=lambda p: p.name)
        if not iter_dirs:
            return {"error": "No iteration data found"}
        
        latest_dir = iter_dirs[-1]
        score, classification, details = self.assess_network_state(latest_dir)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "iteration_dir": str(latest_dir),
            "criticality_score": score,
            "classification": classification,
            "details": details
        }
    
    def generate_report(self) -> str:
        """Generate a human-readable report"""
        result = self.analyze_latest()
        
        if "error" in result:
            return f"Error: {result['error']}"
        
        report = []
        report.append("=" * 60)
        report.append("WARNET CRITICALITY ASSESSMENT")
        report.append("=" * 60)
        report.append(f"Timestamp: {result['timestamp']}")
        report.append(f"Iteration: {result['iteration_dir']}")
        report.append("")
        report.append(f"CRITICALITY SCORE: {result['criticality_score']}")
        report.append(f"CLASSIFICATION: {result['classification']}")
        report.append("")
        
        details = result["details"]
        
        if details["fork_detected"]:
            report.append("🚨 FORK DETECTED!")
        
        if details["height_divergence"] > 0:
            report.append(f"⚠️  Height divergence: {details['height_divergence']} blocks")
        
        if details["isolated_nodes"] > 0:
            report.append(f"⚠️  Isolated nodes: {details['isolated_nodes']}")
        
        if details["consensus_issues"]:
            report.append("\nConsensus Issues:")
            for issue in details["consensus_issues"]:
                report.append(f"  - {issue}")
        
        if details["warnings"]:
            report.append("\nWarnings:")
            for warning in details["warnings"]:
                report.append(f"  - {warning}")
        
        report.append("=" * 60)
        
        return "\n".join(report)

def main():
    assessor = CriticalityAssessor()
    print(assessor.generate_report())
    
    # Save to file
    result = assessor.analyze_latest()
    output_file = Path("test_results/live_monitoring/latest_assessment.json")
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\nDetailed results saved to: {output_file}")

if __name__ == "__main__":
    main()
EOF
