import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory("signal_tower")
    config_file = os.path.join(pkg_share, "config", "signal_tower_params.yaml")

    return LaunchDescription([
        Node(
            package="signal_tower",
            executable="signal_tower_node",
            name="signal_tower_node",
            parameters=[config_file],
            output="screen",
            emulate_tty=True
        )
    ])
