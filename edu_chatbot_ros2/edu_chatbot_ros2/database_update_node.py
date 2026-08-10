from datetime import datetime

import rclpy

from .edu_chatbot.database.database_update_service import DatabaseUpdateService
from .ros_logging_adapter import setup_ros_logging

NODE_NAME = 'database_update_node'

def get_logger():
  return rclpy.logging.get_logger(NODE_NAME)

def main():
  # Bridge Python logging to ROS logging for the edu_chatbot module
  setup_ros_logging(logger_name='edu_chatbot', node_name=NODE_NAME)
  
  # Init DatabaseUpdateService (uses LlamaIndex internally for ChromaDB and Ollama embedding)
  ingestion_service = DatabaseUpdateService()
  
  if not ingestion_service.ping():
    get_logger().error('Failed to connect to LLM or database services. Exiting.')
    return
  
  get_logger().info('Starting database update.')

  start_time = datetime.now() 
  docs_processed, chunks_created = ingestion_service.update_database()
  end_time = datetime.now()
  
  get_logger().info(f'Database update completed in {end_time - start_time}.')
  get_logger().info(f'Processed {docs_processed} documents, created {chunks_created} new chunks.')

if __name__ == '__main__':
  main()
