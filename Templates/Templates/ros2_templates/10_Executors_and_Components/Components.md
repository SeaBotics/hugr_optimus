# Components - Composition & Zero-Copy Architecture
Running multiple nodes from a single executable via a Component Container. Reduces power and memory overhead with large node counts.

Intra-Process Communication (IPC): Bypasses the DDS middleware stack for co-located nodes. Messages pass via shared pointers (zero-copy) instead of serializing, deserializing, and copying data across network or process boundaries.

Inter-Process Zero-Copy (DDS / Shared Memory): When nodes run in separate processes on the same machine, zero-copy is still achievable via specific RMW implementations (e.g., Fast DDS with Loaned Messages or Eclipse Iceoryx) using shared memory segments instead of network sockets.

## When to Use vs. When NOT to Use
### Use Composition & Zero-Copy When:
Resource-Constrained Embedded Systems: Maximizing CPU efficiency and memory bandwidth on edge hardware.

High-Frequency Sensor Streams: Processing heavy data (LiDAR, high-res cameras, IMUs) where serialization bottlenecks throughput and increases latency.

Production Deployment: Bridging the gap from modular prototyping to deterministic, industrial-grade performance.

C++ Environments: Leveraging native shared-library plugin architectures (rclcpp_components).

### Do NOT Use Composition & Zero-Copy When:
Fault Isolation is Critical: If a segmentation fault or crash in one node brings down the entire container process. Standalone processes isolate failures.

Debugging and Profiling: Single-process debugging with multithreading is significantly harder (race conditions, deadlocks) than isolating individual nodes.

Language Agnosticism Required: Mixing Python nodes into the same in-process zero-copy pipeline (Python components cannot use intra-process zero-copy shared pointers).

Distributed Multi-Machine Architectures: Nodes that inherently need to run on separate physical hardware units (DDS network transport is mandatory here).

## More
Buffer error, exceeding limits may not be caused my using DDS instead of IPC, but may be of wromng QoS setup. Where single threaeded callbacks may take too lon.