# Downloads every single dependency required of all ROS Nodes
# Depthai ROS2
sudo python3 -m pip install depthai --break-system-packages
sudo apt install ros2-testing-apt-source
sudo apt update
sudo apt install ros-$ROS_DISTRO-depthai-ros-v3

# Ultralytics systemwide
sudo pip install ultralytics --break-system-packages

# Foxglove Bridge
sudo apt install ros-$ROS_DISTRO-foxglove-bridge

