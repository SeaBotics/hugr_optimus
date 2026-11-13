#!/usr/bin/env python3
import os
import trimesh
import numpy as np

mesh_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/hugr_description/meshes"))
step_path = os.path.join(mesh_dir, "frame.step")

print("Loading CAD model to inspect the 4 T200 Thrusters...")
scene = trimesh.load(step_path)

thruster_nodes = []
for name, geom in scene.geometry.items():
    if "T_20" in name or "THRUSTER" in name.upper() or "T200" in name.upper():
        thruster_nodes.append((name, geom))

print(f"Found {len(thruster_nodes)} thruster related nodes:")
for name, geom in thruster_nodes:
    c = geom.centroid
    bounds = geom.bounds
    extents = geom.extents
    # Map to ROS ENU coordinates:
    # X_ros = -Y_cad
    # Y_ros = +X_cad
    # Z_ros = +Z_cad
    c_ros = np.array([-c[1], c[0], c[2]])
    print(f"\nPart: {name}")
    print(f"  CAD Centroid: X={c[0]:+.4f}, Y={c[1]:+.4f}, Z={c[2]:+.4f}")
    print(f"  ROS Centroid: X={c_ros[0]:+.4f}, Y={c_ros[1]:+.4f}, Z={c_ros[2]:+.4f}")
    print(f"  Bounds: min={[round(float(v), 3) for v in bounds[0]]} max={[round(float(v), 3) for v in bounds[1]]}")
    print(f"  Extents: {[round(float(v), 3) for v in extents]}")

# Also check scene graph transforms (nodes in scene.graph)
print("\n--- Inspecting Scene Graph Node Transforms for T200 ---")
for node_name in scene.graph.nodes_geometry:
    transform, geom_name = scene.graph[node_name]
    if "T_20" in geom_name or "THRUSTER" in geom_name.upper():
        t_pos = transform[:3, 3]
        ros_pos = np.array([-t_pos[1], t_pos[0], t_pos[2]])
        print(f"Node: {node_name} -> Geom: {geom_name}")
        print(f"  CAD Translation: {t_pos}")
        print(f"  ROS Position (X_ros=-Y_cad, Y_ros=+X_cad, Z_ros=+Z_cad): X={ros_pos[0]:+.4f}, Y={ros_pos[1]:+.4f}, Z={ros_pos[2]:+.4f}")
        # Rotation matrix
        R = transform[:3, :3]
        print(f"  Rotation Matrix:\n{R}")
