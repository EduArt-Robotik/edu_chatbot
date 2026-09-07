from datetime import datetime

import rclpy
from rclpy.node import Node

from .edu_chatbot.database.database_update_service import DatabaseUpdateService, DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP, DEFAULT_SEMANTIC_BREAKPOINT_THRESHOLD, DEFAULT_SEMANTIC_BUFFER_SIZE
from .ros_logging_adapter import setup_ros_logging

NODE_NAME = 'database_update_node'

WIPE_PARAM_NAME = 'wipe_database'
CHUNK_SIZE_PARAM_NAME = 'chunk_size'
OVERLAP_PARAM_NAME = 'chunk_overlap'
BREAKPOINT_THRESHOLD_PARAM_NAME = 'semantic_splitting_threshold'
BUFFER_SIZE_PARAM_NAME = 'buffer_size'

DEFAULT_WIPE_DATABASE = True


def get_logger():
  return rclpy.logging.get_logger(NODE_NAME)

def main():
  rclpy.init()
  node: Node = rclpy.create_node(NODE_NAME)

  # Bridge Python logging to ROS logging for the edu_chatbot module
  setup_ros_logging(node_name=NODE_NAME)

  node.declare_parameter(WIPE_PARAM_NAME, DEFAULT_WIPE_DATABASE)
  node.declare_parameter(CHUNK_SIZE_PARAM_NAME, DEFAULT_CHUNK_SIZE)
  node.declare_parameter(OVERLAP_PARAM_NAME, DEFAULT_CHUNK_OVERLAP)
  node.declare_parameter(BREAKPOINT_THRESHOLD_PARAM_NAME, DEFAULT_SEMANTIC_BREAKPOINT_THRESHOLD)
  node.declare_parameter(BUFFER_SIZE_PARAM_NAME, DEFAULT_SEMANTIC_BUFFER_SIZE)

  wipe_database = bool(node.get_parameter(WIPE_PARAM_NAME).value)
  chunk_size = int(node.get_parameter(CHUNK_SIZE_PARAM_NAME).value)
  chunk_overlap = int(node.get_parameter(OVERLAP_PARAM_NAME).value)
  breakpoint_threshold = int(node.get_parameter(BREAKPOINT_THRESHOLD_PARAM_NAME).value)
  buffer_size = int(node.get_parameter(BUFFER_SIZE_PARAM_NAME).value)

  get_logger().info(
    f'Loaded parameters:\n'
    f'  wipe_database: {wipe_database}\n'
    f'  chunk_size: {chunk_size}\n'
    f'  chunk_overlap: {chunk_overlap}\n'
    f'  semantic_splitting_threshold: {breakpoint_threshold}\n'
    f'  buffer_size: {buffer_size}'
  )
  
  try:  
    # Init DatabaseUpdateService (uses LlamaIndex internally for ChromaDB and Ollama embedding)
    ingestion_service = DatabaseUpdateService(
      chunk_size=chunk_size,
      chunk_overlap=chunk_overlap,
      breakpoint_percentile_threshold=breakpoint_threshold,
      buffer_size=buffer_size
    )
    
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
