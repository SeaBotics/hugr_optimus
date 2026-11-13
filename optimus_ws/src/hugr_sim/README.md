# hugr_sim

Fast 2D Software-In-The-Loop (SITL) Marine Simulation package for the **SeaBotics Hugr Optimus**.

---

## 🌊 Overview

`hugr_sim` implements a real-time hydrodynamic physics simulator based on **Thor I. Fossen's non-linear 3-DOF marine maneuvering model** (Surge, Sway, Yaw). It is specifically tailored for rapid algorithm testing, autonomous waypoint navigation, and controller tuning without requiring full 3D rendering overhead.

### Key Capabilities
- **Hydrodynamic Physics:** Non-linear Coriolis terms, quadratic drag, and linear damping based on measured hull parameters.
- **RViz2 Integration:** Publishes vessel coordinate frames, catamaran 3D CAD mesh, and animated thruster vectors.
- **Telemetry Topics:**
  - Subscribes: `/motor_pwms` (`std_msgs/msg/Int32MultiArray`, PWM $1100-1900\ \mu\text{s}$)
  - Publishes: `/odom` (`nav_msgs/msg/Odometry`), `/imu/data` (`sensor_msgs/msg/Imu`), `/fix` (`sensor_msgs/msg/NavSatFix`)

---

## 🚀 How to Launch

From the workspace root (`optimus_ws`):

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch hugr_sim sim.launch.py
```
*(Or simply run `./run_simulation.sh`)*
