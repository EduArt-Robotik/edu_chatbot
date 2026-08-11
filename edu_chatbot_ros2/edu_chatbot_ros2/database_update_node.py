from datetime import datetime

import rclpy
from rclpy.node import Node

from .edu_chatbot.database.database_update_service import DatabaseUpdateService
from .ros_logging_adapter import setup_ros_logging

NODE_NAME = 'database_update_node'
WIPE_PARAM_NAME = 'wipe_database'

def get_logger():
  return rclpy.logging.get_logger(NODE_NAME)

def main():
  rclpy.init()
  node: Node = rclpy.create_node(NODE_NAME)

  # Bridge Python logging to ROS logging for the edu_chatbot module
  setup_ros_logging(logger_name='edu_chatbot', node_name=NODE_NAME)

  node.declare_parameter(WIPE_PARAM_NAME, False)
  wipe_database = bool(node.get_parameter(WIPE_PARAM_NAME).value)

  get_logger().info(
    f'Loaded parameters:\n'
    f'  wipe_database: {wipe_database}'
  )
  
  try:  
    # Init DatabaseUpdateService (uses LlamaIndex internally for ChromaDB and Ollama embedding)
    ingestion_service = DatabaseUpdateService()
    
    if not ingestion_service.ping():
      get_logger().error('Failed to connect to LLM or database services. Exiting.')
      return
    
    get_logger().info('Starting database update.')

    start_time = datetime.now() 
    docs_processed, chunks_created = ingestion_service.update_database(wipe_database=wipe_database)
    end_time = datetime.now()
    
    get_logger().info(f'Database update completed in {end_time - start_time}.')
    get_logger().info(f'Processed {docs_processed} documents, created {chunks_created} new chunks.')
  finally:
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
  main()
