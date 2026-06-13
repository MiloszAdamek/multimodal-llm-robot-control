import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from nav_msgs.msg import Path
from std_msgs.msg import Bool
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
            Bool,
            '/llm_shutdown',
            self.shutdown_callback,
            10
        )

        # Camera
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
        self.actions = []
        self.times = []

        # Thread control
        self.running = True
        self.agent_thread = threading.Thread(target=self.agent_loop, daemon=True)
        self.agent_thread.start()

    def shutdown_callback(self, msg):
        if msg.data:
            self.get_logger().info("Shutdown signal received")

            self.running = False

    def depth_callback(self, msg):
        depth = self.bridge.imgmsg_to_cv2(
            msg,
            desired_encoding='passthrough'
        )

        self.latest_depth = depth

    def camera_callback(self, msg):
        frame = self.bridge.imgmsg_to_cv2(
            msg,
            desired_encoding='bgr8'
        )

        self.latest_frame = frame

    def encode_image(self, frame):
        _, buffer = cv2.imencode('.jpg', frame)

        return base64.b64encode(buffer).decode('utf-8')

    def send_action(self, action, value):
        request = DoRobotAction.Request()
        request.action = action
        request.value = float(value)

        future = self.client.call_async(request)

        while rclpy.ok() and not future.done():
            time.sleep(0.05)

        return future.result()

    def ask_llm(self):
        if self.latest_frame is None:
            self.get_logger().info("No camera frame yet")
            return

        image_base64 = self.encode_image(self.latest_frame)

        # Find a BLUE SQUARE BOX and give a location (left, right, center).
        # prompt = f"""
        #             Task: Find a BLACK METAL FRIDGE CABINET WITH SHELVES and give a location (left, right, center). If you do not see this object, return not visible.
        #             Do not think too much, just answer based on the current image. Follow your intuition, and do not try to be accurate.
        #             Output JSON in format: {{"position": "left/right/center/not visible"}}"""
        prompt = f"""
                    Task: Find the BLACK METAL CABINET WITH SHELVES in the image.
                    Rules:
                    visible = true if the object is clearly visible.
                    visible = false if the object is not visible.
                    x is the horizontal center position of the object from 0 to 100 (0=left, 50=center, 100=right).
                    y is the vertical center position of the object from 0 to 100 (0=top, 50=center, 100=bottom).
                    If you do not see the object, return visible = false and x = 0, y = 0.

                    Output ONLY valid JSON:
                    {{
                    "visible": true|false,
                    "x": value from 0 to 100,
                    "y": value from 0 to 100
                    }}"""

        s = time.perf_counter()
        response = requests.post(
            "http://192.168.224.1:11434/api/generate",
            json={
                "model": "qwen3.5:9b",
                "prompt": prompt,
                "images": [image_base64],
                "stream": False,
                "options": {
                    "presence_penalty": 1.5,
                    "temperature": 0.0,
                    "top_k": 20,
                    "top_p": 0.95
                },
            },
        )
        e = time.perf_counter()
        self.times.append(e-s)
        self.get_logger().info(response.json()["thinking"])

        text = response.json()["response"]
        
        match = re.search(r"\{.*?\}", text, re.DOTALL)
        if not match:
            raise ValueError("No JSON found")

        data = json.loads(match.group(0))
        self.get_logger().info(f"Data: {data}")

        self.actions.append(data)

        if not data["visible"]:
            self.send_action("left", 30)
        else:
            x = data["x"]
            y = data["y"]

            error = (x - 50) / 50.0

            if abs(error) < 0.35:
                x = int((x / 100.0) * 640)
                y = int((y / 100.0) * 480)
                x1 = max(0, x - 30)
                x2 = min(640, x + 30)
                y1 = max(0, y - 30)
                y2 = min(480, y + 30)

                roi = self.latest_depth[y1:y2, x1:x2]
                roi = roi[~np.isnan(roi)]
                roi = roi[roi > 0.01]
                min_dist = np.min(roi)

                action = "forward"
                if min_dist < 2:
                    value = 0.5
                else:
                    value = 1.5

            elif error > 0:
                action = "right"
                value = abs(error) * 30  

            else:
                action = "left"
                value = abs(error) * 30
            
            self.send_action(action, value)


    def agent_loop(self):
        while rclpy.ok() and self.running:
            try:
                self.ask_llm()
            except Exception as e:
                self.get_logger().error(f"LLM loop error: {e}")

            time.sleep(1)
        
        self.get_logger().info(f"Number of actions {len(self.actions)}  Average time of action: {np.mean(self.times)}")

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