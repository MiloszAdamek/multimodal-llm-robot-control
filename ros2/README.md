Każdy terminal to osobne środowisko.

Wymagane:
source install/setup.bash

ros2 pkg list | grep llm
ros2 pkg list | grep llm


Terminal 1:
ros2 run llm_controller llm_node

Terminal 2:
ros2 run llm_controller llm_node

Terminal 3 (opcjonalnie):
ros2 topic echo /cmd_vel


w /ros2:

killall -9 gazebo gzserver gzclient
colcon build 
source install/setup.bash
ros2 launch mobile_robot robot.launch.py