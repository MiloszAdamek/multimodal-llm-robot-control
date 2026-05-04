import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import requests
import json
import math

class LLMController(Node):

    def __init__(self):
        super().__init__('llm_controller')

        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)

        self.timer = self.create_timer(5.0, self.ask_llm)

        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0

        self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

        self.goal_x = 2.0
        self.goal_y = 0.0

        self.history = ""

    def quaternion_to_yaw(self, q):
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        return math.atan2(siny_cosp, cosy_cosp)

    def odom_callback(self, msg):
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y

        orientation_q = msg.pose.pose.orientation
        quaternion = (
            orientation_q.x,
            orientation_q.y,
            orientation_q.z,
            orientation_q.w
        )
        self.current_yaw = self.quaternion_to_yaw(orientation_q)

    def ask_llm(self):

        # prompt = """
        # You control a mobile robot.
        # Respond ONLY with JSON without any text and explanation:
        # {"linear": float, "angular": float}

        # Example:
        # {"linear": 0.5, "angular": 0.0}

        # In every prommpt, I will give you the current state of the robot and the target position.
        # """

        dx = self.goal_x - self.current_x
        dy = self.goal_y - self.current_y

        distance = math.sqrt(dx*dx + dy*dy)
        desired_heading = math.atan2(dy, dx)

        angle_error = desired_heading - self.current_yaw

        # normalizacja do [-pi, pi]
        angle_error = math.atan2(math.sin(angle_error), math.cos(angle_error))

        self.history += f"\nPrevious position: {self.current_x}, {self.current_y}"

        prompt = f"""
        You control a 2 wheeled mobile robot.

        Distance to goal: {distance:.2f} meters
        Heading error: {angle_error:.2f} radians

        If heading error is large, rotate.
        If heading error is small, move forward.

        Respond ONLY with JSON without any text and explanation:
        {{"linear": float, "angular": float}}
        """

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": prompt + self.history,
                "stream": False
            }
        )

        text = response.json()["response"]
        self.get_logger().info(f"Current position: {self.current_x:.2f}, {self.current_y:.2f}")
        try:
            data = json.loads(text.strip())
            msg = Twist()
            msg.linear.x = float(data["linear"])
            msg.angular.z = float(data["angular"])
            self.publisher.publish(msg)
            self.get_logger().info(f"LLM cmd: {data}")
            self.get_logger().info(f"LLM response: {text}")
        except:
            self.get_logger().warn(f"LLM response invalid: {text}")
            self.get_logger().warn("LLM response invalid")

def main(args=None):
    rclpy.init(args=args)
    node = LLMController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()