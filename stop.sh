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

# Runs a command in the background with a spinner. Output is kept in $SPIN_OUT.
SPINNER='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
[ "$(locale charmap 2>/dev/null)" = "UTF-8" ] || SPINNER='|/-\'
spin() {
    local label=$1; shift
    local out i=0 rc
    out=$(mktemp)
    "$@" >"$out" 2>&1 &
    local pid=$!
    if [ -t 1 ]; then
        while kill -0 "$pid" 2>/dev/null; do
            printf "\r  %s  %s " "${SPINNER:i++%${#SPINNER}:1}" "$label"
            sleep 0.1
        done
        printf "\r\033[K"
    fi
    wait "$pid"; rc=$?
    SPIN_OUT=$(cat "$out"); rm -f "$out"
    return $rc
}

count_left() { on "$PRIMUS" 'sleep 3; pgrep -f "[o]ak_container|[y]olo_detector|[o]verlay_creator|[i]mage_preview|[t]hrust_allocation|[f]oxglove_bridge" | wc -l'; }

spin "Stopping teleop on $FOC" on "$FOC" "tmux kill-session -t foc 2>/dev/null" && echo "Stopped teleop on $FOC" || echo "No teleop running on $FOC"
spin "Stopping nodes on $PRIMUS" on "$PRIMUS" "tmux kill-session -t optimus 2>/dev/null" && echo "Stopped nodes on $PRIMUS" || echo "No nodes session on $PRIMUS"
if ! spin "Checking that everything stopped" count_left; then
    echo "WARNING: could not reach $PRIMUS to check that the nodes stopped"
elif [ "$SPIN_OUT" = "0" ]; then
    echo "All nodes on $PRIMUS are stopped."
else
    echo "WARNING: $SPIN_OUT node processes still running on $PRIMUS"
fi
