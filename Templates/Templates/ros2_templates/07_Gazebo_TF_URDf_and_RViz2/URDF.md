# Unified Robot Description Format
Describes the elements of the robot
Used to geenrate Transforms (TF)
Uses .xml format

Visualize in RViz2 is good

Most important of URDF -> assemble 2 links with a joint

Great tool -> Robot Developer Extensions for URDF, allows intellisense with VSCode and Preview of the URDF Model.

<?xml version="1.0"?>
<robot name="my_robot">

    <link name="base_link>
        <viual>
            <geometry>
                <box size="0.6 0.2 0.4" />
            </geometry>
            <origin xyz="0 0 0.1" rpy="0 0 0" />
        </visual>
    </link>
</robot>

view models with:
`ros2 launch urdf_tutorial display.launch.py model:=<myrobot>`

## URDF Package
It is normal practice to make a folder for the URDF models
`ros2 pkg create my_robot_descritpion`
- package.xml    <- keep unchanged
- CMakeLists.txt <- install (DIRECTORY urdf
DESTINATION share/${PROJECT_NAME}
)
- urdf           <- put the urdf model here

### Launch file for the Robot Description
- Have a dedicated launch package
<launch> <node> <param>

Offsetting the visual is no the same as the coordinate syste
issue often people change visual as it seems the 3d model swaps place, but the urdf model does not care
**NB!** CHange the origin of the joint to change the physics not visual therefore set 0 0 0 always 

Documentation for URDF:
https://wiki.ros.org/urdf

https://wiki.ros.org/urdf/XML/joint
https://wiki.ros.org/urdf/XML/link