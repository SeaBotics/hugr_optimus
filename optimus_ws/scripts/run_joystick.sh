#!/bin/bash
# Hugr Optimus - Launch Joystick Remote Control and Thrust Allocation
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

source /opt/ros/jazzy/setup.bash
source "${WS_DIR}/install/setup.bash"

echo "=========================================================="
echo " Starting Hugr Optimus Remote Control (Thrust Allocation)"
echo " - Subscribes to: /joy (Game controller / RC transmitter)"
echo " - Publishes: /motor_pwms (for ESP32 & Fossen Simulator)"
echo " - Publishes: /cmd_vel (standard twist)"
echo "=========================================================="

if [ -e "/dev/input/js0" ]; then
    echo "[INFO] Found /dev/input/js0. Starting standard Linux joy_node..."
    if ! pgrep -f "joy_node" > /dev/null; then
        ros2 run joy joy_node &
        JOY_PID=$!
        trap "kill $JOY_PID 2>/dev/null" EXIT
    fi
else
    echo "[INFO] /dev/input/js0 not detected in WSL2."
    echo "[INFO] Starting UDP Joy Bridge to receive Xbox controller from Windows..."
    if ! pgrep -f "udp_joy_node.py" > /dev/null; then
        python3 "${WS_DIR}/tools/udp_joy_node.py" &
        JOY_PID=$!
        trap "kill $JOY_PID 2>/dev/null" EXIT
    fi
fi

ros2 launch thrust_allocation thrust_allocation.launch.xml
