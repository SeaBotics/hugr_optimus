# Hugr Optimus - Gazebo Digital Twin (`model.sdf`)

This folder contains the complete **Gazebo Sim (Harmonic)** physics, visual, collision, sensor, and propulsion model for the **SeaBotics Hugr Optimus** Autonomous Surface Vehicle (ASV).

---

## 📁 Model Folder Structure

```text
hugr_optimus/
├── model.config               # Gazebo model identification manifest & metadata
├── model.sdf                  # Complete SDF 1.9 digital twin specification
├── README.md                  # This technical documentation
└── meshes/
    └── frame.stl              # High-resolution 3D CAD surface mesh from OnShape assembly
```

---

## ⚓ 1. Naval Architecture & Mass Properties

The physical parameters of `hugr_optimus` were extracted from the OnShape CAD assembly and calibrated against physical tank tests:

| Parameter | Value in `model.sdf` | Physical Explanation |
| :--- | :--- | :--- |
| **Total Vessel Mass** | $35.0\text{ kg}$ | Hull, crossbars, electronics enclosure, battery, payload & thrusters. |
| **Center of Gravity ($CoG$)** | $(-0.04, 0.0, -0.30)\text{ m}$ | Located deep between the pontoons, well below the waterline ($Z = 0.0\text{ m}$). |
| **Roll Inertia ($I_{xx}$)** | $2.5\text{ kg}\cdot\text{m}^2$ | Moment of inertia about longitudinal axis (narrow beam dynamics). |
| **Pitch Inertia ($I_{yy}$)**| $4.8\text{ kg}\cdot\text{m}^2$ | Moment of inertia about transverse axis (resists bow diving). |
| **Yaw Inertia ($I_{zz}$)**  | $5.5\text{ kg}\cdot\text{m}^2$ | Moment of inertia about vertical axis (directional steering stability). |
| **Total Displacement** | $57.6\text{ liters}$ ($57.6\text{ kg}$) | Maximum buoyancy capacity across twin pontoons before full submersion. |
| **Operating Draft** | $\sim 60.7\%$ submerged | $35.0\text{ kg} / 57.6\text{ kg}$: Pontoon bottoms sit $\approx 15\text{ cm}$ below water. |
| **Metacentric Stability** | Positive ($GM > 0$) | **Self-righting**: If tilted by waves or rudder torque, gravity and buoyancy create an immediate restoring torque ($GZ > 0$) returning the vessel upright. |

---

## 🏗️ 2. Visual & Collision Architecture

### Visual Geometry (`<visual>`)
* **Mesh:** Loaded directly from [`meshes/frame.stl`](meshes/frame.stl).
* **Coordinate Alignment:** Uses `<pose>0 0 0 0 0 -1.5708</pose>` ($-90^\circ$ rotation about $Z$) to transform the OnShape CAD modeling frame into the standard ROS/Gazebo **REP-103 convention** ($+X$ forward, $+Y$ port, $+Z$ up).
* **Color / PBR Shader:** Safety-orange marine coating (`ambient: 0.92 0.40 0.06`, `diffuse: 0.96 0.45 0.08`, `specular: 0.6 0.6 0.6`).
* **Sensor Housing:** Visual indicator for the front Luxonis OAK-D camera enclosure on the mast.

### Collision Geometry (`<collision>`)
To maintain a high-speed $500\text{ Hz}$ physics solver step size without CPU bottlenecks, the complex STL mesh is **not** used for collision detection. Instead, the hull is broken down into **9 convex analytical box primitives**:

1. `port_pontoon_collision` & `starboard_pontoon_collision`: Twin main pontoon cylinders ($0.50\text{ m} \times 0.24\text{ m} \times 0.24\text{ m}$) providing primary Archimedes buoyancy.
2. `port_bow_collision` & `starboard_bow_collision`: Tapered forward wedges pitched at $0.20\text{ rad}$ ($11.5^\circ$) to push water aside cleanly.
3. `front_crossbeam_collision` & `rear_crossbeam_collision`: Structural aluminum crossbars connecting the twin pontoons.
4. `electronics_box_collision`: Central watertight enclosure ($0.30\text{ m} \times 0.28\text{ m} \times 0.12\text{ m}$) housing the flight computer and batteries.
5. `bow_center_collision` & `stern_center_collision`: Mounting brackets for sensors and transverse tunnel thrusters.

---

## 📡 3. Sensor Suite (Sim2Real Parity)

Mounted at exact physical positions matching the physical prototype:

| Sensor Element | Type in SDF | Simulated Rate | ROS 2 Output Topic | Output Encoding & Data |
| :--- | :--- | :--- | :--- | :--- |
| **Front RGB Camera** | `camera` | $20\text{ Hz}$ | `/oak/rgb/image_raw` | $1280 \times 720$ BGR8, $HFOV = 80^\circ$ ($1.396\text{ rad}$), pitch $-4.6^\circ$ ($0.08\text{ rad}$) down |
| **Front Depth Camera** | `depth_camera` | $15\text{ Hz}$ | `/oak/stereo/image_raw` | $1280 \times 720$ `R_FLOAT32` metric distance in meters (range: $0.2\text{ m}$ to $50.0\text{ m}$) |
| **Inertial Unit (IMU)** | `imu` | $100\text{ Hz}$ | `/imu/data` | Orientation quaternion, 3-axis angular rates ($\text{rad/s}$), and linear accelerations ($\text{m/s}^2$) |
| **RTK GNSS Receiver** | `navsat` | $10\text{ Hz}$ | `/gnss` | NavSatFix coordinates (Latitude, Longitude, Altitude) |

---

## ⚙️ 4. Propulsion Architecture (4 Thrusters)

Coordinates extracted from the OnShape assembly STEP file:

| Thruster | Link / Joint | Position $(X, Y, Z)$ | Thrust Axis | Primary Function |
| :--- | :--- | :--- | :--- | :--- |
| **M1** | `m1_link` / `m1_joint` | $(-0.2323, +0.1518, -0.3379)\text{ m}$ | Along $+X$ (Forward) | Port main propulsion & differential yaw |
| **M2** | `m2_link` / `m2_joint` | $(-0.2323, -0.1518, -0.3379)\text{ m}$ | Along $+X$ (Forward) | Starboard main propulsion & differential yaw |
| **M3** | `m3_link` / `m3_joint` | $(+0.2884, 0.0000, -0.2969)\text{ m}$ | Along $+Y$ (Lateral) | Bow transverse tunnel thruster (sway) |
| **M4** | `m4_link` / `m4_joint` | $(-0.4066, 0.0000, -0.2969)\text{ m}$ | Along $+Y$ (Lateral) | Stern transverse tunnel thruster (sway) |

* **Plugin:** `gz::sim::systems::Thruster` on each motor joint.
* **Hydrodynamic Thruster Parameters:** `fluid_density = 1000.0`, `propeller_diameter = 0.10 m`, `thrust_coefficient = 0.02`.

---

## 🌊 5. 6-DOF Fossen Hydrodynamic Damping

Water resistance is simulated using Thor I. Fossen's non-linear maneuvering model:
$$\mathbf{M} \dot{\mathbf{\nu}} + \mathbf{C}(\mathbf{\nu})\mathbf{\nu} + \mathbf{D}(\mathbf{\nu})\mathbf{\nu} = \mathbf{\tau}$$
Where the damping matrix combines linear friction and quadratic drag:

```xml
<plugin name="gz::sim::systems::Hydrodynamics" filename="gz-sim-hydrodynamics-system">
  <link_name>base_link</link_name>
  <!-- Linear Damping (Absorbs low-speed oscillations and roll wobble) -->
  <xU>-15.0</xU>   <yV>-35.0</yV>   <zW>-80.0</zW>
  <kP>-25.0</kP>   <mQ>-35.0</mQ>   <nR>-15.0</nR>

  <!-- Quadratic Drag (Limits top speed smoothly and models high-speed turbulence) -->
  <xUabsU>-20.0</xUabsU> <yVabsV>-50.0</yVabsV> <zWabsW>-80.0</zWabsW>
  <kPabsP>-20.0</kPabsP> <mQabsQ>-30.0</mQabsQ> <nRabsR>-18.0</nRabsR>
</plugin>
```

> **Numerical Energy Dissipation:** All coefficients are strictly negative ($\mathbf{\nu}^T \mathbf{D} \mathbf{\nu} \le 0$). This guarantees **unconditional Lyapunov numerical stability**, preventing physics solver explosions or unnatural jittering at any speed.

---

## 📊 6. Odometry Telemetry Publisher

* **Plugin:** `gz::sim::systems::OdometryPublisher`
* **Topic:** `/model/hugr_optimus/odometry` (`nav_msgs/msg/Odometry`) at $50\text{ Hz}$.
* **Frame:** `odom` $\rightarrow$ `base_link`.
* Provides uncorrupted 3D ground truth state (position, linear velocities, orientation quaternion, and angular velocity) to benchmark state estimators (EKF/UKF) and controllers.

---

## 🧪 Syntax Validation & Testing

To validate `model.sdf` for schema compliance:

```bash
gz sdf -k model.sdf
```
*Expected output:* `Valid.`
