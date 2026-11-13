#!/bin/bash
# ==============================================================================
# SeaBotics Hugr Optimus - Gazebo Sim (Harmonic) Marine Proving Ground Launcher
# Compatible with: Ubuntu 24.04 (Native Linux) & Windows 11 (WSL2 / WSLg)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Automatically resolve workspace root
if [ -f "${SCRIPT_DIR}/../../install/setup.bash" ] || [ -d "${SCRIPT_DIR}/../../src" ]; then
    WS_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
elif [ -f "${SCRIPT_DIR}/../install/setup.bash" ] || [ -d "${SCRIPT_DIR}/../src" ]; then
    WS_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
else
    WS_DIR="${SCRIPT_DIR}"
fi

# Source ROS 2 Jazzy
if [ -f "/opt/ros/jazzy/setup.bash" ]; then
    source /opt/ros/jazzy/setup.bash
else
    echo "ERROR: /opt/ros/jazzy/setup.bash not found. Ensure ROS 2 Jazzy is installed."
    exit 1
fi

# Build package if not yet compiled, then source workspace overlay
if [ -f "${WS_DIR}/install/setup.bash" ]; then
    source "${WS_DIR}/install/setup.bash"
else
    echo "Workspace overlay not found. Building hugr_gazebo with colcon..."
    cd "${WS_DIR}"
    colcon build --symlink-install --packages-select hugr_gazebo
    source "${WS_DIR}/install/setup.bash"
fi

# Ensure X11 display socket linking for Windows WSLg hardware acceleration
if [ -S /mnt/wslg/.X11-unix/X0 ] && [ ! -S /tmp/.X11-unix/X0 ]; then
    mkdir -p /tmp/.X11-unix 2>/dev/null || true
    ln -sf /mnt/wslg/.X11-unix/X0 /tmp/.X11-unix/X0 2>/dev/null || true
fi
export DISPLAY="${DISPLAY:-:0}"

echo "=================================================================="
echo " Starting SeaBotics Hugr Optimus 3D Gazebo Simulation"
echo " - Physics: Gazebo Sim (Harmonic) + DART + Fossen Hydrodynamics"
echo " - Environment: Maritime World with Competition Buoys"
echo " - Bridge: ROS 2 <-> Gazebo Parameter Bridge (/oak, /imu, /gnss)"
echo "=================================================================="

# Process cleanup handler to prevent orphaned background instances
cleanup() {
    echo ""
    echo "Shutting down Gazebo Sim and ROS bridge processes..."
    pkill -9 -f 'gz sim' 2>/dev/null || true
    pkill -9 -f 'gz-sim' 2>/dev/null || true
    killall -9 gz-sim-server gz-sim-gui ruby parameter_bridge 2>/dev/null || true
    pkill -9 -f 'thruster_bridge.py' 2>/dev/null || true
}

trap cleanup EXIT INT TERM

# Ensure clean slate before launch
cleanup

ros2 launch hugr_gazebo sim.launch.py "$@"
