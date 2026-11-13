# Creating packages (C++)
Link: https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Creating-Your-First-ROS2-Package.html#

rosdep | tool in ros2 for installing dependencies declared in the package.xml file
- rosdep init                                        (First time pr. system installation)
- rosdep update                                      (Sometimes to sync database)
- rosdep install --from-paths src --ignore-src -y    (Do from root in workspace)

## C++
ros2 pkg create <name> --build-type ament_cmake --dependencies rclcpp
ament is a build system | rcl is ros client library, ros2 API

Follows very similar structure as normal c++ development.

### CMakeLists.txt
Build configuration file for C++ packages in ROS 2 using CMake and ament_cmake.

### package.xml 
Where dependencies and tests are declared for rosdep (Identical to python package.xml)

### src
where the .cpp filer are stored.

## Include
Where the header files are stored like .h or .hpp