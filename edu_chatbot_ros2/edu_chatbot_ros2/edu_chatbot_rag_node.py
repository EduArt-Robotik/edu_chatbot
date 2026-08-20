from datetime import datetime

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer

from edu_chatbot_msgs.action import Query

from .edu_chatbot.chatbot.llm_ollama_impl import OllamaLlm, DEFAULT_LLM_MODEL, DEFAULT_LLM_TEMPERATURE, DEFAULT_EMBEDDING_MODEL
from .edu_chatbot.chatbot.rag_agent import RagAgent, DEFAULT_TOP_K, DEFAULT_MODEL_PERSONALITY, DEFAULT_RAG_INSTRUCTIONS
from .edu_chatbot.database.database_chroma_impl import ChromaDatabase
from .ros_logging_adapter import setup_ros_logging

NODE_NAME         = 'edu_chatbot_rag_node'
LLM_ACTION_TOPIC  = 'llm/query'
RAG_ACTION_TOPIC  = 'rag/query'
DEFAULT_WARM_UP   = True

def get_logger():
  return rclpy.logging.get_logger(NODE_NAME)


class EduChatbotRagNode(Node):
  def __init__(self):
    super().__init__(NODE_NAME)
    
    # Declare ROS parameters with defaults
    self.declare_parameter('top_k', DEFAULT_TOP_K)
    self.declare_parameter('llm_model', DEFAULT_LLM_MODEL)
    self.declare_parameter('temperature', DEFAULT_LLM_TEMPERATURE)
    self.declare_parameter('model_personality', DEFAULT_MODEL_PERSONALITY)
    self.declare_parameter('rag_instructions', DEFAULT_RAG_INSTRUCTIONS)
    self.declare_parameter('embedding_model', DEFAULT_EMBEDDING_MODEL)
    self.declare_parameter('warm_up_pipeline', DEFAULT_WARM_UP)

    # Get parameters
    top_k             = self.get_parameter('top_k').get_parameter_value().integer_value
    llm_model         = self.get_parameter('llm_model').get_parameter_value().string_value
    temperature       = self.get_parameter('temperature').get_parameter_value().double_value
    model_personality = self.get_parameter('model_personality').get_parameter_value().string_value
    rag_instructions  = self.get_parameter('rag_instructions').get_parameter_value().string_value
    embedding_model   = self.get_parameter('embedding_model').get_parameter_value().string_value
    warm_up_pipeline  = self.get_parameter('warm_up_pipeline').get_parameter_value().bool_value
    
    get_logger().info(
      f'Loaded parameters:\n'
      f'  top_k: {top_k}\n'
      f'  llm_model: {llm_model}\n'
      f'  temperature: {temperature}\n'
      f'  model_personality: {model_personality}\n'
      f'  rag_instructions: {rag_instructions}\n'
      f'  embedding_model: {embedding_model}\n'
      f'  warm_up_pipeline: {warm_up_pipeline}'
    )
    
    # Init and test database
    chroma_db = ChromaDatabase()
    if chroma_db.ping():
      get_logger().info('ChromaDB server connection test successful.')
    else:
      raise RuntimeError('ChromaDB server connection test failed. Please ensure the ChromaDB server is running and accessible.')

    # Init and test LLM
    ollama_llm = OllamaLlm(model=llm_model, temperature=temperature, embedding_model=embedding_model)
    if ollama_llm.ping():
      get_logger().info('Ollama server connection test successful.')
    else:
      raise RuntimeError('Ollama server connection test failed. Please ensure the Ollama server is running and accessible.')

    # Init RAG agent with dependencies
    self.rag_agent = RagAgent(
      llm=ollama_llm,
      embedder=ollama_llm,
      database=chroma_db,
      top_k=top_k,
      model_personality=model_personality,
      rag_instructions=rag_instructions
    )
    
    if warm_up_pipeline:
      get_logger().info('Warming up the RAG pipeline...')
      try:
        self.rag_agent.query_rag(query="Hello there!")
        get_logger().info('RAG pipeline warm-up completed successfully.')
      except Exception as e:
        raise RuntimeError(f'Failed to warm up the RAG pipeline: {e}')

    # Only start action servers after successful initialization
    self.llm_action_server = ActionServer(self, Query, LLM_ACTION_TOPIC, self.llm_action_callback)
    self.rag_action_server = ActionServer(self, Query, RAG_ACTION_TOPIC, self.rag_action_callback)
    get_logger().info(f'{NODE_NAME} has been started successfully.')


  def llm_action_callback(self, goal_handle):
    self.get_logger().debug(f'Received LLM action goal: {goal_handle.request.query}')

    result = Query.Result()

    # Abort if agent isn't ready
    if self.rag_agent is None:
      self.get_logger().error('RAG agent not initialized')
      goal_handle.abort()
      result.response = "Agent not initialized"
      return result

    try:
      start_time = datetime.now()
      result.response, context = self.rag_agent.query_llm(query=goal_handle.request.query)
      self.get_logger().debug(f'LLM prompt:\n{context}')
      self.get_logger().debug(f'LLM response:\n{result.response}')
      self.get_logger().debug(f'LLM response time: {(datetime.now() - start_time).total_seconds()} seconds.')
      goal_handle.succeed()

    except Exception as e:
      self.get_logger().error(f'Failed to generate response: {e}')
      goal_handle.abort()
      result.response = f"Error: {e}"

    return result

  def rag_action_callback(self, goal_handle):
    self.get_logger().debug(f'Received RAG action goal: {goal_handle.request.query}')

    result = Query.Result()

    # Abort if agent isn't ready
    if self.rag_agent is None:
      self.get_logger().error('RAG agent not initialized')
      goal_handle.abort()
      result.response = "Agent not initialized"
      return result

    try:
      start_time = datetime.now()
      result.response, context = self.rag_agent.query_rag(query=goal_handle.request.query)
      self.get_logger().debug(f'RAG prompt:\n{context}')
      self.get_logger().debug(f'RAG response:\n{result.response}')
      self.get_logger().debug(f'RAG response time: {(datetime.now() - start_time).total_seconds()} seconds.')
      goal_handle.succeed()

    except Exception as e:
      self.get_logger().error(f'Failed to generate response: {e}')
      goal_handle.abort()
      result.response = f"Error: {e}"

    return result

def main():
  rclpy.init()
  
  # Bridge Python logging to ROS logging for the edu_chatbot module
  setup_ros_logging(node_name=NODE_NAME)

  # Init node
  try:
    edu_chatbot_node = EduChatbotRagNode()
  except Exception as e:
    get_logger().error(f'Failed to initialize {NODE_NAME}: {e}')
    rclpy.shutdown()
    return
  
  rclpy.spin(edu_chatbot_node)
  edu_chatbot_node.destroy_node()
  rclpy.shutdown()

if __name__ == '__main__':
  main()

