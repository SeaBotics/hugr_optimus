#!/bin/bash
# Stops teleop on foc and all nodes on primus. The Arduino goes to neutral after 0.5 s without commands.

FOC=${FOC:-foc}
PRIMUS=${PRIMUS:-primus}

on() {
    local host=$1; shift
    if [ "${host#*@}" = "$(hostname)" ]; then
        bash -c "$*"
    else
        ssh -o BatchMode=yes -o ConnectTimeout=10 "$host" "$*"
    fi
}

on "$FOC" "tmux kill-session -t foc 2>/dev/null" && echo "Stopped teleop on $FOC" || echo "No teleop running on $FOC"
on "$PRIMUS" "tmux kill-session -t optimus 2>/dev/null" && echo "Stopped nodes on $PRIMUS" || echo "No nodes session on $PRIMUS"
sleep 3
left=$(on "$PRIMUS" 'pgrep -f "[o]ak_container|[y]olo_detector|[o]verlay_creator|[i]mage_preview|[t]hrust_allocation|[f]oxglove_bridge" | wc -l')
[ "$left" = "0" ] && echo "All nodes on $PRIMUS are stopped." || echo "WARNING: $left node processes still running on $PRIMUS"
