import time

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor

# Message and Action Imports
from std_msgs.msg import String

DEFAULT_PIB_FACE_EXPRESSION_TOPIC = "/pib/expression"
DEFAULT_PIB_FACE_TEXT_TOPIC = "/pib/display_text"

class EduPipInterface():
  def __init__(self, node : Node):
    self.node = node

    self.pub_face_expression = node.create_publisher(String, DEFAULT_PIB_FACE_EXPRESSION_TOPIC, 10)
    self.pub_face_text = node.create_publisher(String, DEFAULT_PIB_FACE_TEXT_TOPIC, 10)

  def set_face_expression(self, expression : str):
    msg = String()
    msg.data = expression
    self.pub_face_expression.publish(msg)
    self.node.get_logger().info(f"Set face expression to: {expression}")

  def set_face_text(self, text : str):
    msg = String()
    msg.data = text
    self.pub_face_text.publish(msg)
    self.node.get_logger().info(f"Set face text to: {text}")