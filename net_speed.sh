#!/bin/bash
# Measures throughput between foc and primus over Husarnet.
# Run from a machine with SSH key access to both. Uses mobile data.

FOC=${FOC:-foc}
PRIMUS=${PRIMUS:-primus}
DURATION=${DURATION:-10}
PORT=${PORT:-5560}

run() { ssh -o BatchMode=yes -o ConnectTimeout=10 "$@"; }

path() {
    run "$1" "husarnet status | grep -A1 ' $2\$' | tail -1" | grep -oE "peer to peer|tunelled"
}

latency() {
    run "$1" "ping -6 -c 5 -q $2 | tail -1" | awk -F/ '{print $5 " ms"}'
}

measure() {
    local src=$1 dst=$2 out
    out=$(mktemp)
    run "$dst" "timeout $((DURATION + 15)) nc -6 -l -d $PORT | wc -c" >"$out" &
    local rx=$!
    sleep 2
    run "$src" "timeout $DURATION sh -c 'cat /dev/zero | nc -6 $dst $PORT'" >/dev/null 2>&1
    wait $rx
    awk -v b="$(cat "$out")" -v d="$DURATION" 'BEGIN { printf "%.1f Mbit/s (%.1f MB)", b * 8 / d / 1e6, b / 1e6 }'
    rm -f "$out"
}

echo "Path:     $FOC -> $PRIMUS: $(path "$FOC" "$PRIMUS"),  $PRIMUS -> $FOC: $(path "$PRIMUS" "$FOC")"
echo "Latency:  $(latency "$FOC" "$PRIMUS")"
echo "Testing ${DURATION}s per direction..."
echo "$FOC -> $PRIMUS: $(measure "$FOC" "$PRIMUS")"
echo "$PRIMUS -> $FOC: $(measure "$PRIMUS" "$FOC")"
