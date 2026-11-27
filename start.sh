#!/bin/bash

if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
    echo "Run with ./start.sh, not source."
    return 1
fi

# Do not rely on ~/.bashrc (not read by tmux/ssh/systemd commands)
source /opt/ros/jazzy/setup.bash

WS="$(cd "$(dirname "$0")" && pwd)/optimus_ws"
cd "$WS" || exit 1

pkill -f "depthai_ros_driver_v3|oak_container|yolo_detector|overlay_creator|image_preview|foxglove_bridge|thrust_allocation"
sleep 2

colcon build --symlink-install || exit 1
source install/setup.bash

trap 'trap - EXIT; kill 0' EXIT INT TERM

echo "Starting camera driver..."
ros2 launch depthai_ros_driver_v3 driver.launch.py params_file:="$WS/camera.yaml" > ~/camera_driver.log 2>&1 &
sleep 3

echo "Starting neural network nodes..."
ros2 run neuralnetwork yolo_detector > ~/yolo.log 2>&1 &
sleep 2

ros2 run neuralnetwork overlay_creator > ~/overlay.log 2>&1 &
sleep 2

echo "Starting 320x320 preview for Foxglove..."
ros2 run neuralnetwork image_preview > ~/preview.log 2>&1 &
sleep 1

echo "Starting thrust allocation..."
ros2 run thrust_allocation thrust_allocation > ~/thrust.log 2>&1 &
sleep 1

echo "Starting Foxglove bridge..."
# Husarnet is IPv6-only
ros2 launch foxglove_bridge foxglove_bridge_launch.xml address:="'::'" send_buffer_limit:=100000 > ~/foxglove.log 2>&1 &

echo "All nodes started. Logs in ~/*.log. Ctrl+C stops everything."
wait
