# Gazebo Docs
Technical Resources
For ROS2 Jazzy Jalisco we use gazebo Harmonic.

Documentation: https://gazebosim.org/docs/harmonic/getstarted/ 
Libraries: https://gazebosim.org/libs/ 
Videos: https://www.youtube.com/c/GazeboSim 
BlueROV2 Marine Environment: https://github.com/clydemcqueen/bluerov2_gz 

# About
Gazebo is a Physics simulator for Robotics, made by Open Robotics, the same Open Source Foundation behind ROS2.

It’s a high-fidelity 3D multi-robot physics simulator. It behaves as a virtual testbed, simulating physical forces, collisions, sensor outputs, and environmental factors so you can test robot software before deploying it to physical hardware.

It utilized the SDF format, and supports URDF.

Physics Engine: Simulates rigid-body dynamics, gravity, friction, drag, and contact forces (using solvers like DART or ODE).

Sensor Simulation: Generates realistic synthetic data for sensors (e.g., 2D/3D LIDAR, RGB-D cameras, IMUs, GPS) including noise models.

Environmental Modeling: Simulates wind, underwater currents (crucial for ArduSub/ROVs), light sources, and complex terrain.


# 1. Installation

Install Gazebo Harmonic along with all ROS2-to-Gazebo interface packages, the simulation bridge, and ros2_control integrations directly through apt:

sudo apt update
`# Install core simulation wrappers and bridge`
`sudo apt install ros-jazzy-ros-gz`
`# Install ros2_control integration for physical controllers`
`sudo apt install ros-jazzy-gz-ros2-control`

CLI Verification: Source your workspace to add the gz CLI tools to your path:

`source /opt/ros/jazzy/setup.bash`
`gz sim --version  # Should output Gazebo Sim, version 8.x (Harmonic)`

# 2. Launching Gazebo

To spin up a simulation world from a terminal, use the gz sim command:

## Launch GUI & World:

`ros2 launch ros_gz_sim gz_sim.launch.py rviz:=true`

Note: Running WSL2, Gazebo may get WARN or not start, try to close WSL2, → Windows Powershell → wsl --shutdown, then start Ubuntu and try again.