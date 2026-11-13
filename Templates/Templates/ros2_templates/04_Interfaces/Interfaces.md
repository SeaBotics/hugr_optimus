# Interface
A way to connect something physically or digirally.

We have:
- Messages `.msg` used in topics, Publish/Subcribe, one-way
- Services `.srv` used in Server/client -> Request/Respond, sync/async
- Actions `.action` used in actions, Goal, Result, feedback

## Finding the right msg type (Interface)
`ros2 interface list`

Common types: https://github.com/ros2/common_interfaces/tree/rolling
Also see:     https://github.com/ros2/rcl_interfaces

Supported datatypes for messages:
https://docs.ros.org/en/jazzy/Concepts/Basic/About-Interfaces.html

# Relevant msg for us


# Creating custom interfaces .msg and .srv
Rules: camelcase, start with capital letter in name.
Troubleshootig: Make sure IDE is up-to-date if opnened from unsourced enviornment.
Troubleshootig: Cpp, cutom msg may not be recognized in vscode. src -> .vscode -> c_cpp:properties.json -> "includePath" -> add the path to install folder where msg are. (pwd).

run `ros2 pkg create <package name> , ament does not need to be specified just use standrad cmake
make a msg folder or srv depending on case

use only
- package.xml
Always add:

<buildtool_depend>rosidl_default_generators</buildtool_depend>
<exec_depend>rosidl_default_runtime</exec_depend>
<member_of_group>rosidl_interface_packages</member_of_group>

- CMakeLists.txt
Does not need build things, add after find packages and before ament package.

find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/MyCustomMessage.msg"
  "srv/MyCustomService.srv"
)

ament_export_dependencies(rosidl_default_runtime)

**NB!** This gives a package we can add n amount of interfaces in the future.