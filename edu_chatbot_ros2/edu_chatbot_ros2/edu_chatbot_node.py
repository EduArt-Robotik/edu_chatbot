import rclpy
from rclpy.node import Node
from std_msgs.msg import String

#from ollama import chat
#from ollama import ChatResponse
from ollama import generate
from ollama import GenerateResponse

import chromadb

from datetime import datetime

NODE_NAME    = 'edu_chatbot_node'
INPUT_TOPIC  = 'rag/input'
OUTPUT_TOPIC = 'rag/output'

LLM_TEMPERATURE = 0.2
LLM_MODEL       = 'gemma3:270m'
EMBEDDING_MODEL = 'nomic-embed-text'

MODEL_PERSONALITY   = 'You are a helpful and concise fair exhibition chatbot.'
ANSWER_INSTRUCTIONS = 'Answer the following query concisely in 1 to 3 sentences providing accurate information. Provide a plain text answer.'
RAG_INSTRUCTIONS    = 'Use the following context to answer the query. Answer with "I don\'t know" if the answer is not contained in the context.'


def get_logger():
  return rclpy.logging.get_logger(NODE_NAME)


def generate_prompt(query: str, context: str = None) -> str:
  if context:
    return f'{MODEL_PERSONALITY}\n{ANSWER_INSTRUCTIONS}\nQuery: {query}\n{RAG_INSTRUCTIONS}\nContext: {context}'
  else:
    return f'{MODEL_PERSONALITY}\n{ANSWER_INSTRUCTIONS}\nQuery: {query}'


def probe_chromadb_connection() -> bool:
  get_logger().debug('Check ChromaDB server connection...')

  try:
    chroma_client = chromadb.Client()
    get_logger().debug(f'ChromaDB server heartbeat: {chroma_client.heartbeat()}')
    get_logger().info('ChromaDB server connection successful.')
    return True

  except Exception as e:
    get_logger().error(f'Failed to connect to ChromaDB client: {e}')
    return False


def probe_ollama_connection() -> bool:
  get_logger().debug('Check Ollama server connection...')
  query = 'Answer the following query briefly and concisely in 1 to 3 sentences: Why is the sky blue?'
  get_logger().debug(f'Query: {query}\n')

  try:
    query_ts = datetime.now()
    response: GenerateResponse = generate(model=LLM_MODEL, prompt=query)
    get_logger().debug(f'Got response in {(datetime.now() - query_ts).total_seconds()} seconds.')
    get_logger().debug(f'Response: {response.response}')
    get_logger().info('Ollama server connection test successful.')
    return True

  except Exception as e:
    get_logger().error(f'Failed to connect to Ollama server: {e}')
    return False


class EduChatbotNode(Node):
  def __init__(self):
    super().__init__(NODE_NAME)
    self.text_in_sub = self.create_subscription( String, INPUT_TOPIC, self.listener_callback, 10)
    self.text_out_pub = self.create_publisher(String, OUTPUT_TOPIC, 10)
    self.get_logger().info('EduChatbotNode has been started.')

  def listener_callback(self, msg):
    self.get_logger().debug(f'Received message: {msg.data}')

    prompt = generate_prompt(query=msg.data)
    self.get_logger().debug(f'Generated prompt for LLM:\n{prompt}')
    try:
      response: GenerateResponse = generate(model=LLM_MODEL, prompt=prompt, options={'temperature': LLM_TEMPERATURE})

      response_msg = String()
      response_msg.data = f'{response.response}'
      self.text_out_pub.publish(response_msg)
      self.get_logger().debug(f'Published response:\n{response_msg.data}')
    except Exception as e:
      self.get_logger().error(f'Failed to generate response: {e}')


def main():
  chroma_success = probe_chromadb_connection()
  ollama_success = probe_ollama_connection()

  if not chroma_success or not ollama_success:
    get_logger().info('One or more tests failed. Exiting.')
    return
  
  get_logger().info('All tests passed successfully.')
  
  rclpy.init()
  edu_chatbot_node = EduChatbotNode()
  rclpy.spin(edu_chatbot_node)
  edu_chatbot_node.destroy_node()
  rclpy.shutdown()

if __name__ == '__main__':
  main()
