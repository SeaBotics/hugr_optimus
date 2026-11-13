from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    ld = LaunchDescription()

    mypackage = Node(
        package="packagename",
        executable="packagename"
    )

    ld.add_action(mypackage)

    return ld