#!/bin/bash
# Hugr Optimus - Launch Gazebo Sim (Harmonic) 3D Maritime Simulation
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

source /opt/ros/jazzy/setup.bash

if [ -f "${WS_DIR}/install/setup.bash" ]; then
    source "${WS_DIR}/install/setup.bash"
else
    echo "Warning: install/setup.bash not found. Building workspace first..."
    cd "${WS_DIR}" && colcon build --symlink-install --packages-select hugr_description hugr_gazebo
    source "${WS_DIR}/install/setup.bash"
fi

# Ensure X11 display socket linking for WSLg
if [ -S /mnt/wslg/.X11-unix/X0 ] && [ ! -S /tmp/.X11-unix/X0 ]; then
    mkdir -p /tmp/.X11-unix 2>/dev/null || true
    ln -sf /mnt/wslg/.X11-unix/X0 /tmp/.X11-unix/X0 2>/dev/null || true
fi
export DISPLAY="${DISPLAY:-:0}"

echo "=========================================================="
echo " Starting SeaBotics Hugr Optimus 3D Gazebo Simulation"
echo " - Physics: Gazebo Sim (Harmonic) + DART + Hydrodynamics"
echo " - Environment: Maritime World with Competition Buoys"
echo " - Bridge: ROS 2 <-> Gazebo Parameter Bridge"
echo "=========================================================="

killall -9 gz sim 2>/dev/null || true

ros2 launch hugr_gazebo sim.launch.py "$@"
