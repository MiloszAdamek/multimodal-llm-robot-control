import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped
import requests
import json
import math
import re
import threading


class LLMController(Node):

    def __init__(self):
        super().__init__('llm_controller')

        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)

        # LLM timer (5 sec)
        self.timer = self.create_timer(5.0, self.ask_llm)

        self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

        # Current state
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0

        # Goal
        self.goal_x = -5.0
        self.goal_y = 4.0

        # P controller
        self.k_linear = 0.8
        self.k_angular = 2.0

        # Limits
        self.max_linear = 0.6
        self.max_angular = 1.5
        self.goal_tolerance = 0.2

        self.current_action = "stop"
        self.llm_busy = False
        self.goal_reached = False

        # Publisher for path visualization
        self.path_publisher = self.create_publisher(Path, '/robot_path', 10)

        self.path_msg = Path()
        self.path_msg.header.frame_id = "odom"

    def clamp(self, value, min_val, max_val):
        return max(min(value, max_val), min_val)

    def quaternion_to_yaw(self, q):
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        return math.atan2(siny_cosp, cosy_cosp)

    def odom_callback(self, msg):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y
        self.current_yaw = self.quaternion_to_yaw(msg.pose.pose.orientation)

        # Update path for visualization
        pose = PoseStamped()
        pose.header.frame_id = "odom"
        pose.header.stamp = self.get_clock().now().to_msg()

        pose.pose.position.x = self.current_x
        pose.pose.position.y = self.current_y
        pose.pose.position.z = 0.0
        pose.pose.orientation = msg.pose.pose.orientation

        self.path_msg.header.stamp = pose.header.stamp
        self.path_msg.poses.append(pose)

        # Max path length
        if len(self.path_msg.poses) > 2000:
            self.path_msg.poses.pop(0)

        self.path_publisher.publish(self.path_msg)

    def shutdown_node(self):
        self.get_logger().info("Shutting down node...")
        self.destroy_node()
        rclpy.shutdown()

    def ask_llm(self):
        if self.llm_busy:
            return

        thread = threading.Thread(target=self._ask_llm_thread)
        thread.start()

    def _ask_llm_thread(self):
        self.llm_busy = True

        dx = self.goal_x - self.current_x
        dy = self.goal_y - self.current_y

        distance = math.sqrt(dx * dx + dy * dy)
        desired_heading = math.atan2(dy, dx)
        angle_error = desired_heading - self.current_yaw
        angle_error = math.atan2(math.sin(angle_error), math.cos(angle_error))

        self.get_logger().info(
            f"Pos: {self.current_x:.2f}, {self.current_y:.2f} | "
            f"Dist: {distance:.2f} | Angle err: {angle_error:.2f}"
        )

        # Stop condition
        if distance < self.goal_tolerance:
            self.get_logger().info("Goal reached.")
            self.goal_reached = True
            return

        prompt = f"""
                    You control a mobile robot.

                    Based on the state decide only one action:

                    - "rotate"  → if heading error is large
                    - "forward" → if heading error is small
                    - "stop"    → if distance is very small less than 0.1

                    Distance to goal: {distance:.3f}
                    Heading error: {angle_error:.3f}

                    Respond ONLY with JSON:
                    {{"action": "rotate" or "forward" or "stop"}}
                """

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "gemma3:4b",
                    "prompt": prompt,
                    "stream": False
                },
                # timeout=15.0
            )

            text = response.json()["response"]
            # self.get_logger().info(f"LLM answer: {text}")

            match = re.search(r"\{.*?\}", text, re.DOTALL)
            if not match:
                raise ValueError("No JSON found")

            data = json.loads(match.group(0))

            action = data["action"].lower()

            if action not in ["rotate", "forward", "stop"]:
                raise ValueError("Invalid action")

            self.current_action = action
            self.get_logger().info(f"LLM action: {action}")

            # Stop if goal is reached (doesn't work well)
            if self.current_action == "stop":
                self.get_logger().info("Goal reached or very close. Stopping.")
                self.llm_busy = False

        except Exception as e:
            self.get_logger().warn(f"LLM error: {e}")

        self.llm_busy = False

    # P control loop 20 Hz
    def control_loop(self):

        if self.goal_reached:
            msg = Twist()
            self.publisher.publish(msg)
            self.get_logger().info("Shutting down...")
            self.shutdown_node()
            return

        dx = self.goal_x - self.current_x
        dy = self.goal_y - self.current_y

        distance = math.sqrt(dx * dx + dy * dy)
        desired_heading = math.atan2(dy, dx)
        angle_error = desired_heading - self.current_yaw
        angle_error = math.atan2(math.sin(angle_error), math.cos(angle_error))

        msg = Twist()

        if self.current_action == "rotate":
            msg.linear.x = 0.0
            msg.angular.z = self.k_angular * angle_error

        elif self.current_action == "forward":
            msg.linear.x = self.k_linear * distance
            msg.angular.z = 0.5 * angle_error

        elif self.current_action == "stop":
            msg.linear.x = 0.0
            msg.angular.z = 0.0

        # Limits
        msg.linear.x = self.clamp(msg.linear.x, -self.max_linear, self.max_linear)
        msg.angular.z = self.clamp(msg.angular.z, -self.max_angular, self.max_angular)

        self.publisher.publish(msg)



def main(args=None):
    rclpy.init(args=args)
    node = LLMController()

    node.create_timer(0.05, node.control_loop) # 20 Hz P control loop

    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()