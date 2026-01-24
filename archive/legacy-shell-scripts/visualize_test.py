#!/usr/bin/env python3
"""
Create a simple text-based timeline visualization of the test
"""
import json
from pathlib import Path
from collections import defaultdict

monitoring_dir = Path("test_results/live_monitoring")
iter_dirs = sorted(monitoring_dir.glob("iter_*"), key=lambda p: p.name)

if not iter_dirs:
    print("No monitoring data found")
    exit(1)

print("=" * 80)
print("FORK TEST TIMELINE VISUALIZATION")
print("=" * 80)
print()

# Track each node's chain over time
node_chains = defaultdict(list)

for idx, iter_dir in enumerate(iter_dirs):
    iter_num = int(iter_dir.name.split("_")[1])
    
    # Load all node tips
    tips = {}
    for node_file in iter_dir.glob("tank-*_blockchain.json"):
        node_name = node_file.stem.replace("_blockchain", "")
        try:
            with open(node_file) as f:
                data = json.load(f)
                if "bestblockhash" in data:
                    tips[node_name] = data["bestblockhash"][:8]
        except:
            continue
    
    # Detect unique tips
    unique_tips = set(tips.values())
    
    if len(unique_tips) > 1:
        # Fork detected
        print(f"Iter {iter_num:3d}: 🚨 FORK - {len(unique_tips)} chains")
        
        # Group nodes by tip
        tip_groups = defaultdict(list)
        for node, tip in tips.items():
            tip_groups[tip].append(node)
        
        for tip, nodes in tip_groups.items():
            print(f"         Chain {tip}: {', '.join(sorted(nodes))}")
    else:
        # Synchronized
        if idx == 0:
            print(f"Iter {iter_num:3d}: ✓ Synchronized (baseline)")
        elif idx == len(iter_dirs) - 1:
            print(f"Iter {iter_num:3d}: ✓ Synchronized (resolved)")
        else:
            # Check if this is first sync after fork
            if idx > 0:
                prev_dir = iter_dirs[idx-1]
                prev_tips = set()
                for node_file in prev_dir.glob("tank-*_blockchain.json"):
                    try:
                        with open(node_file) as f:
                            data = json.load(f)
                            if "bestblockhash" in data:
                                prev_tips.add(data["bestblockhash"][:8])
                    except:
                        continue
                
                if len(prev_tips) > 1:
                    print(f"Iter {iter_num:3d}: ✓ Synchronized (REORG COMPLETE)")
                else:
                    print(f"Iter {iter_num:3d}: ✓ Synchronized")

print()
print("=" * 80)
