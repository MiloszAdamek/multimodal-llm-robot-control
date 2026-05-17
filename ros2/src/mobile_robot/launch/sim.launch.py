from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch_ros.parameter_descriptions import ParameterValue
from launch.substitutions import Command

import os


def generate_launch_description():

    # --- ścieżka do pakietu ---
    pkg_share = get_package_share_directory('mobile_robot')

    urdf_file = os.path.join(pkg_share, 'urdf', 'robot.urdf')

    # --- Gazebo (ROS2-safe) ---
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('gazebo_ros'),
                'launch',
                'gazebo.launch.py'
            )
        )
    )

    # --- robot state publisher ---
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': ParameterValue(
                Command(['cat ', urdf_file]),
                value_type=str
            )
        }]
    )

    # --- spawn entity ---
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        output='screen',
        arguments=[
            '-entity', 'robot',
            '-topic', 'robot_description',
            '-z', '0.05'
        ]
    )

    blue_box_model = os.path.join(pkg_share, 'urdf', 'blue_box', 'model.sdf')
    spawn_blue_box = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        output='screen',
        arguments=[
            '-file', blue_box_model,
            '-entity', 'blue_box',
            '-x', '1.0',
            '-y', '4.0',
            '-z', '0.05'
        ]
    )

    delayed_spawn = TimerAction(
        period=5.0,
        actions=[spawn_entity, spawn_blue_box]
    )

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        delayed_spawn
    ])