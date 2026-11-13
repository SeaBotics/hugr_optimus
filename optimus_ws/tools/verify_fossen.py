#!/usr/bin/env python3
import sys
import os

ws_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ws_dir, "src/hugr_sim"))

try:
    import rclpy
    from hugr_sim.fossen_sim_node import FossenSimNode
    params_file = os.path.join(ws_dir, "src/hugr_sim/config/fossen_params.yaml")
    rclpy.init(args=["--ros-args", "--params-file", params_file])
    node = FossenSimNode()
    print("[SUCCESS] FossenSimNode initialized and loaded fossen_params.yaml successfully!")
    print(f"  Waves enabled: {node.enable_waves}")
    print(f"  Significant height: {node.wave_hs} m")
    print(f"  Wave length: {node.wave_len} m")
    print(f"  Buoys in field: {len(node.competition_buoys)}")
    node.destroy_node()
    rclpy.shutdown()
except Exception as e:
    print("[ERROR]", e)
    sys.exit(1)
