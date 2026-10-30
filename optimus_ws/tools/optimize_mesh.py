#!/usr/bin/env python3
import os
import trimesh

mesh_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/hugr_description/meshes"))
stl_full = os.path.join(mesh_dir, "frame_full.stl")
stl_opt = os.path.join(mesh_dir, "frame.stl")
dae_opt = os.path.join(mesh_dir, "frame.dae")

# Rename current 94MB stl to frame_full.stl if not already done
if not os.path.exists(stl_full):
    os.rename(stl_opt, stl_full)

print("Loading full mesh for optimization...")
m = trimesh.load(stl_full)
print(f"Original faces: {len(m.faces)}, vertices: {len(m.vertices)}")

# Simplify to ~200,000 faces (plenty for high quality CAD render, fast in RViz)
target_faces = 250000
if len(m.faces) > target_faces:
    print(f"Decimating mesh to ~{target_faces} faces for smooth 60fps RViz rendering...")
    # Fast decimation using trimesh / fast-simplification or open3d if available
    try:
        import fast_simplification
        pts, tris = fast_simplification.simplify(m.vertices, m.faces, target_reduction=(1.0 - target_faces/len(m.faces)))
        m_opt = trimesh.Trimesh(vertices=pts, faces=tris)
    except Exception as e:
        print(f"Simplification note: {e}")
        m_opt = m
else:
    m_opt = m

print(f"Exporting optimized mesh: {len(m_opt.faces)} faces...")
m_opt.export(stl_opt)
print(f"Optimized STL size: {os.path.getsize(stl_opt) / (1024*1024):.2f} MB")

# Also export DAE with proper material
try:
    m_opt.export(dae_opt)
    print(f"Exported DAE: {dae_opt}")
except Exception as e:
    print(f"DAE export note: {e}")
