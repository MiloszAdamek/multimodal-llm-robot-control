import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from llm_controller_interfaces.srv import DoRobotAction

# import torch
# from PIL import Image
# from transformers import AutoTokenizer, AutoModel

import requests
import json
import math
import re
import threading
import time
import cv2
import numpy as np
import base64


class LLMController(Node):

    def __init__(self):
        super().__init__('llm_controller')

        self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

        # Depth Camera
        self.bridge = CvBridge()
        
        self.latest_frame = None
        self.create_subscription(
            Image,
            '/depth_camera_sensor/image_raw',
            self.camera_callback,
            10
        )

        self.latest_depth = None
        self.create_subscription(
            Image,
            '/depth_camera_sensor/depth/image_raw',
            self.depth_callback,
            10
        )

        # Service client
        self.client = self.create_client(
            DoRobotAction,
            'do_robot_action'
        )

        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for service...")

        # Current state
        self.last_actions = ["None","None"]
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0

        # Publisher for path visualization
        self.path_publisher = self.create_publisher(Path, '/robot_path', 10)
        self.path_msg = Path()
        self.path_msg.header.frame_id = "odom"

        # Thread control
        self.running = True
        self.agent_thread = threading.Thread(target=self.agent_loop, daemon=True)
        self.agent_thread.start()

    def camera_callback(self, msg):
        frame = self.bridge.imgmsg_to_cv2(
            msg,
            desired_encoding='bgr8'
        )

        self.latest_frame = frame
    
    def depth_callback(self, msg):
        depth = self.bridge.imgmsg_to_cv2(
            msg,
            desired_encoding='passthrough'
        )

        self.latest_depth = depth

    def encode_image(self, frame):
        _, buffer = cv2.imencode('.jpg', frame)

        return base64.b64encode(buffer).decode('utf-8')

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

    def send_action(self, action, value):
        request = DoRobotAction.Request()
        request.action = action
        request.value = float(value)

        future = self.client.call_async(request)

        while rclpy.ok() and not future.done():
            time.sleep(0.05)

        return future.result()

    def ask_llm(self):
        if self.latest_frame is None or self.latest_depth is None:
            self.get_logger().info("No camera frame or depth data yet")
            return

        image_base64 = self.encode_image(self.latest_frame)

        prompt = f"""You are a perception module for a mobile robot.
                    Your goal: Find a box, drive towards it and stop when close.
                    Rules:
                    - If object is close → action = "stop"
                    - If object is not visible → action = "search"
                    - If object is left → action = "left"
                    - If object is right → action = "right"
                    - If object is centered → action = "forward"
                    Respond ONLY with valid JSON:
                    {{"action": "search" | "left" | "right" | "forward" | "stop"}}
                    Image size: {self.latest_frame.shape}"""

        response = requests.post(
            "http://192.168.224.1:11434/api/generate",
            json={
                "model": "qwen3.5:4b",
                "prompt": prompt,
                "images": [image_base64],
                "stream": False,
            },
        )
        self.get_logger().info(response.json()["thinking"])

        text = response.json()["response"]
        
        match = re.search(r"\{.*?\}", text, re.DOTALL)
        if not match:
            raise ValueError("No JSON found")

        data = json.loads(match.group(0))

        action = data["action"].lower()
        self.last_actions.append(action)
        if len(self.last_actions) > 2:
            self.last_actions.pop(0)

        self.get_logger().info(f"LLM action: {action}")

        if action in ["search", "left", "right", "forward", "stop"]:
            if action == "search":
                action = "left"
                value = 25
            elif action == "left":
                value = 10
            elif action == "right":
                value = 10
            elif action == "forward":
                value = 20
            else:
                value = 0
            self.send_action(action, value)
            
            if action == "stop":
                self.running = False
                self.get_logger().info(f"Stopping LLM")

    def agent_loop(self):
        while rclpy.ok() and self.running:
            try:
                self.ask_llm()
            except Exception as e:
                self.get_logger().error(f"LLM loop error: {e}")

            time.sleep(1)

    def destroy_node(self):
        self.running = False
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = LLMController()

    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()