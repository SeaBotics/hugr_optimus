#!/bin/bash
# Brings up foc and primus for a test session and ends with a green or red flag.
# Run on foc (or any machine with SSH key access to both).

cd "$(dirname "$0")" || exit 1
set -o pipefail

FOC=${FOC:-foc}
PRIMUS=${PRIMUS:-primus}
MIN_MBIT=${MIN_MBIT:-5}
NODES="oak_container yolo_detector overlay_creator image_preview thrust_allocation foxglove_bridge"
ROS='source /opt/ros/jazzy/setup.bash;'
TELEOP="tmux new -d -s foc \"bash -c 'source /opt/ros/jazzy/setup.bash && ros2 launch teleop_twist_joy teleop-launch.py joy_config:=xbox'\""
PRIMUS_START="tmux kill-session -t optimus 2>/dev/null; tmux new -d -s optimus 'cd ~/Code && ./start.sh'"
ROUTER_UP='for d in ~/Code/ros2router ~/ros2router; do [ -f $d/compose.yaml ] && cd $d && docker compose up -d >/dev/null 2>&1 && exit 0; done; exit 1'

on() {
    local host=$1; shift
    if [ "${host#*@}" = "$(hostname)" ]; then
        bash -c "$*"
    else
        ssh -o BatchMode=yes -o ConnectTimeout=10 "$host" "$*"
    fi
}

on_tty() {
    local host=$1; shift
    if [ "${host#*@}" = "$(hostname)" ]; then
        bash -c "$*"
    else
        ssh -t -o ConnectTimeout=10 "$host" "$*"
    fi
}

wait_for() {
    local secs=$1; shift
    local end=$((SECONDS + secs))
    until "$@" >/dev/null 2>&1; do
        [ $SECONDS -ge $end ] && return 1
        sleep 3
    done
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

ok()   { echo "  OK    $*"; }
warn() { echo "  WARN  $*"; WARNINGS="$WARNINGS\n  - $*"; }
red()  {
    echo "  FAIL  $1"
    [ -n "$2" ] && echo "        Fix: $2"
    echo
    echo -e "\e[41;97m  RED FLAG: do not start testing  \e[0m"
    exit 1
}
ask()  { local a; read -r -p "  $1 [y/N] " a; [[ $a =~ ^[yY]$ ]]; }

joined()     { on "$1" 'husarnet status | grep "Is joined" | grep -q yes'; }
reachable()  { on "$1" true; }
p2p()        { on "$FOC" "husarnet status | grep -A1 ' $PRIMUS\$' | grep -q 'peer to peer'"; }
router_ok()  { on "$1" '[ "$(docker ps --format "{{.Image}}" | grep -c ros2router)" -eq 1 ] && docker exec ros2router grep -q rt/joy /var/tmp/DDS_ROUTER_CONFIGURATION.yaml'; }
running()    { on "$PRIMUS" "for p in $NODES; do pgrep -f \"[\${p:0:1}]\${p:1}\" >/dev/null || exit 1; done"; }
any_running(){ on "$PRIMUS" "for p in $NODES; do pgrep -f \"[\${p:0:1}]\${p:1}\" >/dev/null && exit 0; done; exit 1"; }
joy_ok()     { on "$FOC" "$ROS timeout 10 ros2 topic echo --once /joy sensor_msgs/msg/Joy --field header"; }
joystick()   { on "$FOC" 'ev=$(ls /sys/class/input/js0/device/ 2>/dev/null | grep -m1 "^event") && [ -r /dev/input/$ev ]'; }
router_up()  { on "$1" "$ROUTER_UP" && wait_for 60 router_ok "$1"; }
start_ros()  { on "$PRIMUS" "$PRIMUS_START" && wait_for 120 running; }
start_joy()  { on "$FOC" "tmux kill-session -t foc 2>/dev/null; $TELEOP" && wait_for 30 joy_ok; }

fix_husarnet() {
    local h=$1
    if ask "Husarnet on $h is not joined. Restart it now (needs sudo password)?"; then
        on_tty "$h" "sudo systemctl restart husarnet"
        spin "Waiting for $h to join Husarnet" wait_for 90 joined "$h" && return 0
    fi
    return 1
}

echo "1. Husarnet"
spin "Waiting for $FOC to join Husarnet" wait_for 60 joined "$FOC" || fix_husarnet "$FOC" || red "$FOC is not joined to Husarnet" "sudo systemctl restart husarnet, or sudo husarnet join <code> $FOC"
ok "$FOC is joined"
spin "Connecting to $PRIMUS" wait_for 120 reachable "$PRIMUS" || red "cannot reach $PRIMUS over SSH" "check that primus is powered; on primus (USB: ssh primus@192.168.55.1): sudo systemctl restart husarnet"
spin "Waiting for $PRIMUS to join Husarnet" wait_for 60 joined "$PRIMUS" || fix_husarnet "$PRIMUS" || red "$PRIMUS is not joined to Husarnet" "on primus: sudo systemctl restart husarnet, or sudo husarnet join <code> primus"
ok "$PRIMUS is joined"
if spin "Waiting for a direct (peer to peer) link" wait_for 60 p2p; then
    ok "$FOC <-> $PRIMUS is peer to peer"
else
    warn "$FOC <-> $PRIMUS is tunelled (slow relay). Check that the two Jetsons have different LAN IPs, then restart husarnet on both"
fi

echo "2. ros2router"
for h in "$FOC" "$PRIMUS"; do
    if ! spin "Checking ros2router on $h" router_ok "$h"; then
        spin "Starting ros2router on $h" router_up "$h" || red "ros2router on $h is not running with the filter" "cd ~/Code/ros2router (or ~/ros2router) && docker compose up -d; docker logs ros2router"
    fi
    ok "$h runs ros2router with filter"
done

echo "3. Link speed"
spin "Measuring link speed (about 20 s)" env DURATION=5 ./net_speed.sh
speed=$SPIN_OUT
echo "$speed" | sed 's/^/        /'
mbit=$(echo "$speed" | awk -v p="$PRIMUS -> $FOC:" 'index($0, p) == 1 {print $(NF-3)}')
if [ -z "$mbit" ]; then
    warn "could not measure link speed"
elif awk -v m="$mbit" -v t="$MIN_MBIT" 'BEGIN { exit !(m < t) }'; then
    warn "$PRIMUS -> $FOC is only $mbit Mbit/s (preview needs about 4)"
else
    ok "$PRIMUS -> $FOC is $mbit Mbit/s"
fi

echo "4. Controller"
spin "Checking the Xbox controller" joystick || red "Xbox controller missing or not readable on $FOC" "plug it in; if it is plugged in: sudo usermod -aG input foc, then log in again"
ok "Xbox controller is connected and readable"

echo "5. ROS on $PRIMUS"
if spin "Checking nodes on $PRIMUS" running; then
    ok "all nodes already running"
else
    spin "Checking for partly running nodes" any_running && echo "        Some nodes are running, restarting all."
    ask "Is the boat safe? Thrusters will be enabled." || red "stopped before starting the thrusters"
    spin "Starting nodes on $PRIMUS (up to 2 min)" start_ros || red "not all nodes started on $PRIMUS" "check ~/*.log on primus, or ssh -t primus tmux attach -t optimus"
    ok "all nodes started"
fi

echo "6. Teleop on $FOC"
if spin "Checking /joy" joy_ok; then
    ok "/joy is publishing"
else
    spin "Starting teleop" start_joy || red "/joy is not publishing on $FOC" "tmux attach -t foc on foc to see the error"
    ok "teleop started, /joy is publishing"
fi

echo "7. Final check"
spin "Letting nodes settle" sleep 5
if ! spin "Running check_link.sh (about 1 min)" ./check_link.sh; then
    spin "Retrying in 15 s (nodes may still be starting)" sleep 15
    if ! spin "Running check_link.sh again" ./check_link.sh; then
        echo "$SPIN_OUT" | sed 's/^/    /'
        red "check_link.sh failed" "see the FAIL lines above"
    fi
fi
echo "$SPIN_OUT" | sed 's/^/    /'

echo
if [ -n "$WARNINGS" ]; then
    echo -e "Warnings:$WARNINGS"
    echo
fi
echo -e "\e[42;97m  GREEN FLAG: ready to test  \e[0m"
echo
echo "Foxglove (desktop app): ws://$PRIMUS:8765"
echo "  Image:        /oak/rgb/preview/compressed"
echo "  Calibration:  /oak/rgb/preview/camera_info"
echo "  Annotations:  /oak/rgb/preview/image_annotations"
echo "  Depth:        /oak/stereo/preview/compressed"
echo "Stop everything with ./stop.sh"
