#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=========================================================="
echo " Starting Hugr Optimus Motor Dashboard..."
echo " Topic: /motor_pwms"
echo " Web UI: http://localhost:8080"
echo "=========================================================="
source /opt/ros/jazzy/setup.bash
source "${WS_DIR}/install/setup.bash"
python3 "${WS_DIR}/tools/motor_dashboard.py"
