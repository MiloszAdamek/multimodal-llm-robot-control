import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from std_msgs.msg import Bool
from llm_controller_interfaces.srv import DoRobotAction

import math
import time
import numpy as np

class MotionServer(Node):
    def __init__(self):
        super().__init__('motion_server')
        self.ang_speed = 0.3
        self.lin_speed = 0.1

        self.srv = self.create_service(DoRobotAction, 'do_robot_action', self.do_action_callback)
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)

        self.shutdown_pub = self.create_publisher(
            Bool,
            '/llm_shutdown',
            10
        )

        # Depth Camera
        self.bridge = CvBridge()

        self.latest_depth = None
        self.create_subscription(
            Image,
            '/depth_camera_sensor/depth/image_raw',
            self.depth_callback,
            10
        )

    def depth_callback(self, msg):
        depth = self.bridge.imgmsg_to_cv2(
            msg,
            desired_encoding='passthrough'
        )

        self.latest_depth = depth

    def is_obstacle_close(self, threshold=0.5):
        if self.latest_depth is None:
            return False

        depth = self.latest_depth

        h, w = depth.shape

        roi = depth[h//2 - 20:h//2 + 20, w//2 - 20:w//2 + 20]

        roi = roi[~np.isnan(roi)]
        roi = roi[roi > 0.01]

        if len(roi) == 0:
            return False

        min_dist = np.min(roi)
        self.get_logger().info(f"{min_dist:.2f} m")

        return min_dist < threshold

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
            distance_m = value
            duration = distance_m / self.lin_speed
            msg.linear.x = self.lin_speed

            if self.is_obstacle_close(1.0):
                    msg_shutdown = Bool()
                    msg_shutdown.data = True
                    self.shutdown_pub.publish(msg_shutdown)

                    msg.linear.x = 0.0
                    msg.angular.z = 0.0
                    self.publisher.publish(msg)
            else:
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