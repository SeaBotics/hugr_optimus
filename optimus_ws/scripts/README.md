# SeaBotics Hugr Optimus - Launch & Test Scripts

This folder contains helper scripts to run simulations, teleoperation, testing, and autonomy on both Linux (WSL2 / native Ubuntu) and Windows.

## 🚀 Simulation Launchers

| Script (Linux) | Script (Windows) | Description |
| :--- | :--- | :--- |
| `run_gazebo.sh` | `run_gazebo.bat` | **Gazebo Sim (Harmonic)** 3D maritime world with water buoyancy, competition buoys, sensors (Camera, IMU, GPS), BlueRobotics T200 thrusters, and ROS 2 parameter bridge. |
| `reload_boat.sh` | `reload_boat.bat` | **Instant Hot-Reload**: Deletes and respawns the boat with latest `model.sdf` parameters in 1s without restarting Gazebo. |
| `run_simulation.sh` | `run_simulation.bat` | **Fossen SITL Simulator** fast 2D non-linear 3-DOF maneuvering simulation visualized in RViz2. |

## 🕹️ Control & Teleoperation

| Script (Linux) | Script (Windows) | Description |
| :--- | :--- | :--- |
| `run_teleop.sh` | `run_teleop.bat` | Standard keyboard control (`teleop_twist_keyboard`) commanding surge and yaw. |
| `run_joystick.sh` | `run_joystick.bat` | Gamepad joystick controller and thrust allocation node. |
| — | `run_gamepad_teleop.bat` | Direct Windows gamepad teleoperation reading Xbox / DirectInput controller and bridging to ROS 2. |
| `run_motor_dashboard.sh` | `run_motor_dashboard.bat` | Web-based real-time motor monitor and telemetry dashboard (port 8080). |
| — | `control_motors.bat` | Interactive terminal console to test manual motor PWM pulses. |

## 🧭 Autonomy & Navigation

| Script (Linux) | Script (Windows) | Description |
| :--- | :--- | :--- |
| `run_autonomy.sh` | `run_autonomy.bat` | Line-of-Sight (LOS) waypoint follower responding to 2D Goal Pose in RViz2. |
| — | `start_circuit.bat` | Automatically starts the autonomous competition buoy circuit (Gate 1, Gate 2, Yellow pivot buoy, return home). |
| — | `send_destination.bat` | CLI helper to send custom waypoints (e.g. `--x 15.0 --y 20.0` or `--lat ... --lon ...`). |
| — | `test_motors.bat` | Automated test suite verifying thruster allocation and odometry telemetry. |
