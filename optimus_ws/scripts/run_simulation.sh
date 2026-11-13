#!/bin/bash
# Hugr Optimus - Launch Fossen SITL Marine Simulation and RViz2
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

source /opt/ros/jazzy/setup.bash
source "${WS_DIR}/install/setup.bash"

# Ensure X11 display socket linking for WSLg
if [ -S /mnt/wslg/.X11-unix/X0 ] && [ ! -S /tmp/.X11-unix/X0 ]; then
    mkdir -p /tmp/.X11-unix 2>/dev/null || true
    ln -sf /mnt/wslg/.X11-unix/X0 /tmp/.X11-unix/X0 2>/dev/null || true
fi
export DISPLAY="${DISPLAY:-:0}"

echo "=========================================================="
echo " Starting SeaBotics Hugr Optimus Marine Simulation"
echo " - Hydrodynamics: Thor I. Fossen 3-DOF Maneuvering Model"
echo " - Visualization: RViz2 with Catamaran URDF"
echo "=========================================================="

ros2 launch hugr_sim sim.launch.py "$@"
