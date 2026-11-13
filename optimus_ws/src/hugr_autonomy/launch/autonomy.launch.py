import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    pkg_share = get_package_share_directory('hugr_autonomy')
    params_path = os.path.join(pkg_share, 'config', 'autonomy_params.yaml')

    waypoint_navigator_node = Node(
        package='hugr_autonomy',
        executable='waypoint_navigator',
        name='waypoint_navigator',
        output='screen',
        parameters=[params_path]
    )

    return LaunchDescription([
        waypoint_navigator_node
    ])
