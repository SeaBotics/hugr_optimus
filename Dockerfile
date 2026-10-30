# Ubuntu 24.04 LTS image with ROS 2 Jazzy
FROM osrf/ros:jazzy-desktop

# Container environment variables
ARG DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=jazzy

# Install of necessary packages for development (open for modification later, ask admin for extended list)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    nano \
    vim \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# User in environment setup
ARG USERNAME=ros
ARG USER_UID=1000
ARG USER_GID=$USER_UID

## User permissions in container (safely create user if missing)
RUN userdel -r ubuntu 2>/dev/null || true \
    && groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo "$USERNAME ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Setup workspace structure folder
ENV RWS_DIR=/home/$USERNAME/optimus_ws
RUN mkdir -p $RWS_DIR/src
WORKDIR $RWS_DIR

# Switch to non-root user, less chance of having user messing up within container
USER $USERNAME

# Automatically source ROS 2 and workspace on bash startup
RUN echo "source /opt/ros/$ROS_DISTRO/setup.bash" >> /home/$USERNAME/.bashrc \
    && echo "if [ -f /home/$USERNAME/optimus_ws/install/setup.bash ]; then source /home/$USERNAME/optimus_ws/install/setup.bash; fi" >> /home/$USERNAME/.bashrc
