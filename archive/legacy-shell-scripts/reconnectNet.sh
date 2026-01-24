# Remove all bans
for i in {0..7}; do
    NODE="tank-$(printf '%04d' $i)"
    # Clear ban list
    warnet bitcoin rpc $NODE listbanned | grep -o '"[0-9.]*"' | while read ip; do
        ip_clean=$(echo $ip | tr -d '"')
        warnet bitcoin rpc $NODE setban "$ip_clean" remove
        echo "✓ $NODE unbanned $ip_clean"
    done
done

echo ""
echo "✓ Network reconnected! Watch for reorg resolution..."
