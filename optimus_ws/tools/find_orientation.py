#!/usr/bin/env python3
import os
import trimesh

mesh_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/hugr_description/meshes"))
step_path = os.path.join(mesh_dir, "frame.step")

print("Inspecting Scene nodes in STEP...")
scene = trimesh.load(step_path)
for name, geom in scene.geometry.items():
    if "OAK" in name.upper() or "CAMERA" in name.upper() or "ENCLOSURE" in name.upper():
        print(f"Found Camera node: {name}")
        print("  Bounds:", geom.bounds)
        print("  Centroid:", geom.centroid)

# Also check overall bounds of components
print("\nTop 5 largest sub-geometries:")
sorted_geoms = sorted(scene.geometry.items(), key=lambda x: len(x[1].vertices) if hasattr(x[1], 'vertices') else 0, reverse=True)[:5]
for name, geom in sorted_geoms:
    print(f"Node: {name} | Verts: {len(geom.vertices)} | Bounds: {[round(float(v), 3) for v in geom.bounds[0]]} to {[round(float(v), 3) for v in geom.bounds[1]]}")
