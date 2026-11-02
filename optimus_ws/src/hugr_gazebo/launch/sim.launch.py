import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node

def generate_launch_description():
    # 1. Package directories
    pkg_hugr_gazebo = get_package_share_directory('hugr_gazebo')
    pkg_hugr_description = get_package_share_directory('hugr_description')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    # 2. Config paths
    bridge_config_path = os.path.join(pkg_hugr_gazebo, 'config', 'bridge.yaml')

    # 3. Environment paths (Gazebo will look directly in these folders)
    models_dir = os.path.join(pkg_hugr_gazebo, 'models')
    worlds_dir = os.path.join(pkg_hugr_gazebo, 'worlds')
    description_parent = os.path.dirname(pkg_hugr_description)

    gz_resource_paths = f"{worlds_dir}:{models_dir}:{description_parent}:{pkg_hugr_description}"

    set_gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=gz_resource_paths
    )

    headless_arg = DeclareLaunchArgument(
        'headless',
        default_value='false',
        description='Run Gazebo in server-only headless mode without GUI'
    )

    headless = LaunchConfiguration('headless')
    gz_args = PythonExpression([
        "'-s -r circuit_world.sdf' if '", headless, "'.lower() in ['true', '1'] else '-r circuit_world.sdf'"
    ])

    # 4. Launch Gazebo Sim - Passing only the world filename without space-containing paths
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': gz_args}.items()
    )

    # 5. Launch the ROS-GZ Parameter Bridge
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{'config_file': bridge_config_path}],
        output='screen'
    )

    # 6. Launch Gazebo Thruster Bridge (/motor_pwms and /cmd_vel -> Gazebo thrusters)
    thruster_bridge = Node(
        package='hugr_gazebo',
        executable='thruster_bridge.py',
        output='screen'
    )

    return LaunchDescription([
        headless_arg,
        set_gz_resource_path,
        gz_sim,
        bridge,
        thruster_bridge
    ])
