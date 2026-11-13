# Creating packages (Python)
Link: https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Creating-Your-First-ROS2-Package.html#

rosdep | tool in ros2 for installing dependencies declared in the package.xml file
- rosdep init                                        (First time pr. system installation)
- rosdep update                                      (Sometimes to sync database)
- rosdep install --from-paths src --ignore-src -y    (Do from root in workspace)

## Python
ros2 pkg create <name> --build-type ament_python --dependencies rclpy
ament is a build system | rcl is ros client library, ros2 API

From the standard setup cd into the package

### package
A folder with the same name as the package -> Here goes you code, and there is a empty __init__.py -> marks the directory as a Python package so the interpreter recognizes it for module imports. Without this file, the ROS 2 build system and Python runtime cannot resolve module paths within the workspace.

### resource and test folder (Best not to change)
The resource folder has an empty "tag" with the same name as the package without any file type. It is a tag for ros2, best to let be.

### package.xml
Where dependencies and tests are declared for rosdep

### setup.cfg 
Usually do not change, but if you change the package name, change it in this file or else ros2 colcon build fails. Tells Python and ROS 2 where to put executable scripts.

### setup.py
Main configuration script for building Python packages using setuptools in ROS 2.

Add nodes: 
entry_points={
    'console_scripts': [
        'node_name = package_name.module_name:main',
    ],
}

Note: node_name you can cakk whatever, does not need to match package but good practice
Note: package_name must match the names of the package and is listed in packages[] in setup.py

The find packages replaced with packages=[package_name],

## NB! Always colcon build in root