#!/bin/bash
# Hugr Optimus - Instant Model Hot-Reload
# Removes the current boat from the running Gazebo world and respawns it
# from the updated model.sdf without needing to restart Gazebo.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

source /opt/ros/jazzy/setup.bash
source "${WS_DIR}/install/setup.bash"

MODEL_SDF="${WS_DIR}/src/hugr_gazebo/models/hugr_optimus/model.sdf"

echo "=========================================================="
echo " [HOT-RELOAD] Reloading Hugr Optimus in Gazebo..."
echo "=========================================================="

# 1. Remove existing model from running simulation
echo "-> Removing current boat..."
gz service -s /world/circuit_world/remove \
  --reqtype gz.msgs.Entity \
  --reptype gz.msgs.Boolean \
  --timeout 2000 \
  --req 'name: "hugr_optimus", type: 2' > /dev/null 2>&1 || true

sleep 0.3

# 2. Respawn updated model from disk
echo "-> Spawning updated model from model.sdf..."
ros2 run ros_gz_sim create \
  -world circuit_world \
  -name hugr_optimus \
  -file "${MODEL_SDF}" \
  -z 0.25

echo "=========================================================="
echo " [OK] Boat reloaded with latest model.sdf parameters!"
echo "=========================================================="
