#!/bin/bash
while true; do
    echo "$(date): Mempool Status"
    for node in tank-0000 tank-0001 tank-0002 tank-0003 tank-0004 tank-0005 tank-0006 tank-0007; do
        size=$(warnet bitcoin rpc $node getmempoolinfo | jq '.size')
        bytes=$(warnet bitcoin rpc $node getmempoolinfo | jq '.bytes')
        echo "$node: $size txs, $bytes bytes"
    done
    echo "---"
    sleep 30
done
