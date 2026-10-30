# hugr_gazebo

ROS 2 Jazzy simulation package for the **SeaBotics Hugr Optimus** Autonomous Surface Vehicle (ASV) in **Gazebo Sim (Harmonic)**.

---

## 🌟 Key Features

1. **Authentic 3D Catamaran CAD Geometry:**
   - Visual mesh loaded directly from the OnShape assembly STEP model (`meshes/frame.stl`).
   - Exact mounting origins for all 4 BlueRobotics T200 thrusters, front Luxonis OAK-D camera, Xsens IMU, and GPS.

2. **Hydrodynamics & Buoyancy:**
   - Multi-layer fluid Archimedes buoyancy system (`gz-sim-buoyancy-system`) with water surface at $Z = 0\text{ m}$.
   - Faithful hull volume decomposition providing $63.4\text{ L}$ of pontoon displacement for the $28\text{ kg}$ vessel (equilibrium waterline draft $\approx 7.4\text{ cm}$).
   - Low center of mass ($Z = -0.26\text{ m}$) ensuring positive metacentric height ($GM > 0$) for self-righting stability.
   - Purely dissipative 6-DOF Fossen hydrodynamic damping eliminating numerical solver instabilities.

3. **Maritime Competition Circuit:**
   - **Gate 1:** Red $(8, 2)$ and Green $(8, -2)$ buoys.
   - **Gate 2:** Red $(18, 3)$ and Green $(18, -1)$ buoys.
   - **Turnaround Pivot:** Yellow $(28, 0)$ buoy for 360-degree circling.

4. **Bi-directional ROS 2 Bridge:**
   - Camera: `/camera/image_raw` (`sensor_msgs/msg/Image`)
   - IMU: `/imu/data` (`sensor_msgs/msg/Imu`)
   - GPS: `/fix` (`sensor_msgs/msg/NavSatFix`)
   - Clock: `/clock` (`rosgraph_msgs/msg/Clock`)
   - 4 Thrusters: `/hugr/thrusters/m[1-4]/cmd_thrust` (`std_msgs/msg/Float64`)

---

## 🚀 How to Launch

### 1. Standard 3D GUI Launch
From the workspace root (`optimus_ws`):

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch hugr_gazebo sim.launch.py
```
*(Or simply run `./run_gazebo.sh`)*

### 2. Headless Mode (Server-only / CI)
```bash
ros2 launch hugr_gazebo sim.launch.py headless:=true
```

---

## 📦 Package Structure

```tree
hugr_gazebo
├── CMakeLists.txt
├── package.xml
├── README.md
├── config
│   └── bridge.yaml              # ROS 2 <-> Gazebo Sim bridge definitions
├── launch
│   └── sim.launch.py            # Unified simulation launch script
├── models
│   └── hugr_optimus
│       ├── model.config         # Gazebo model metadata
│       ├── model.sdf            # Complete vessel SDF (CAD mesh + physics)
│       └── meshes
│           └── frame.stl        # Authentic 3D vessel frame mesh
└── worlds
    └── circuit_world.sdf        # Maritime ocean plane, sun, and competition buoys
```
