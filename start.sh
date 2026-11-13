#!/bin/bash

# Source packages
cd optimus_ws
colcon build --symlink-install
source install/setup.bash

echo "Starting camera driver..."
# Run the working standalone node in background with output redirected to a log file for debugging
ros2 run depthai_ros_driver_v3 driver_node --ros-args \
  --params-file camera.yaml > ~/camera_driver.log 2>&1 &
sleep 3

echo "Starting neural network nodes..."
ros2 run neuralnetwork yolo_detector > ~/yolo.log 2>&1 &
sleep 2

ros2 run neuralnetwork overlay_creator > ~/overlay.log 2>&1 &
sleep 2

echo "Starting Foxglove bridge..."
ros2 launch foxglove_bridge foxglove_bridge_launch.xml > ~/foxglove.log 2>&1 &

echo "All nodes started! Check logs in ~/*.log if anything fails."
