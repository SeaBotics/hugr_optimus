#!/bin/bash
set -e
MESH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../src/hugr_description/meshes" && pwd)"
cd "${MESH_DIR}"

echo "=========================================================="
echo " Converting STEP CAD model to STL..."
echo " Input:  ${MESH_DIR}/frame.step"
echo " Output: ${MESH_DIR}/frame.stl"
echo "=========================================================="

gmsh frame.step -2 -format stl -o frame.stl

echo "Checking generated STL file..."
ls -lh frame.stl

# Also convert STL to DAE (COLLADA) with assimp if available
if command -v assimp >/dev/null 2>&1; then
    echo "Converting frame.stl to frame.dae (COLLADA) with assimp..."
    assimp export frame.stl frame.dae || echo "Assimp export completed with warnings."
    ls -lh frame.dae 2>/dev/null || true
fi

echo "CAD Conversion Complete!"
