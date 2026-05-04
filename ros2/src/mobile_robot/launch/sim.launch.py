from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node
from launch.substitutions import Command
import os

def generate_launch_description():

    pkg_path = os.path.join(
        os.getenv('HOME'),
        'dev/multimodal-llm-robot-control/ros2/src/mobile_robot'
    )

    urdf_file = os.path.join(pkg_path, 'urdf/robot.urdf')

    return LaunchDescription([

        ExecuteProcess(
            cmd=['gazebo', '--verbose', '-s', 'libgazebo_ros_factory.so'],
            output='screen'),

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{
                'robot_description': Command(['cat ', urdf_file])
            }],
            output='screen'
        ),

        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=[
                '-entity', 'robot',
                '-topic', 'robot_description',
                '-z', '0.05'
            ],
            output='screen'
        ),
    ])