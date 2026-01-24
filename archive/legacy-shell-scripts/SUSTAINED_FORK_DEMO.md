# Sustained Fork Testing Demo

Complete workflow for creating, monitoring, and analyzing sustained forks with depth measurement.

---

## Prerequisites

- Warnet deployed with 5 nodes (node-0000 to node-0004)
- Enhanced fork monitor or persistent monitor running
- Nodes at block height > 100

---

## Complete Workflow

### Step 1: Start Monitoring

Open a terminal and start the enhanced fork monitor:

```bash
cd warnetScenarioDiscovery/tools
./enhanced_fork_monitor.sh
```

Leave this running to capture fork events and depth analysis.

### Step 2: Partition the Network

In another terminal, create network partition:

```bash
cd warnetScenarioDiscovery/tools
./partition_5node_network.sh
```

This creates two isolated groups:
- **Group A (v26)**: node-0001, node-0003 (2 nodes)
- **Group B (v27)**: node-0000, node-0002, node-0004 (3 nodes)

### Step 3: Mine Competing Chains

Mine blocks on each partition to create divergent chains:

```bash
# Mine 5 blocks on Group A (v26)
for i in {1..5}; do
    warnet bitcoin rpc node-0001 generatetoaddress 1 "bcrt1qxxx"
    sleep 2
done

# Mine 8 blocks on Group B (v27)
for i in {1..8}; do
    warnet bitcoin rpc node-0000 generatetoaddress 1 "bcrt1qxxx"
    sleep 2
done
```

### Step 4: Verify Fork Exists

Check that nodes are on different chains:

```bash
# Check Group A
warnet bitcoin rpc node-0001 getblockcount
warnet bitcoin rpc node-0001 getbestblockhash

# Check Group B
warnet bitcoin rpc node-0000 getblockcount
warnet bitcoin rpc node-0000 getbestblockhash
```

You should see different tip hashes!

### Step 5: Analyze Fork Depth

Measure how deep the fork is:

```bash
python3 analyze_fork_depth.py --node1 node-0001 --node2 node-0000
```

**Expected output**:
```
🔥 FORK DETECTED
============================================================

Chain A:
  Tip:    abc123def456...
  Height: 105
  Blocks since fork: 5

Chain B:
  Tip:    def789ghi012...
  Height: 108
  Blocks since fork: 8

Common Ancestor:
  Hash:   xyz999abc777...
  Height: 100

Fork Depth Analysis:
  Chain A: 5 blocks
  Chain B: 8 blocks
  Total:   13 blocks

Fork depth: 13 blocks (5 + 8)
============================================================
```

### Step 6: Let Fork Sustain

Wait 1-2 minutes to observe sustained fork:
- Monitor shows continuous fork detection
- Fork depth remains stable
- Each group continues building their chain

### Step 7: Reconnect Network

Reconnect the partitioned network:

```bash
./reconnect_5node_network.sh
```

### Step 8: Observe Chain Reorganization

Watch the monitor for reorg:
- Nodes detect longer chain (Group B with 8 blocks)
- Group A nodes reorganize to Group B's chain
- Network converges to single tip
- **Fork depth goes from 13 → 0**

---

## Understanding the Output

### Fork Monitor Output

```
⚠️  FORK DETECTED! 2 different chain tips

📊 Analyzing fork depth...

🔥 FORK DETECTED
Fork depth: 13 blocks (5 + 8)
```

### What the Numbers Mean

- **Chain A: 5 blocks** - How many blocks Group A mined since partition
- **Chain B: 8 blocks** - How many blocks Group B mined since partition
- **Total: 13 blocks** - Total divergence (5 + 8)
- **Common ancestor: height 100** - Last block both groups agreed on

### After Reconnection

```
✓ Network synchronized - all nodes on same tip
```

Longest chain wins (Group B's 8-block chain), Group A reorganizes.

---

## Variations

### Test 1: Equal Mining

```bash
# Both groups mine same number of blocks
for i in {1..5}; do warnet bitcoin rpc node-0001 generatetoaddress 1 "bcrt1qxxx"; sleep 2; done
for i in {1..5}; do warnet bitcoin rpc node-0000 generatetoaddress 1 "bcrt1qxxx"; sleep 2; done

# Result: Tie-breaker based on which tip was seen first
```

### Test 2: Continuous Competing Mining

```bash
# Mine continuously on both groups (run in separate terminals)

# Terminal 1: Group A
while true; do
    warnet bitcoin rpc node-0001 generatetoaddress 1 "bcrt1qxxx"
    sleep 5
done

# Terminal 2: Group B
while true; do
    warnet bitcoin rpc node-0000 generatetoaddress 1 "bcrt1qxxx"
    sleep 3
done

# Watch fork depth continuously increase!
```

### Test 3: Version-Based Fork

Use your generated networks where Group A and B have different Bitcoin Core versions:
- Group A (v26) mines one chain
- Group B (v27) mines another
- Demonstrates version split with economic weighting

---

## Integration with Phase 1 Tests

Add to your Phase 1 test scripts:

```bash
# In test script...

# Create sustained fork
./partition_5node_network.sh
sleep 5

# Mine competing chains
for i in {1..5}; do
    warnet bitcoin rpc node-0001 generatetoaddress 1 "bcrt1qxxx"
    sleep 1
done

for i in {1..8}; do
    warnet bitcoin rpc node-0000 generatetoaddress 1 "bcrt1qxxx"
    sleep 1
done

# Analyze fork depth
python3 analyze_fork_depth.py --node1 node-0001 --node2 node-0000 \
    > ${RESULTS_DIR}/fork_depth_analysis.txt

# Save fork depth metric
FORK_DEPTH=$(grep "Total:" ${RESULTS_DIR}/fork_depth_analysis.txt | awk '{print $2}')
echo "Fork depth: $FORK_DEPTH blocks" >> ${RESULTS_DIR}/FINDINGS.md

# Reconnect and observe reorg
./reconnect_5node_network.sh
```

---

## Troubleshooting

### Fork Not Detected

**Problem**: Nodes still synchronized after partition

**Solution**:
- Verify bans applied: `warnet bitcoin rpc node-0001 listbanned`
- Check peer count dropped to 0: `warnet bitcoin rpc node-0001 getconnectioncount`
- Ensure you're mining on DIFFERENT nodes from each group

### Fork Depth Analysis Fails

**Problem**: "Could not find common ancestor"

**Solution**:
- Ensure node has full blockchain history
- Try analyzing from a node that was running during entire fork
- Use `--node1 node-0000` (Group B node often has more history)

### Nodes Won't Reconnect

**Problem**: Peers not connecting after reconnect script

**Solution**:
```bash
# Manual reconnect
for node in node-0000 node-0001 node-0002 node-0003 node-0004; do
    warnet bitcoin rpc $node clearbanned
done

# Wait and check
sleep 10
warnet status
```

---

## Quick Reference

```bash
# Create partition
./partition_5node_network.sh

# Mine on Group A (v26)
warnet bitcoin rpc node-0001 generatetoaddress 5 "bcrt1qxxx"

# Mine on Group B (v27)
warnet bitcoin rpc node-0000 generatetoaddress 8 "bcrt1qxxx"

# Analyze depth
python3 analyze_fork_depth.py --node1 node-0001 --node2 node-0000

# Reconnect
./reconnect_5node_network.sh
```

---

## Expected Results

For Phase 1 testing:

| Test | Fork Depth (expected) | Winner | Notes |
|------|----------------------|---------|-------|
| critical-50-50-split | 10-15 blocks | Group B (v27) | Volume dominance |
| custody-volume-conflict | 15-20 blocks | Group B (v27) | Volume beats custody |
| single-major-exchange | 5-10 blocks | Group B (v27) | Network majority |
| dual-metric-baseline | Variable | Longest chain | Baseline behavior |

---

**Status**: Ready for Phase 1 sustained fork testing!
