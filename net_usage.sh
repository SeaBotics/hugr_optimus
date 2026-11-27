#!/bin/bash
# Live network usage on this machine, one line per interval. Ctrl+C to stop.
# Run on primus: ./net_usage.sh   From foc: ssh -t primus ~/Code/net_usage.sh

INTERVAL=${INTERVAL:-1}
HNET=${HNET:-hnet0}
WAN=${WAN:-enP8p1s0}

bytes() { cat "/sys/class/net/$1/statistics/$2_bytes" 2>/dev/null || echo 0; }

# Bytes sent on Foxglove websocket connections, and the number of clients
foxglove() {
    ss -tni state established "( sport = :8765 )" 2>/dev/null |
        awk -F'bytes_acked:' 'NF > 1 { split($2, a, " "); s += a[1]; n++ } END { print s + 0, n + 0 }'
}

mbit() { awk -v d="$1" -v i="$INTERVAL" 'BEGIN { if (d < 0) d = 0; printf "%6.2f", d * 8 / 1e6 / i }'; }

read -r fox_prev _ < <(foxglove)
h_tx_prev=$(bytes "$HNET" tx); h_rx_prev=$(bytes "$HNET" rx)
w_tx_prev=$(bytes "$WAN" tx);  w_rx_prev=$(bytes "$WAN" rx)

echo "Mbit/s every ${INTERVAL}s on $(hostname). Ctrl+C to stop."
echo "Out = sent from this machine. Other = Husarnet out minus Foxglove (router, SSH)."
printf "%-8s  %13s %13s  %13s %13s  %18s  %6s\n" "time" "Husarnet out" "Husarnet in" "Modem out" "Modem in" "Foxglove out" "Other"

while sleep "$INTERVAL"; do
    read -r fox clients < <(foxglove)
    h_tx=$(bytes "$HNET" tx); h_rx=$(bytes "$HNET" rx)
    w_tx=$(bytes "$WAN" tx);  w_rx=$(bytes "$WAN" rx)

    fox_d=$((fox - fox_prev))
    [ "$fox_d" -lt 0 ] && fox_d=0
    other_d=$((h_tx - h_tx_prev - fox_d))

    printf "%-8s  %13s %13s  %13s %13s  %11s (%d cl)  %6s\n" "$(date +%T)" \
        "$(mbit $((h_tx - h_tx_prev)))" "$(mbit $((h_rx - h_rx_prev)))" \
        "$(mbit $((w_tx - w_tx_prev)))" "$(mbit $((w_rx - w_rx_prev)))" \
        "$(mbit "$fox_d")" "$clients" "$(mbit "$other_d")"

    fox_prev=$fox
    h_tx_prev=$h_tx; h_rx_prev=$h_rx
    w_tx_prev=$w_tx; w_rx_prev=$w_rx
done
