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

        self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0

        self.service = self.create_service(DoRobotAction, 'do_robot_action', self.do_action_callback)

    def quaternion_to_yaw(self, q):
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        return math.atan2(siny_cosp, cosy_cosp)

    def odom_callback(self, msg):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y
        self.current_yaw = self.quaternion_to_yaw(
            msg.pose.pose.orientation
        )

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
            distance_m = value/20.0
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