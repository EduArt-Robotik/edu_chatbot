import time
import asyncio
import numpy as np
from os import path
from pathlib import Path

from openwakeword.model import Model

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data, QoSProfile, ReliabilityPolicy, HistoryPolicy

from audio_common_msgs.msg import AudioStamped


NODE_NAME = 'edu_chatbot_wakeword_node'

DEFAULT_DEBOUNCE_TIME                = 1.0
DEFAULT_SCORE_THRESHOLD              = 0.05
DEFAULT_INPUT_TOPIC                  = '/audio/in'
DEFAULT_OUTPUT_TOPIC                 = '/wakeword/output'
DEFAULT_MODEL_NAME                   = 'hey_rick.onnx'


def get_logger():
  return rclpy.logging.get_logger(NODE_NAME)


class EduWakewordDetector(Node):
  def __init__(self):
    super().__init__(NODE_NAME)

    # Members
    self.last_detection_time = 0

    # Parameters Configuration
    self.declare_parameter('input_topic', DEFAULT_INPUT_TOPIC)
    self.input_topic = self.get_parameter('input_topic').get_parameter_value().string_value

    self.declare_parameter('score_threshold', DEFAULT_SCORE_THRESHOLD)
    self.score_threshold = self.get_parameter('score_threshold').get_parameter_value().double_value

    self.declare_parameter('model_name', DEFAULT_MODEL_NAME)
    self.model_name = self.get_parameter('model_name').get_parameter_value().string_value

    self.declare_parameter('debounce_time', DEFAULT_DEBOUNCE_TIME)
    self.debounce_time = self.get_parameter('debounce_time').get_parameter_value().double_value
    
    get_logger().info(
      f'Loaded parameters:\n'
      f'  debounce_time: {self.debounce_time}\n'
      f'  score_threshold: {self.score_threshold}\n'
      f'  model_name: {self.model_name}\n'
      f'  input_topic: {self.input_topic}' 
    )

    get_logger().info('Loading wakeword model.')
    self.model = Model(wakeword_model_paths=[path.join(path.dirname(__file__), "..", "models", self.model_name)])
    model_count = len(self.model.models.keys())
    print(f"Loaded {model_count} wakeword models.")
    
    #qos_profile = QoSProfile(
    #  reliability=ReliabilityPolicy.RELIABLE,
    #  history=HistoryPolicy.KEEP_LAST,
    #  depth=10
    #)

    self.subscription = self.create_subscription(
      AudioStamped,
      self.input_topic,
      self.audio_callback,
      qos_profile_sensor_data #qos_profile
    )

    get_logger().info(f'{NODE_NAME} initialized successfully.')

  def audio_callback(self, msg):
    self.get_logger().info('Got first audio msg. Inference running.', once=True)

    # Manually convert each chunk, but this should be reasonably quick
    audio = np.asarray(msg.audio.audio_data.float32_data, dtype=np.float32)
    audio_int16 = np.clip(audio, -1.0, 1.0)
    audio_int16 = (audio_int16 * 32767).astype(np.int16)

    prediction = self.model.predict(audio_int16)

    for model in self.model.prediction_buffer.keys():
      scores = list(
        self.model.prediction_buffer[model]
      )

      if not scores:
        continue

      score = scores[-1]

      if score >= self.score_threshold:
        current_time = time.time()
        if current_time - self.last_detection_time >= self.debounce_time:
          get_logger().info(f"Wakeword detected by model '{model}' with score {score:.3f}")
          self.last_detection_time = current_time


def main():
  rclpy.init()
  node = EduWakewordDetector()

  try:
    rclpy.spin(node)
  except KeyboardInterrupt:
    pass
  finally:
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
  main()