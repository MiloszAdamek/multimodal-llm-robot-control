from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

    llm_node = Node(
        package='llm_controller',
        executable='llm_node',
        name='llm_node',
        output='screen'
    )

    robot_action_server = Node(
        package='llm_controller',
        executable='robot_action_server',
        name='robot_action_server',
        output='screen'
    )

    return LaunchDescription([
        llm_node,
        robot_action_server
    ])