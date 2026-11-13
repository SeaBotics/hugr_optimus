#!/usr/bin/env python3
import subprocess
import os

urdf_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/hugr_description/urdf"))
xacro_file = os.path.join(urdf_dir, "hugr.urdf.xacro")
urdf_file = os.path.join(urdf_dir, "hugr.urdf")

print("Rendering:", xacro_file, "->", urdf_file)
res = subprocess.run(["xacro", xacro_file, "-o", urdf_file], capture_output=True, text=True)
if res.returncode == 0:
    print("URDF generated successfully!")
else:
    print("Error:", res.stderr)
