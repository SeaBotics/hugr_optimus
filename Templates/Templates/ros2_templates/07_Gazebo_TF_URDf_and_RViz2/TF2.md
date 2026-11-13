# I - Transform for ROS2 (TF2)

TF2 is a ROS 2 standard library used to keep track of different coordinate systems (or frames) and their relationships over time.

*   **URDF:** TF2 uses the Unified Robot Description Format (URDF) to define different coordinate systems.
*   **Transformation:** Calculates the positions between frames.
*   **Buffer:** Saves a transform history so you can look up relations back in time.
*   **Broadcaster:** Publishes the relation between two frames.
*   **Listener:** Receives the transform information and allows the user to query relations.

---

## What is /robot_state_publisher
The URDF outputs the `robot_description`. The `joint_states` publishes `/joint_states (sensor_msgs/msg/JointState)`. `joint_state_publisher` and `joint_state_publisher_gui` can be used for artifical data to test movement, and publishes to `/joint_states`. The `robot_state_publisher` is important and calculates transforms and forward kinematics, takes  `/joint_states` + `/robot_description` and outputs `/tf` and `/tf_static`, they use `tf2_msgs/msg/TFMessage`. 

Tips: Visualize the robot: ros2 launch urdf_tutorial display.launch.py model:="my_robot"

---

## Tools & Commands

*   **View Framees:**
    ```bash
    ros2 run tf2_tools view_frames.py
    ```
*   **Report Transform:**
    ```bash
    ros2 run tf2_ros tf2_echo [source_frame] [target_frame]
    ```

---

## Math & Representation

TF2 uses $4 \times 4$ transformation matrices to represent the spatial relationship between frames:

$$
T = \begin{bmatrix} 
R & t \\ 
0 & 1 
\end{bmatrix}
$$

*   **$R$ (Rotation):** Represented as a quaternion (4 parameters: $x, y, z, w$) to avoid gimbal lock.
*   **$t$ (Translation):** 3D translation vector ($x, y, z$).
*   **Interpolation:** If timestamps do not match exactly, TF2 interpolates the transforms across time.

---

## Broadcasters & Topics

### Static Transformations
*   **Topic:** `/tf_static`
*   **Description:** Defines relationships between non-moving parts using a static broadcaster.
*   **Timestamping:** Setting `t.header.stamp = self.get_clock().now().to_msg()` is critical for sensors to trace when events occurred.

### Dynamic Transformations
*   **Topic:** `/tf`
*   **Description:** For relations that change over time. Requires a loop to constantly broadcast updated information.

---

## TF2 Listener & Trees

*   **TransformListener:** Used to access frame transformations. It creates a buffer of a specified duration to store incoming transforms.
*   **The TF2 Tree:** TF2 builds a coordinate tree. Tree structures do **not** allow closed loops (relationships must be one-to-many, never many-to-one). The `world` frame typically acts as the root.
*   **Lookup Transform:** Calling `lookup_transform` searches the buffer, matches the timestamps, resolves the frame chain, and calculates the relation. A timeout parameter can be set to block and wait for the transform to become available. This is useful for dealing with varying publish rates or network latency.

---

## Pose & Quaternions

### Pose
A Pose represents a spatial position and orientation at a single point in time.
*   **Mathematical representation:** $P = \{t, q\}$, where $t$ is the translation vector and $q$ is the orientation quaternion.
*   **Usage:** Sensors and state estimation filters (like Extended Kalman Filters - EKF) publish positions using pose data structures.
*   **Standard Message:** `geometry_msgs/msg/PoseStamped` (which includes header metadata like timestamps and frame IDs).

### Quaternions
A quaternion is a 4-tuple ($x, y, z, w$) representing 3D rotation. It is more compact than a $3 \times 3$ rotation matrix, avoids gimbal lock, and is highly efficient for computing three-dimensional rotations.