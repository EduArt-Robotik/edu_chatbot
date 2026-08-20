import time
from enum import Enum, auto
from threading import Thread

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor
from std_srvs.srv import SetBool

# Message and Action Imports
from edu_chatbot_msgs.action import Query
# from whisper_msgs.action import STT
# from audio_common_msgs.action import TTS

NODE_NAME = 'edu_chatbot_pipeline_manager_node'

DEFAULT_WAKEUP_KEYWORD   = 'Hey Eddie'
DEFAULT_LOG_TO_FILE      = False
DEFAULT_START_ENABLED    = True
DEFAULT_STT_ACTION_TOPIC = '/audio/in'
DEFAULT_RAG_ACTION_TOPIC = '/rag/query'
DEFAULT_TTS_ACTION_TOPIC = '/audio/out'

# Timeout limits in seconds, None means no timeout (wait indefinitely)
TIMEOUT_STT_SEC = None
TIMEOUT_RAG_SEC = 10.0
TIMEOUT_TTS_SEC = 15.0


class ChatbotState(Enum):
  OFF       = auto()
  LISTENING = auto()
  THINKING  = auto()
  SPEAKING  = auto()
  ERROR     = auto()


class EduChatbotPipelineManagerNode(Node):
  def __init__(self):
    super().__init__(NODE_NAME)

    # Parameters Configuration
    self.declare_parameter('wakeup_keyword', DEFAULT_WAKEUP_KEYWORD)
    self.wakeup_keyword = self.get_parameter('wakeup_keyword').get_parameter_value().string_value

    self.declare_parameter('log_to_file', DEFAULT_LOG_TO_FILE)
    self.log_to_file = self.get_parameter('log_to_file').get_parameter_value().bool_value

    self.declare_parameter('start_enabled', DEFAULT_START_ENABLED)
    self.pipeline_enabled = self.get_parameter('start_enabled').get_parameter_value().bool_value

    self.declare_parameter('stt_action_topic', DEFAULT_STT_ACTION_TOPIC)
    self.declare_parameter('rag_action_topic', DEFAULT_RAG_ACTION_TOPIC)
    self.declare_parameter('tts_action_topic', DEFAULT_TTS_ACTION_TOPIC)

    # Internal pipeline buffers passed between states
    self._current_user_text = ""
    self._current_rag_response = ""

    # State Machine Variable
    self.state = ChatbotState.LISTENING if self.pipeline_enabled else ChatbotState.OFF

    # Action Clients
    # self.stt_action_client = ActionClient(self, STT, stt_action_topic)
    self.rag_action_client = ActionClient(self, Query, DEFAULT_RAG_ACTION_TOPIC)
    # self.tts_action_client = ActionClient(self, TTS, tts_action_topic)

    # Services and Execution Thread
    self.enable_srv = self.create_service(SetBool, "enable_pipeline", self.enable_callback)
    Thread(target=self.run_pipeline_loop, daemon=True).start()

    self.get_logger().info(f'{NODE_NAME} initialized successfully.')

  def enable_callback(self, request, response):
    if request.data:
      self.get_logger().info("Pipeline service call: Enabling system.")
      self.pipeline_enabled = True
      if self.state == ChatbotState.OFF:
        self.state = ChatbotState.LISTENING
    else:
      self.get_logger().info("Pipeline service call: Disabling system.")
      self.pipeline_enabled = False
      self.state = ChatbotState.OFF
    
    response.success = True
    return response

  # ---------------------------------------------------------------------------
  # Action Helpers
  # ---------------------------------------------------------------------------
  def _wait_for_future(self, future, timeout_sec=None):
    """Poll a future without blocking executor threads."""
    start_time = time.time()
    while rclpy.ok() and not future.done():
      if timeout_sec and (time.time() - start_time) > timeout_sec:
        return None
      time.sleep(0.01)
    
    return future.result() if future.done() else None

  def _send_action_goal_sync(self, client, goal_msg, timeout_sec=None):
    """Send an action goal and wait for result (timeout protected)."""
    goal_future = client.send_goal_async(goal_msg)
    goal_handle = self._wait_for_future(goal_future, timeout_sec=timeout_sec)

    if goal_handle is None:
      raise TimeoutError("Timed out while waiting for server to accept action goal.")
    if not goal_handle.accepted:
      raise RuntimeError("Action goal was rejected by the server.")

    result_future = goal_handle.get_result_async()
    result_wrapped = self._wait_for_future(result_future, timeout_sec=timeout_sec)
    
    if result_wrapped is None:
      raise TimeoutError("Timed out waiting for action execution to complete.")
      
    return result_wrapped.result

  # ---------------------------------------------------------------------------
  # State Handlers
  # ---------------------------------------------------------------------------
  def _state_listening(self):
    """Blocks indefinitely until speech keyword is spoken, then shifts to THINKING."""
    self.get_logger().info("[State: LISTENING] Waiting for keyword activation...")

    # Listen state has infinite timeout (timeout_sec=None)
    # TODO: Maybe execute some idle poses while waiting for user input
    # stt_goal = STT.Goal()
    # stt_res = self._send_action_goal_sync(self.stt_action_client, stt_goal, timeout_sec=TIMEOUT_STT_SEC)
    # self._current_user_text = stt_res.text

    # Placeholder for testing
    time.sleep(5.0)
    self._current_user_text = "What can you tell me?"
    self.get_logger().info(f"User Input: '{self._current_user_text}'")

    self.state = ChatbotState.THINKING

  def _state_thinking(self):
    self.get_logger().info("[State: THINKING] Querying RAG backend...")

    rag_msg = Query.Goal()
    rag_msg.query = self._current_user_text
    rag_res = self._send_action_goal_sync(self.rag_action_client,rag_msg,timeout_sec=TIMEOUT_RAG_SEC)

    self._current_rag_response = rag_res.response
    self.get_logger().info(f"RAG Response: '{self._current_rag_response}'")

    self.state = ChatbotState.SPEAKING

  def _state_speaking(self):
    self.get_logger().info("[State: SPEAKING] Outputting response...")

    # tts_goal = TTS.Goal(text=self._current_rag_response)
    # self._send_action_goal_sync(self.tts_action_client, tts_goal, timeout_sec=TIMEOUT_TTS_SEC)

    self.state = ChatbotState.LISTENING

  def _state_error(self, error_message: str):
    self.get_logger().error(f"[State: ERROR] Pipeline failure: {error_message}")
    # TODO: Maybe inform user that an error occurred (or maybe not, if there are too many errors)
    self.state = ChatbotState.LISTENING if self.pipeline_enabled else ChatbotState.OFF

  # ---------------------------------------------------------------------------
  # State Machine Execution Loop
  # ---------------------------------------------------------------------------
  def run_pipeline_loop(self):
    self.get_logger().info("Waiting for external Action Servers to become ready...")
    # self.stt_action_client.wait_for_server()
    self.rag_action_client.wait_for_server()
    # self.tts_action_client.wait_for_server()
    self.get_logger().info("Connected to Action Servers. Pipeline active.")

    while rclpy.ok():
      if not self.pipeline_enabled:
        self.state = ChatbotState.OFF
        time.sleep(0.1)
        continue

      try:
        if self.state == ChatbotState.LISTENING:
          self._state_listening()
        elif self.state == ChatbotState.THINKING:
          self._state_thinking()
        elif self.state == ChatbotState.SPEAKING:
          self._state_speaking()

      except Exception as exc:
        self.state = ChatbotState.ERROR
        self._state_error(str(exc))

def main():
  rclpy.init()
  edu_chatbot_node = EduChatbotPipelineManagerNode()

  executor = MultiThreadedExecutor()
  executor.add_node(edu_chatbot_node)

  try:
    executor.spin()
  except KeyboardInterrupt:
    pass
  finally:
    edu_chatbot_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
  main()