# Downloads every single dependency required of all ROS Nodes

# ROS2 Jazzy
locale 

sudo apt update && sudo apt install locales

sudo locale-gen en_US en_US.UTF-8

sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8

export LANG=en_US.UTF-8

locale 

sudo apt install software-properties-common

sudo add-apt-repository universe

sudo apt update && sudo apt install curl -y

export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F'"' '{print $4}')

curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"

sudo dpkg -i /tmp/ros2-apt-source.deb

grep Suites /etc/apt/sources.list.d/ubuntu.sources

sudo apt clean && sudo apt update && sudo apt full-upgrade -y

sudo apt update && sudo apt install ros-dev-tools

sudo apt update

sudo apt install ros-jazzy-ros-base

source /opt/ros/jazzy/setup.bash

echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc

# Depthai ROS2
sudo python3 -m pip install depthai --break-system-packages
sudo apt install ros2-testing-apt-source
sudo apt update
sudo apt install ros-$ROS_DISTRO-depthai-ros-v3

# Ultralytics systemwide
sudo pip install ultralytics --break-system-packages

# Foxglove Bridge
sudo apt install ros-$ROS_DISTRO-foxglove-bridge

