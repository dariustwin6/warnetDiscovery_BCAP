# Get node IPs and create partition
# Group A: tank-0000 to tank-0003
# Group B: tank-0004 to tank-0007

# Ban Group B from Group A
for i in {0..3}; do
    NODE_A="tank-$(printf '%04d' $i)"
    for j in {4..7}; do
        NODE_B="tank-$(printf '%04d' $j)"
        IP_B=$(kubectl get pod $NODE_B -o jsonpath='{.status.podIP}')
        warnet bitcoin rpc $NODE_A setban "$IP_B" add 86400
        echo "✓ $NODE_A banned $NODE_B ($IP_B)"
    done
done

# Ban Group A from Group B
for i in {4..7}; do
    NODE_B="tank-$(printf '%04d' $i)"
    for j in {0..3}; do
        NODE_A="tank-$(printf '%04d' $j)"
        IP_A=$(kubectl get pod $NODE_A -o jsonpath='{.status.podIP}')
        warnet bitcoin rpc $NODE_B setban "$IP_A" add 86400
        echo "✓ $NODE_B banned $NODE_A ($IP_A)"
    done
done

echo ""
echo "🚨 Network partitioned! Watch your monitor for fork detection..."
echo "Let it run for 2-3 minutes to allow chains to diverge"
