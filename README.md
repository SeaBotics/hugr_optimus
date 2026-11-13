# hugr_optimus

The official repository for the **SeaBotics Hugr Optimus**. This repo is the successor to the Hugr Primus repository for legacy code.

The Hugr Optimus is a fully autonomous surface vessel (ASV) built by students at the **University of Agder** to compete in national and international competitions.

---

## 📂 Repository Overview

```tree
hugr_optimus
├─ Dependencies   - External dependencies
├─ Documentations - Tasks, schematics, datasheets, etc.
├─ Misc           - Code examples: ROS2 in practice
├─ Templates      - ROS2 templates for different frameworks 
└─ optimus_ws     - Main workspace for Hugr Optimus
    ├─ scripts    - Quick-launch scripts for Linux/WSL2 and Windows
    ├─ tools      - Teleoperation, motor dashboard, and telemetry utilities
    └─ src
        ├─ hugr_gazebo        - 3D Gazebo Sim (Harmonic) maritime simulation
        ├─ hugr_sim           - 2D Fossen SITL hydrodynamic simulator + RViz2
        ├─ hugr_description   - URDF model, coordinate frames & 3D CAD meshes
        ├─ hugr_autonomy      - Autonomous waypoint navigation (LOS guidance)
        ├─ thrust_allocation  - 4-thruster allocation matrix (cmd_vel -> PWMs)
        ├─ signal_tower       - Safety signal tower indicator node
        └─ xsens_mti_driver   - Xsens MTi IMU driver
```

---

## ⚡ Quickstart: Simulation & Development

### 1. Requirements
- Ubuntu 24.04 (native or WSL2)
- ROS 2 Jazzy Jalisco
- Gazebo Sim Harmonic (`sudo apt install -y ros-jazzy-ros-gz ros-jazzy-ros-gz-sim ros-jazzy-ros-gz-bridge`)

### 2. Build the Workspace
From the `optimus_ws` directory:

```bash
cd optimus_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

### 3. Launching Simulations

- **3D Gazebo Sim (Harmonic) with water buoyancy, sensors & competition circuit:**
  ```bash
  ./run_gazebo.sh
  # or directly: ros2 launch hugr_gazebo sim.launch.py
  ```

- **Fast 2D Fossen SITL Simulator with RViz2:**
  ```bash
  ./run_simulation.sh
  # or directly: ros2 launch hugr_sim sim.launch.py
  ```

### 4. Teleoperation & Testing
All convenience launchers are available in `optimus_ws/scripts/`:
- **Keyboard Teleop:** `bash scripts/run_teleop.sh`
- **Gamepad / Joystick:** `bash scripts/run_joystick.sh` (or `scripts/run_gamepad_teleop.bat` on Windows)
- **Motor Web Dashboard:** `bash scripts/run_motor_dashboard.sh` (open `http://localhost:8080`)
- **Autonomous Navigation:** `bash scripts/run_autonomy.sh`
