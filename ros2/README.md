Każdy terminal to osobne środowisko.

Wymagane:
cd ros2
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 pkg list | grep llm

Terminal 1:
ros2 launch mobile_robot sim.launch.py

Terminal 2:
ros2 launch llm_controller llm_system.launch.py

<!-- Terminal 2:
ros2 run llm_controller robot_action_server

Terminal 3:
ros2 run llm_controller llm_node -->

Terminal 4 (podgląd kamery, opcjonalne):
ros2 run rqt_image_view rqt_image_view

w /ros2:

killall -9 gazebo gzserver gzclient
colcon build 
source install/setup.bash
ros2 launch mobile_robot robot.launch.py

colcon build