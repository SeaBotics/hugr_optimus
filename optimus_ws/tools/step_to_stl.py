#!/usr/bin/env python3
import sys
import os

mesh_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/hugr_description/meshes"))
step_path = os.path.join(mesh_dir, "frame.step")
stl_path = os.path.join(mesh_dir, "frame.stl")

print(f"Loading {step_path}...")
try:
    import trimesh
    mesh = trimesh.load(step_path)
    print("Trimesh loaded:", type(mesh))
    if isinstance(mesh, trimesh.Scene):
        mesh = mesh.dump(concatenate=True)
    mesh.export(stl_path)
    print(f"Exported successfully to {stl_path}!")
    sys.exit(0)
except Exception as e:
    print(f"Trimesh error: {e}")

# If trimesh lacks step backend, try gmsh python api
try:
    print("Trying Gmsh Python API...")
    import gmsh
    gmsh.initialize()
    gmsh.open(step_path)
    # Set fast 2D meshing options to prevent hanging on micro-fillets
    gmsh.option.setNumber("Mesh.Algorithm", 1) # MeshAdapt
    gmsh.option.setNumber("Mesh.MeshSizeMin", 5.0) # mm
    gmsh.option.setNumber("Mesh.MeshSizeMax", 50.0) # mm
    gmsh.option.setNumber("General.Verbosity", 2)
    gmsh.model.mesh.generate(2)
    gmsh.write(stl_path)
    gmsh.finalize()
    print(f"Gmsh successfully generated {stl_path}!")
    sys.exit(0)
except Exception as e:
    print(f"Gmsh Python error: {e}")
