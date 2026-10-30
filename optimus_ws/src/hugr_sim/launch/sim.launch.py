import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration
from launch.conditions import IfCondition
from launch_ros.actions import Node

def generate_launch_description():
    desc_pkg = get_package_share_directory('hugr_description')
    sim_pkg = get_package_share_directory('hugr_sim')

    urdf_file = os.path.join(desc_pkg, 'urdf', 'hugr.urdf')
    xacro_file = os.path.join(desc_pkg, 'urdf', 'hugr.urdf.xacro')
    rviz_config_path = os.path.join(desc_pkg, 'rviz', 'hugr.rviz')
    params_path = os.path.join(sim_pkg, 'config', 'fossen_params.yaml')

    use_rviz = LaunchConfiguration('use_rviz', default='true')

    if os.path.exists(urdf_file):
        with open(urdf_file, 'r') as f:
            robot_description_content = f.read()
    else:
        robot_description_content = Command(['xacro ', xacro_file])

    # 1. Robot State Publisher (publishes 3D transforms of all links)
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description_content
        }]
    )

    # 2. Joint State Publisher
    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher'
    )

    # 3. Fossen Marine Hydrodynamic Simulator Node
    fossen_sim_node = Node(
        package='hugr_sim',
        executable='fossen_sim_node',
        name='fossen_sim_node',
        output='screen',
        parameters=[params_path]
    )

    # 4. RViz2 Visualization
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_path],
        condition=IfCondition(use_rviz)
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            name='use_rviz',
            default_value='true',
            description='Whether to start RViz2 visualization'
        ),
        robot_state_publisher_node,
        joint_state_publisher_node,
        fossen_sim_node,
        rviz_node
    ])
