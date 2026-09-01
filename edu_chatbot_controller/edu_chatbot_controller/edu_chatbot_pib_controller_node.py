import time
from enum import Enum, auto
from threading import Thread
from rapidfuzz import process, fuzz

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor

# Message and Action Imports
from std_srvs.srv import SetBool
from whisper_msgs.action import STT
from edu_chatbot_msgs.action import Query
from audio_common_msgs.action import TTS

from .pib_interface import EduPipInterface, PoseCategory

NODE_NAME = 'edu_chatbot_pipeline_manager_node'

DEFAULT_WAKEUP_KEYWORDS              = ['Hello Pib', 'Hello Robot', 'Hey Pib', 'Hey Robot', 'Good morning Pib', 'Good morning Robot', 'Good afternoon Pib', 'Good afternoon Robot', 'Good evening Pib', 'Good evening Robot']
DEFAULT_KEYWORD_SIMILARITY_THRESHOLD = 75
DEFAULT_LOG_TO_FILE                  = False
DEFAULT_START_ENABLED                = True
DEFAULT_STT_TOPIC                    = '/whisper/listen'
DEFAULT_RAG_TOPIC                    = '/rag/query'
DEFAULT_TTS_TOPIC                    = '/piper/say'

# Timeout limits in seconds, None means no timeout (wait indefinitely)
TIMEOUT_STT_SEC = None
TIMEOUT_RAG_SEC = 30.0
TIMEOUT_TTS_SEC = 120.0

# Face expressions
FACE_EXPRESSION_LISTENING = "rick_neutral"
FACE_EXPRESSION_THINKING  = "rick_thinking_hard"
FACE_EXPRESSION_SPEAKING  = "rick_answering"

def get_logger():
  return rclpy.logging.get_logger(NODE_NAME)

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
    self.declare_parameter('wakeup_keywords', DEFAULT_WAKEUP_KEYWORDS)
    self.wakeup_keywords = self.get_parameter('wakeup_keywords').get_parameter_value().string_array_value

    self.declare_parameter('keyword_similarity_threshold', DEFAULT_KEYWORD_SIMILARITY_THRESHOLD)
    self.keyword_similarity_threshold = self.get_parameter('keyword_similarity_threshold').get_parameter_value().integer_value

    self.declare_parameter('log_to_file', DEFAULT_LOG_TO_FILE)
    self.log_to_file = self.get_parameter('log_to_file').get_parameter_value().bool_value

    self.declare_parameter('start_enabled', DEFAULT_START_ENABLED)
    self.pipeline_enabled = self.get_parameter('start_enabled').get_parameter_value().bool_value

    self.declare_parameter('stt_topic', DEFAULT_STT_TOPIC)
    self.declare_parameter('rag_topic', DEFAULT_RAG_TOPIC)
    self.declare_parameter('tts_topic', DEFAULT_TTS_TOPIC)

    get_logger().info(
      f'Loaded parameters:\n'
      f'  wakeup_keywords: {self.wakeup_keywords}\n'
      f'  keyword_similarity_threshold: {self.keyword_similarity_threshold}\n'
      f'  log_to_file: {self.log_to_file}\n'
      f'  start_enabled: {self.pipeline_enabled}\n'
      f'  stt_topic: {self.get_parameter("stt_topic").get_parameter_value().string_value}\n'
      f'  rag_topic: {self.get_parameter("rag_topic").get_parameter_value().string_value}\n'
      f'  tts_topic: {self.get_parameter("tts_topic").get_parameter_value().string_value}'
    )

    # Internal pipeline buffers passed between states
    self._current_user_text = ""
    self._current_rag_response = ""

    # State Machine Variable
    self.state = ChatbotState.LISTENING if self.pipeline_enabled else ChatbotState.OFF

    # Action Clients
    self.stt_action_client = ActionClient(self, STT, DEFAULT_STT_TOPIC)
    self.rag_action_client = ActionClient(self, Query, DEFAULT_RAG_TOPIC)
    self.tts_action_client = ActionClient(self, TTS, DEFAULT_TTS_TOPIC)

    # Pib Interface
    self.pib_interface = EduPipInterface(self)
    try:
      self.pib_interface.set_face_expression(FACE_EXPRESSION_LISTENING)
      self.pib_interface.move_to_random_pose(PoseCategory.NEUTRAL)
    finally:
      pass

    # Services and Execution Thread
    self.enable_srv = self.create_service(SetBool, "enable_pipeline", self.enable_callback)
    Thread(target=self.run_pipeline_loop, daemon=True).start()

    get_logger().info(f'{NODE_NAME} initialized successfully.')

  def enable_callback(self, request, response):
    if request.data:
      get_logger().info("Pipeline service call: Enabling system.")
      self.pipeline_enabled = True
      if self.state == ChatbotState.OFF:
        self.state = ChatbotState.LISTENING
    else:
      get_logger().info("Pipeline service call: Disabling system.")
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
  def process_transcription(self, text: str, score_cutoff: int = DEFAULT_KEYWORD_SIMILARITY_THRESHOLD) -> (bool, str):
    """
    Finds the best matching wakeword in `text` and returns the sub-string AFTER it.
    """
    text_clean = text.lower().strip()
    
    # 1. Use fuzz.partial_ratio to get a numeric score for extractOne
    match = process.extractOne(
      text_clean, 
      self.wakeup_keywords,
      scorer=fuzz.partial_ratio,
      score_cutoff=score_cutoff
    )
    
    if match:
      matched_phrase, score, index = match
      
      # 2. Get the exact alignment indices for the winning match
      alignment = fuzz.partial_ratio_alignment(text_clean, matched_phrase)
      
      if alignment:
        matched_end_idx = alignment.src_end
        remaining_text = text_clean[matched_end_idx:].lstrip(" ,.!?")
        return True, remaining_text
        
    return False, text_clean

  # ---------------------------------------------------------------------------
  # State Handlers
  # ---------------------------------------------------------------------------
  def _state_listening(self):
    """Blocks indefinitely until speech keyword is spoken, then shifts to THINKING."""
    get_logger().info("[State: LISTENING] Waiting for keyword activation...")

    # Listen state has infinite timeout (timeout_sec=None)
    # TODO: Maybe execute some idle poses while waiting for user input
    stt_goal = STT.Goal()
    stt_res = self._send_action_goal_sync(self.stt_action_client, stt_goal, timeout_sec=TIMEOUT_STT_SEC)
    get_logger().info(f"STT Result: '{stt_res.transcription.text}'")

    found, action_text = self.process_transcription(stt_res.transcription.text, self.keyword_similarity_threshold)
    if found:
      if len(action_text) > 10:
        get_logger().info(f"Wakeword detected. User said: '{action_text}'")
        self._current_user_text = action_text
        self.state = ChatbotState.THINKING
      else:
        get_logger().info(f"Wakeword detected, but no user query found. Restart listening...")
    else:
      get_logger().info(f"Wakeword not detected. Restart listening...")

    # Placeholder for testing
    #time.sleep(5.0)
    #self._current_user_text = "What can you tell me?"


  def _state_thinking(self):
    get_logger().info("[State: THINKING] Querying RAG backend...")

    rag_msg = Query.Goal()
    rag_msg.query = self._current_user_text
    rag_res = self._send_action_goal_sync(self.rag_action_client,rag_msg,timeout_sec=TIMEOUT_RAG_SEC)

    self._current_rag_response = rag_res.response
    get_logger().info(f"RAG Response: '{self._current_rag_response}'")

    self.state = ChatbotState.SPEAKING

  def _state_speaking(self):
    get_logger().info("[State: SPEAKING] Outputting response...")

    tts_goal = TTS.Goal(text=self._current_rag_response)
    tts_result = self._send_action_goal_sync(self.tts_action_client, tts_goal, timeout_sec=TIMEOUT_TTS_SEC)
    
    self.state = ChatbotState.LISTENING

  def _state_error(self, error_message: str):
    get_logger().error(f"[State: ERROR] Pipeline failure: {error_message}")
    # TODO: Maybe inform user that an error occurred (or maybe not, if there are too many errors)
    self.state = ChatbotState.LISTENING if self.pipeline_enabled else ChatbotState.OFF

  # ---------------------------------------------------------------------------
  # State Machine Execution Loop
  # ---------------------------------------------------------------------------
  def run_pipeline_loop(self):
    get_logger().info("Waiting for external servers to become ready...")
    self.stt_action_client.wait_for_server()
    get_logger().info("[1/3] Connected to STT Action Server.")
    self.rag_action_client.wait_for_server()
    get_logger().info("[2/3] Connected to RAG Action Server.")
    self.tts_action_client.wait_for_server()
    get_logger().info("[3/3] Connected to TTS Action Server.")
    get_logger().info("All external servers active. Activating pipeline...")

    #TODO: Cancel outstanding actions if pipeline was previously disabled mid-execution

    while rclpy.ok():
      if not self.pipeline_enabled:
        self.state = ChatbotState.OFF
        time.sleep(0.1)
        continue

      try:
        if self.state == ChatbotState.LISTENING:
          try:
            self.pib_interface.set_face_expression(FACE_EXPRESSION_LISTENING)
            self.pib_interface.move_to_random_pose(PoseCategory.NEUTRAL)
          finally:
            pass
          self._state_listening()
        elif self.state == ChatbotState.THINKING:
          try:
            self.pib_interface.set_face_expression(FACE_EXPRESSION_THINKING)
            self.pib_interface.move_to_random_pose(PoseCategory.THINKING)
          finally:
            pass
          self._state_thinking()
        elif self.state == ChatbotState.SPEAKING:
          try:
            self.pib_interface.set_face_expression(FACE_EXPRESSION_SPEAKING)
            self.pib_interface.move_to_random_pose(PoseCategory.SPEAKING)
          finally:
            pass
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