from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'device_mode',
            default_value='auto',
            description='Device mode: "auto", "serial", or "udp"'
        ),
        DeclareLaunchArgument(
            'serial_port',
            default_value='/dev/ttyUSB0',
            description='Serial port path (e.g. /dev/ttyUSB0 or COM7)'
        ),
        DeclareLaunchArgument(
            'baudrate',
            default_value='921600',
            description='Baudrate for serial connection'
        ),
        DeclareLaunchArgument(
            'udp_port',
            default_value='9876',
            description='UDP port for network bridge mode'
        ),
        Node(
            package='xsens_mti_driver',
            executable='xsens_node',
            name='xsens_mti_node',
            output='screen',
            parameters=[{
                'device_mode': LaunchConfiguration('device_mode'),
                'serial_port': LaunchConfiguration('serial_port'),
                'baudrate': LaunchConfiguration('baudrate'),
                'udp_port': LaunchConfiguration('udp_port'),
                'imu_frame_id': 'imu_link',
                'gnss_frame_id': 'gnss_link',
            }]
        )
    ])
