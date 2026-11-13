# Maritime Simulation Worlds (`circuit_world.sdf`)

This directory contains the 3D marine simulation worlds for the **SeaBotics Hugr Optimus** Autonomous Surface Vehicle (ASV) in **Gazebo Sim (Harmonic)**.

---

## 🌊 World Overview: `circuit_world.sdf`

`circuit_world.sdf` defines a complete maritime competition arena engineered for autonomous visual servoing, obstacle avoidance, and waypoint navigation.

### Key Simulation Systems & Physics

1. **Physics Engine Configuration (`<physics>`):**
   * **Solver:** DART (Dynamic Animation and Robotics Toolkit).
   * **Time Step (`max_step_size`):** $0.002\text{ s}$ ($500\text{ Hz}$ physics integration rate).
   * **Real-Time Factor (`real_time_factor`):** $1.0$ (calibrated for strictly real-time 1:1 execution).

2. **Core World Plugins:**
   * `gz::sim::systems::Physics`: Computes rigid-body dynamics, joint constraints, and contacts.
   * `gz::sim::systems::UserCommands`: Allows spawning, moving, and deleting models dynamically.
   * `gz::sim::systems::SceneBroadcaster`: Broadcasts world state to the Gazebo GUI and ROS bridges.
   * `gz::sim::systems::Sensors`: Powered by the **Ogre2 rendering engine** for physically based lighting, realistic water surface specular highlights, and hardware-accelerated RGB and Depth shader pipelines.

3. **Archimedes Buoyancy System (`gz-sim-buoyancy-system`):**
   * **Waterline Datum:** Fixed at $Z = 0.0\text{ m}$.
   * **Graded Fluid Density:**
     * Subsurface ($Z \le 0\text{ m}$): $\rho = 1000.0\text{ kg/m}^3$ (water).
     * Atmospheric ($Z > 0\text{ m}$): $\rho = 1.2\text{ kg/m}^3$ (air).
   * Automatically integrates the submerged hull collision volume of `hugr_optimus::base_link` and exerts the corresponding upward hydrostatic buoyant force.

4. **Environment & Visuals:**
   * **Ocean Plane:** $200\text{ m} \times 200\text{ m}$ reflective water surface with semi-transparent cyan marine shader (`ambient: 0.05 0.25 0.35`, `diffuse: 0.1 0.45 0.55`).
   * **Directional Sunlight:** Direction vector $(-0.5, 0.2, -1.0)$ with cast shadows and calibrated specular reflection.

---

## 🚩 Competition Course Layout & Buoy Coordinates

The course models a standard RoboBoat / Maritime RobotX navigation channel with slaloms, a hazardous obstacle, and a turnaround mark:

```
Y (North / Port)
 ▲
 │                          [Gate 2 Red] (15, 5.0)
5│                                 │
4│                                 │
3│                                 │                    [Gate 4 Red] (33, 2.5)
2│   [Gate 1 Red] (7, 2.2)         │                           │
1│            │             [Gate 2 Green] (15, 1.4)           │
0├──[Start]───┼───────────────[Orange Obs] (20, 0.8)───────────┼──────[Yellow Pivot] (42, 0.5)
-1│   (0,0)   │                                         [Gate 4 Green] (33, -1.5)
-2│  [Gate 1 Green] (7, -2.2)               [Gate 3 Red] (25, 0.4)
-3│                                                │
-4│                                         [Gate 3 Green] (25, -3.2)
 └────┴───────┴───────────────┴───────────────┴────────────────┴──────────────► X (East / Forward)
      0       7               15              25               33             42 meters
```

### Complete Buoy Coordinate Table

| Marker / Gate | Model Name | World Pose $(X, Y, Z)$ | Visual Color | Gate Width / Dimensions | Function |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Start / Spawn** | `hugr_optimus` | $(0.0, 0.0, 0.25)\text{ m}$ | Orange Hull | $35\text{ kg}$ Catamaran | Mission starting dock |
| **Gate 1 - Port** | `gate1_red_buoy` | $(7.0, +2.2, 0.4)\text{ m}$ | Red ($\text{RGB}: 1, 0, 0$) | $r = 0.25\text{ m}, h = 0.8\text{ m}$ | Entry Gate (Port marker) |
| **Gate 1 - Starboard**| `gate1_green_buoy` | $(7.0, -2.2, 0.4)\text{ m}$ | Green ($\text{RGB}: 0, 1, 0$) | Gate Width: $4.4\text{ m}$ | Entry Gate (Starboard marker) |
| **Gate 2 - Port** | `gate2_red_buoy` | $(15.0, +5.0, 0.4)\text{ m}$ | Red ($\text{RGB}: 1, 0, 0$) | $r = 0.25\text{ m}, h = 0.8\text{ m}$ | Port Slalom Gate (offset North) |
| **Gate 2 - Starboard**| `gate2_green_buoy` | $(15.0, +1.4, 0.4)\text{ m}$ | Green ($\text{RGB}: 0, 1, 0$) | Gate Width: $3.6\text{ m}$ | Port Slalom Gate |
| **Hazard Obstacle** | `obstacle_orange_buoy` | $(20.0, +0.8, 0.4)\text{ m}$ | Orange / Brown ($\text{RGB}: 0.85, 0.35, 0$) | $r = 0.28\text{ m}, h = 0.8\text{ m}$ | Mid-channel collision threat |
| **Gate 3 - Port** | `gate3_red_buoy` | $(25.0, +0.4, 0.4)\text{ m}$ | Red ($\text{RGB}: 1, 0, 0$) | $r = 0.25\text{ m}, h = 0.8\text{ m}$ | Starboard Chicane Gate (offset South) |
| **Gate 3 - Starboard**| `gate3_green_buoy` | $(25.0, -3.2, 0.4)\text{ m}$ | Green ($\text{RGB}: 0, 1, 0$) | Gate Width: $3.6\text{ m}$ | Starboard Chicane Gate |
| **Gate 4 - Port** | `gate4_red_buoy` | $(33.0, +2.5, 0.4)\text{ m}$ | Red ($\text{RGB}: 1, 0, 0$) | $r = 0.25\text{ m}, h = 0.8\text{ m}$ | Final Approach Gate |
| **Gate 4 - Starboard**| `gate4_green_buoy` | $(33.0, -1.5, 0.4)\text{ m}$ | Green ($\text{RGB}: 0, 1, 0$) | Gate Width: $4.0\text{ m}$ | Final Approach Gate |
| **Turnaround Mark** | `pivot_yellow_buoy`| $(42.0, +0.5, 0.6)\text{ m}$ | Yellow ($\text{RGB}: 1, 0.95, 0$) | $r = 0.35\text{ m}, h = 1.2\text{ m}$ | $180^\circ$ Turnaround / Rounding Pillar |

---

## 🧪 Syntax Validation & Testing

To test and validate `circuit_world.sdf` for XML syntax errors and schema conformance:

```bash
export GZ_SIM_RESOURCE_PATH="$(pwd)/../models"
gz sdf -k circuit_world.sdf
```
*Expected exit code:* `0` (clean schema validation without errors).

To inspect the world standalone in Gazebo Sim without ROS 2 nodes:
```bash
gz sim circuit_world.sdf
```
