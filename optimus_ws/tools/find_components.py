#!/usr/bin/env python3
import os
import trimesh
import numpy as np

mesh_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/hugr_description/meshes"))
step_path = os.path.join(mesh_dir, "frame.step")

scene = trimesh.load(step_path)
T_cad_to_ros = np.array([
    [ 0.0, -1.0,  0.0],
    [ 1.0,  0.0,  0.0],
    [ 0.0,  0.0,  1.0]
])

targets = ["T_20", "Lysstolpe", "IMU", "MTi", "Antenne", "OKE-D", "Jetson", "LiFePO4"]

print("=== KEY COMPONENT POSITIONS IN ROS ENU ===")
for node_name in scene.graph.nodes_geometry:
    transform, geom_name = scene.graph[node_name]
    if any(t.lower() in geom_name.lower() or t.lower() in node_name.lower() for t in targets):
        t_pos = transform[:3, 3]
        ros_pos = T_cad_to_ros @ t_pos
        print(f"[{geom_name:30s}] Node: {node_name:25s} -> ROS pos: X={ros_pos[0]:+.4f}, Y={ros_pos[1]:+.4f}, Z={ros_pos[2]:+.4f}")
