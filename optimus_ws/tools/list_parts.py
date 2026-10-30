#!/usr/bin/env python3
import os
import trimesh

mesh_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/hugr_description/meshes"))
scene = trimesh.load(os.path.join(mesh_dir, "frame.step"))
print(f"Total parts in assembly: {len(scene.geometry)}")
for name in sorted(scene.geometry.keys()):
    geom = scene.geometry[name]
    verts = len(geom.vertices) if hasattr(geom, 'vertices') else 0
    c = [round(float(v), 3) for v in geom.centroid]
    print(f"  {name:30s} | Verts: {verts:6d} | Centroid: {c}")
