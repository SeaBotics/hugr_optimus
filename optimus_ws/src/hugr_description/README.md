# hugr_description

Robot description package for the **SeaBotics Hugr Optimus** Autonomous Surface Vessel.

---

## 📦 Contents

- **`urdf/`**: 
  - `hugr.urdf`: Formatted Unified Robot Description Format file describing the vessel, its coordinate frames, inertia, thrusters, and sensors.
  - `hugr.urdf.xacro`: Parameterized Xacro source file.
- **`meshes/`**:
  - `frame.stl`: Decimated, high-performance 3D CAD mesh ($12.5\text{ MB}$, 250k triangles) derived from the OnShape assembly STEP model.

---

## 📐 Coordinate Frames

All coordinates are aligned with standard maritime and ROS REP-103 conventions:
- $+X$: Proa / Forward (Surge)
- $+Y$: Babor / Port (Sway)
- $+Z$: Arriba / Up (Heave)

| Frame | Origin $(X, Y, Z)$ | Description |
| :--- | :--- | :--- |
| `base_footprint` | $(0, 0, 0)$ | Water surface projection at calm water |
| `base_link` | $(0, 0, 0.08)$ | Vessel Center of Gravity |
| `port_main_thruster_link` (M1) | $(-0.2323, +0.1518, -0.3379)$ | BlueRobotics T200 Port Surge Thruster |
| `starboard_main_thruster_link` (M2) | $(-0.2323, -0.1518, -0.3379)$ | BlueRobotics T200 Starboard Surge Thruster |
| `bow_transverse_thruster_link` (M3) | $(+0.2884, 0.0, -0.2969)$ | BlueRobotics T200 Bow Tunnel Thruster |
| `stern_transverse_thruster_link` (M4) | $(-0.4066, 0.0, -0.2969)$ | BlueRobotics T200 Stern Tunnel Thruster |
| `camera_link` | $(+0.4076, 0.0, +0.18)$ | Luxonis OAK-D Front Stereo Camera |
| `imu_link` | $(0.0, 0.0, -0.0184)$ | Xsens MTi IMU Sensor |
| `gps_link` | $(0.0, 0.0, +0.15)$ | GNSS / GPS Antenna |
