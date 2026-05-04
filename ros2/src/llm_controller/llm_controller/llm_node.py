import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import requests
import json

class LLMController(Node):

    def __init__(self):
        super().__init__('llm_controller')

        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)

        self.timer = self.create_timer(5.0, self.ask_llm)

    def ask_llm(self):

        prompt = """
        You control a mobile robot.
        Respond ONLY with JSON:
        {"linear": float, "angular": float}

        Example:
        {"linear": 0.5, "angular": 0.0}
        """

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False
            }
        )

        text = response.json()["response"]

        try:
            data = json.loads(text.strip())
            msg = Twist()
            msg.linear.x = float(data["linear"])
            msg.angular.z = float(data["angular"])
            self.publisher.publish(msg)
            self.get_logger().info(f"LLM cmd: {data}")
        except:
            self.get_logger().warn("LLM response invalid")

def main(args=None):
    rclpy.init(args=args)
    node = LLMController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()