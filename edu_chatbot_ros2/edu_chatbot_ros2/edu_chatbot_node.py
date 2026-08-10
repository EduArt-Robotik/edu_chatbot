from datetime import datetime

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from .edu_chatbot.chatbot.llm_ollama_impl import OllamaLlm, DEFAULT_LLM_MODEL, DEFAULT_LLM_TEMPERATURE, DEFAULT_EMBEDDING_MODEL
from .edu_chatbot.chatbot.rag_agent import RagAgent, DEFAULT_TOP_K, DEFAULT_MODEL_PERSONALITY, DEFAULT_RAG_INSTRUCTIONS
from .edu_chatbot.database.database_chroma_impl import ChromaDatabase
from .ros_logging_adapter import setup_ros_logging

NODE_NAME    = 'edu_chatbot_node'
LLM_INPUT_TOPIC  = 'llm/input'
LLM_OUTPUT_TOPIC = 'llm/output'
RAG_INPUT_TOPIC  = 'rag/input'
RAG_OUTPUT_TOPIC = 'rag/output'


def get_logger():
  return rclpy.logging.get_logger(NODE_NAME)


class EduChatbotNode(Node):
  def __init__(self):
    super().__init__(NODE_NAME)
    
    # Declare ROS parameters with defaults
    self.declare_parameter('model', DEFAULT_LLM_MODEL)
    self.declare_parameter('temperature', DEFAULT_LLM_TEMPERATURE)
    self.declare_parameter('embedding_model', DEFAULT_EMBEDDING_MODEL)
    self.declare_parameter('top_k', DEFAULT_TOP_K)
    self.declare_parameter('model_personality', DEFAULT_MODEL_PERSONALITY)
    self.declare_parameter('rag_instructions', DEFAULT_RAG_INSTRUCTIONS)
    
    # Initialize components (will be set up after parameter reading)
    self.rag_agent = None

    self.llm_in_sub = self.create_subscription(String, LLM_INPUT_TOPIC, self.llm_callback, 10)
    self.llm_out_pub = self.create_publisher(String, LLM_OUTPUT_TOPIC, 10)
    self.rag_in_sub = self.create_subscription(String, RAG_INPUT_TOPIC, self.rag_callback, 10)
    self.rag_out_pub = self.create_publisher(String, RAG_OUTPUT_TOPIC, 10)
    
    self.get_logger().info('EduChatbotNode has been started.')

  def setup_rag_agent(self) -> bool:
    """Initialize the RAG agent with parameters. Returns True on success."""
    # Get parameters
    model = self.get_parameter('model').get_parameter_value().string_value
    temperature = self.get_parameter('temperature').get_parameter_value().double_value
    embedding_model = self.get_parameter('embedding_model').get_parameter_value().string_value
    top_k = self.get_parameter('top_k').get_parameter_value().integer_value
    model_personality = self.get_parameter('model_personality').get_parameter_value().string_value
    rag_instructions = self.get_parameter('rag_instructions').get_parameter_value().string_value
    
    self.get_logger().info(
      f'Loaded parameters:\n'
      f'  model: {model}\n'
      f'  temperature: {temperature}\n'
      f'  embedding_model: {embedding_model}\n'
      f'  top_k: {top_k}\n'
      f'  model_personality: {model_personality}\n'
      f'  rag_instructions: {rag_instructions}'
    )
    
    # Init and test database
    chroma_db = ChromaDatabase()
    if chroma_db.ping():
      self.get_logger().info('ChromaDB server connection test successful.')
    else:
      self.get_logger().error('ChromaDB server connection test failed.')
      return False

    # Init and test LLM
    ollama_llm = OllamaLlm(model=model, temperature=temperature, embedding_model=embedding_model)
    if ollama_llm.ping():
      self.get_logger().info('Ollama server connection test successful.')
    else:
      self.get_logger().error('Ollama server connection test failed.')
      return False

    # Init RAG agent with dependencies
    self.rag_agent = RagAgent(
      llm=ollama_llm,
      embedder=ollama_llm,
      database=chroma_db,
      top_k=top_k,
      model_personality=model_personality,
      rag_instructions=rag_instructions
    )
    
    self.get_logger().info('All components are up and running.')
    return True

  def llm_callback(self, msg):
    self.get_logger().debug(f'Received llm query: {msg.data}')

    if self.rag_agent is None:
      self.get_logger().error('RAG agent not initialized')
      return

    try:
      start_time = datetime.now()
      response, prompt = self.rag_agent.query_llm(query=msg.data)

      response_msg = String()
      response_msg.data = response
      self.llm_out_pub.publish(response_msg)
      end_time = datetime.now()
      self.get_logger().debug(f'LLM prompt:\n{prompt}')
      self.get_logger().debug(f'LLM response:\n{response_msg.data}')
      self.get_logger().debug(f'LLM response time: {(end_time - start_time).total_seconds()} seconds.')
    except Exception as e:
      self.get_logger().error(f'Failed to generate response: {e}')

  def rag_callback(self, msg):
    self.get_logger().debug(f'Received rag query: {msg.data}')

    if self.rag_agent is None:
      self.get_logger().error('RAG agent not initialized')
      return

    try:
      start_time = datetime.now()
      response, context = self.rag_agent.query_rag(query=msg.data)

      response_msg = String()
      response_msg.data = response
      self.rag_out_pub.publish(response_msg)
      self.get_logger().debug(f'RAG prompt:\n{context}')
      self.get_logger().debug(f'RAG response:\n{response_msg.data}')
      self.get_logger().debug(f'RAG response time: {(datetime.now() - start_time).total_seconds()} seconds.')
    except Exception as e:
      self.get_logger().error(f'Failed to generate response: {e}')

def main():
  rclpy.init()
  
  # Bridge Python logging to ROS logging for the edu_chatbot module
  setup_ros_logging(logger_name='edu_chatbot', node_name=NODE_NAME)

  # Init node (parameters are declared in __init__)
  edu_chatbot_node = EduChatbotNode()
  
  # Setup RAG agent with parameters
  if not edu_chatbot_node.setup_rag_agent():
    get_logger().error('Failed to initialize RAG agent. Exiting.')
    edu_chatbot_node.destroy_node()
    rclpy.shutdown()
    return
  
  rclpy.spin(edu_chatbot_node)
  edu_chatbot_node.destroy_node()
  rclpy.shutdown()

if __name__ == '__main__':
  main()

