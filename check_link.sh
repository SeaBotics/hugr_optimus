#!/bin/bash
# Run on foc, primus, or any machine with SSH key access to both.

PRIMUS=${PRIMUS:-primus}
FOC=${FOC:-foc}
ROS_ENV='source /opt/ros/jazzy/setup.bash; source ~/Code/optimus_ws/install/setup.bash 2>/dev/null; export ROS_LOCALHOST_ONLY=1;'

failed=0

on() {
    local host=$1; shift
    if [ "${host#*@}" = "$(hostname)" ]; then
        bash -c "$ROS_ENV $*" </dev/null
    else
        ssh -o BatchMode=yes -o ConnectTimeout=10 "$host" "$ROS_ENV $*" </dev/null
    fi
}

check() {
    local desc=$1; shift
    if "$@" >/dev/null 2>&1; then
        echo "  OK    $desc"
    else
        echo "  FAIL  $desc"
        failed=1
    fi
}

for h in "$FOC" "$PRIMUS"; do
    if ! on "$h" true >/dev/null 2>&1; then
        echo "Cannot SSH to $h without a password. Set up a key: ssh-keygen -t ed25519 && ssh-copy-id $h"
        exit 2
    fi
done

echo "1. Husarnet"
for h in "$FOC" "$PRIMUS"; do
    check "$h is joined" on "$h" 'husarnet status | grep "Is joined" | grep -q yes'
done
check "$FOC can ping $PRIMUS" on "$FOC" "ping -6 -c 2 -W 3 $PRIMUS"

echo "2. ros2router"
for h in "$FOC" "$PRIMUS"; do
    check "$h runs exactly one router" on "$h" '[ "$(docker ps --format "{{.Image}}" | grep -c ros2router)" -eq 1 ]'
    check "$h filter active (joy allowed, image_raw blocked)" on "$h" \
        'C=/var/tmp/DDS_ROUTER_CONFIGURATION.yaml; docker exec ros2router grep -q rt/joy $C && ! docker exec ros2router grep -q image_raw $C'
done

echo "3. Nodes on $PRIMUS"
for p in oak_container yolo_detector overlay_creator image_preview foxglove_bridge thrust_allocation; do
    check "$p running" on "$PRIMUS" "pgrep -f [${p:0:1}]${p:1}"
done
check "camera publishes /oak/rgb/image_raw/compressed" on "$PRIMUS" 'timeout 15 ros2 topic echo --once /oak/rgb/image_raw/compressed sensor_msgs/msg/CompressedImage --field header'
check "YOLO publishes /oak/rgb/detections" on "$PRIMUS" 'timeout 15 ros2 topic echo --once /oak/rgb/detections vision_msgs/msg/Detection2DArray --field header'
check "preview publishes /oak/rgb/preview/compressed" on "$PRIMUS" 'timeout 15 ros2 topic echo --once /oak/rgb/preview/compressed sensor_msgs/msg/CompressedImage --field header'
check "preview publishes /oak/rgb/preview/camera_info" on "$PRIMUS" 'timeout 15 ros2 topic echo --once /oak/rgb/preview/camera_info sensor_msgs/msg/CameraInfo --field width'

echo "4. Foxglove"
check "foxglove_bridge listens on IPv6 :8765" on "$PRIMUS" 'ss -ltn | grep -qE "(\*|\[::\]):8765"'
check "$FOC reaches $PRIMUS:8765" on "$FOC" "nc -6 -z -w 5 $PRIMUS 8765"

echo "5. $PRIMUS -> $FOC via router"
check "$FOC sees /oak/rgb/detections" on "$FOC" 'ros2 topic list --no-daemon --spin-time 5 | grep -qx /oak/rgb/detections'
if on "$FOC" 'ros2 interface show vision_msgs/msg/Detection2DArray' >/dev/null 2>&1; then
    check "$FOC receives /oak/rgb/detections" on "$FOC" 'timeout 15 ros2 topic echo --once /oak/rgb/detections vision_msgs/msg/Detection2DArray --field header'
else
    echo "  SKIP  vision_msgs missing on $FOC. Install: sudo apt install ros-jazzy-vision-msgs"
fi

echo "6. $FOC -> $PRIMUS via router"
if on "$FOC" 'pgrep -f [j]oy_node' >/dev/null 2>&1; then
    check "$PRIMUS receives /joy" on "$PRIMUS" 'timeout 15 ros2 topic echo --once /joy sensor_msgs/msg/Joy --field header'
else
    echo "  SKIP  no joy_node on $FOC. Start: ros2 launch teleop_twist_joy teleop-launch.py joy_config:=xbox"
    failed=1
fi

echo
[ $failed -eq 0 ] && echo "All checks passed." || echo "Some checks failed."
exit $failed
