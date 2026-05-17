import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from llm_controller_interfaces.srv import DoRobotAction

import math
import time

class MotionServer(Node):
    def __init__(self):
        super().__init__('motion_server')
        self.ang_speed = 0.3
        self.lin_speed = 0.1

        self.srv = self.create_service(DoRobotAction, 'do_robot_action', self.do_action_callback)
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)

        self.service = self.create_service(DoRobotAction, 'do_robot_action', self.do_action_callback)

    def stop_robot(self):
        msg = Twist()
        self.publisher.publish(msg)

    def do_action_callback(self, request, response):
        action = request.action
        value = request.value

        msg = Twist()

        if action == "left":
            duration = math.radians(value) / self.ang_speed
            msg.angular.z = self.ang_speed
            start = time.time()

            while time.time() - start < duration:
                self.publisher.publish(msg)
                time.sleep(0.05)

        elif action == "right":
            duration = math.radians(value) / self.ang_speed
            msg.angular.z = -self.ang_speed
            start = time.time()

            while time.time() - start < duration:
                self.publisher.publish(msg)
                time.sleep(0.05)

        elif action == "forward":
            distance_m = value/50.0
            duration = distance_m / self.lin_speed
            msg.linear.x = self.lin_speed
            start = time.time()

            while time.time() - start < duration:
                self.publisher.publish(msg)
                time.sleep(0.05)

        elif action == "stop":
            self.stop_robot()

        self.stop_robot()

        response.success = True

        return response


def main():
    rclpy.init()
    node = MotionServer()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()