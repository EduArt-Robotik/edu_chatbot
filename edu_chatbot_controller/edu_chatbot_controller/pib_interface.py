import time
import random
from enum import Enum

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor

# Message and Action Imports
from std_msgs.msg import String
from datatypes.action import MoveToPose


class PoseCategory(Enum):
    NEUTRAL = "neutral"
    THINKING = "thinking"
    SPEAKING = "speaking"

ROBOT_POSE_KEYS = {
  PoseCategory.NEUTRAL: "Chatbot/Neutral",
  PoseCategory.THINKING: "Chatbot/Thinking",
  PoseCategory.SPEAKING: "Chatbot/Speaking",
}

POSE_COUNT_NEUTRAL   = 5
POSE_COUNT_THINKING  = 3
POSE_COUNT_SPEAKING  = 7

DEFAULT_PIB_FACE_EXPRESSION_TOPIC = "/pib/expression"
DEFAULT_PIB_FACE_TEXT_TOPIC       = "/pib/display_text"
DEFAULT_PIB_POSE_TOPIC            = '/move_to_pose'


def random_pose(category: PoseCategory) -> str:
  if category == PoseCategory.NEUTRAL:
    return f"{ROBOT_POSE_KEYS[PoseCategory.NEUTRAL]}{random.randint(1, POSE_COUNT_NEUTRAL)}"
  elif category == PoseCategory.THINKING:
    return f"{ROBOT_POSE_KEYS[PoseCategory.THINKING]}{random.randint(1, POSE_COUNT_THINKING)}"
  elif category == PoseCategory.SPEAKING:
    return f"{ROBOT_POSE_KEYS[PoseCategory.SPEAKING]}{random.randint(1, POSE_COUNT_SPEAKING)}"
  else:
    raise ValueError(f"Unknown pose category: {category}")


class EduPipInterface():
  def __init__(self, node : Node):
    self.node = node

    self.pub_face_expression = node.create_publisher(String, DEFAULT_PIB_FACE_EXPRESSION_TOPIC, 10)
    self.pub_face_text = node.create_publisher(String, DEFAULT_PIB_FACE_TEXT_TOPIC, 10)
    self.pose_client = ActionClient(self.node, MoveToPose, DEFAULT_PIB_POSE_TOPIC)

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

  def move_to_pose(self, pose_name : str) -> rclpy.task.Future | None:
    # Wait until the action server is available
    if not self.pose_client.wait_for_server(timeout_sec=5.0):
      self.node.get_logger().error("MoveToPose action server not available.")
      return

    # Create a goal message
    goal_msg = MoveToPose.Goal()
    goal_msg.pose_name = pose_name

    # Send the goal to the action server
    try:
      self.node.get_logger().info(f"Sending goal to move to pose: {pose_name}")
      future = self.pose_client.send_goal_async(goal_msg)
    except Exception as e:
      self.node.get_logger().error(f"Failed to send goal: {e}")
      return

    return future

  def move_to_random_pose(self, category: PoseCategory = PoseCategory.NEUTRAL) -> rclpy.task.Future | None:
    try:
      pose_name = random_pose(category)
      return self.move_to_pose(pose_name)
    except ValueError as e:
      self.node.get_logger().error(f"Failed to move to random pose: {e}")
      return