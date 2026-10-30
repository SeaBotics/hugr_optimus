#!/bin/bash
# Hugr Optimus - Launch Autonomous LOS Waypoint Navigator
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

source /opt/ros/jazzy/setup.bash
source "${WS_DIR}/install/setup.bash"

echo "=========================================================="
echo " Hugr Optimus - Autonomous LOS Navigation Node Active"
echo " In RViz2, click '2D Goal Pose' anywhere on the grid"
echo " to command the boat to navigate autonomously!"
echo "=========================================================="

ros2 launch hugr_autonomy autonomy.launch.py "$@"
