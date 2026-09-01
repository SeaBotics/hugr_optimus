# How to set up a workspace in ROS2
Link: https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Creating-A-Workspace/Creating-A-Workspace.html

mkdir a workspace ros2_ws -> cd that workspace -> mkdir "src"
src is where everything will be made, and 3rd party packages are installed.

In ros2_ws you execute colcon build (ros-dev-tools) to build packages, checks the .xml file and dependencies.

- colcon build                          (Build all, most often first time to build all)
- colcon build --packages-select <name> (Specific package, save time)
- colcon build --symlink-install        (Makes symboliv link, like python, .xml, launch files etc, c/c++ still need to be compiled, best for protyping only)

After colcon build some other files like, build, install and log are generated:
    The install folder, there is a setup.bash here, hence when colcon builidng and having multiple ros2 projetcs you run "source install/setup.bash" from the root of the workspace.
    Note: You may add it to bashrc, but if you have multiple workspaces that may create issues.