#!/usr/bin/env python3
import os
import trimesh

mesh_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/hugr_description/meshes/frame.stl"))
m = trimesh.load(mesh_path)
print("Mesh file:", mesh_path)
print(f"File size: {os.path.getsize(mesh_path) / (1024*1024):.2f} MB")
print("Vertices:", len(m.vertices), "Faces:", len(m.faces))
print("Bounds min:", [round(float(x), 4) for x in m.bounds[0]])
print("Bounds max:", [round(float(x), 4) for x in m.bounds[1]])
print("Extents (Size X, Y, Z):", [round(float(x), 4) for x in m.extents])
print("Centroid:", [round(float(x), 4) for x in m.centroid])
