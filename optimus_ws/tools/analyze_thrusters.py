#!/usr/bin/env python3
import numpy as np

# CAD to ROS rotation:
# X_ros = -Y_cad
# Y_ros = +X_cad
# Z_ros = +Z_cad
T_cad_to_ros = np.array([
    [ 0.0, -1.0,  0.0],
    [ 1.0,  0.0,  0.0],
    [ 0.0,  0.0,  1.0]
])

# Thrusters transforms from scene graph:
thrusters = {
    "T_200 (Port Lateral)": {
        "cad_pos": np.array([0.15179662, -0.2323297, -0.33794996]),
        "R_cad": np.array([
            [-0.342020154,  0.939692617,  0.0],
            [ 0.0,          0.0,         -1.0],
            [-0.939692617, -0.342020154,  0.0]
        ])
    },
    "T_200_202 (Starboard Lateral)": {
        "cad_pos": np.array([-0.15179662, -0.2323297, -0.33794996]),
        "R_cad": np.array([
            [-0.342020154, -0.939692617,  0.0],
            [ 0.0,          0.0,         -1.0],
            [ 0.939692617, -0.342020154,  0.0]
        ])
    },
    "T_201 (Bow Transverse)": {
        "cad_pos": np.array([-0.00167903, -0.40658149, -0.296875]),
        "R_cad": np.array([
            [ 0.0,  0.0, -1.0],
            [ 0.0, -1.0,  0.0],
            [-1.0,  0.0,  0.0]
        ])
    },
    "T_200_203 (Stern Transverse)": {
        "cad_pos": np.array([-0.00167598,  0.28841853, -0.296875]),
        "R_cad": np.array([
            [ 0.0,  0.0, -1.0],
            [ 0.0, -1.0,  0.0],
            [-1.0,  0.0,  0.0]
        ])
    }
}

for name, data in thrusters.items():
    cad_pos = data["cad_pos"]
    ros_pos = T_cad_to_ros @ cad_pos
    R_cad = data["R_cad"]
    # What are the axes of this part in ROS?
    # Part local X, Y, Z in CAD:
    x_cad = R_cad[:, 0]
    y_cad = R_cad[:, 1]
    z_cad = R_cad[:, 2] # thruster propeller/cylinder axis in T200 part
    
    # In ROS:
    x_ros = T_cad_to_ros @ x_cad
    y_ros = T_cad_to_ros @ y_cad
    z_ros = T_cad_to_ros @ z_cad
    
    print(f"=== {name} ===")
    print(f"  ROS Position: X={ros_pos[0]:+.4f}, Y={ros_pos[1]:+.4f}, Z={ros_pos[2]:+.4f}")
    print(f"  Part local X axis in ROS: {np.round(x_ros, 4)}")
    print(f"  Part local Y axis in ROS: {np.round(y_ros, 4)}")
    print(f"  Part local Z axis (thrust axis) in ROS: {np.round(z_ros, 4)}")
    # Check orientation matrix in ROS: R_ros = T_cad_to_ros @ R_cad
    R_ros = T_cad_to_ros @ R_cad
    # Compute roll, pitch, yaw from R_ros
    pitch = np.arctan2(-R_ros[2, 0], np.sqrt(R_ros[0, 0]**2 + R_ros[1, 0]**2))
    yaw = np.arctan2(R_ros[1, 0], R_ros[0, 0])
    roll = np.arctan2(R_ros[2, 1], R_ros[2, 2])
    print(f"  Euler RPY (rad): roll={roll:.4f}, pitch={pitch:.4f}, yaw={yaw:.4f}")
    print(f"  Euler RPY (deg): roll={np.degrees(roll):.1f}, pitch={np.degrees(pitch):.1f}, yaw={np.degrees(yaw):.1f}")
    print()
