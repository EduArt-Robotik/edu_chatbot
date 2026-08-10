import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from .edu_chatbot.chatbot.llm_ollama_impl import OllamaLlm
from .edu_chatbot.chatbot.rag_agent import RagAgent
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
  def __init__(self, rag_agent: RagAgent):
    super().__init__(NODE_NAME)
    self.rag_agent = rag_agent

    self.llm_in_sub = self.create_subscription(String, LLM_INPUT_TOPIC, self.llm_callback, 10)
    self.llm_out_pub = self.create_publisher(String, LLM_OUTPUT_TOPIC, 10)
    self.rag_in_sub = self.create_subscription(String, RAG_INPUT_TOPIC, self.rag_callback, 10)
    self.rag_out_pub = self.create_publisher(String, RAG_OUTPUT_TOPIC, 10)
    
    self.get_logger().info('EduChatbotNode has been started.')

  def llm_callback(self, msg):
    self.get_logger().debug(f'Received llm query: {msg.data}')

    try:
      response, prompt = self.rag_agent.query_llm(query=msg.data)

      response_msg = String()
      response_msg.data = response
      self.llm_out_pub.publish(response_msg)
      self.get_logger().debug(f'Llm prompt:\n{prompt}')
      self.get_logger().debug(f'Published llm response:\n{response_msg.data}')
    except Exception as e:
      self.get_logger().error(f'Failed to generate response: {e}')

  def rag_callback(self, msg):
    self.get_logger().debug(f'Received rag query: {msg.data}')

    try:
      response, context = self.rag_agent.query_rag(query=msg.data)

      response_msg = String()
      response_msg.data = response
      self.rag_out_pub.publish(response_msg)
      self.get_logger().debug(f'Rag prompt:\n{context}')
      self.get_logger().debug(f'Published rag response:\n{response_msg.data}')
    except Exception as e:
      self.get_logger().error(f'Failed to generate response: {e}')

def main():
  # Bridge Python logging to ROS logging for the edu_chatbot module
  setup_ros_logging(logger_name='edu_chatbot', node_name=NODE_NAME)

  # Init and test database
  chroma_db = ChromaDatabase()
  if chroma_db.ping():
    get_logger().info('ChromaDB server connection test successful.')
  else:
    get_logger().info('ChromaDB server connection test failed. Exiting.')
    return

  # Init and test LLM
  ollama_llm = OllamaLlm('gemma3:1b')
  if ollama_llm.ping():
    get_logger().info('Ollama server connection test successful.')
  else:
    get_logger().info('Ollama server connection test failed. Exiting.')
    return

  # Init RAG agent with dependencies
  # OllamaLlm handles both text generation and embeddings
  rag_agent = RagAgent(llm=ollama_llm, embedder=ollama_llm, database=chroma_db)
  
  get_logger().info('All components are up and running.')
  
  # Init node with RAG agent
  rclpy.init()
  edu_chatbot_node = EduChatbotNode(rag_agent=rag_agent)
  rclpy.spin(edu_chatbot_node)
  edu_chatbot_node.destroy_node()
  rclpy.shutdown()

if __name__ == '__main__':
  main()

