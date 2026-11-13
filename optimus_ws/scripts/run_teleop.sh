#!/bin/bash
# Hugr Optimus - Keyboard Teleoperation
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

source /opt/ros/jazzy/setup.bash
source "${WS_DIR}/install/setup.bash"

echo "=========================================================="
echo " Hugr Optimus - Keyboard Teleoperation"
echo " Use keys:"
echo "   i : Move Forward"
echo "   j : Turn Left (Port)"
echo "   l : Turn Right (Starboard)"
echo "   k : Stop"
echo "   , : Move Backward"
echo "=========================================================="

ros2 run teleop_twist_keyboard teleop_twist_keyboard
