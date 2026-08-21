"""ROS logging handler that bridges Python's standard logging to rclpy logging."""

import logging
import rclpy
import rclpy.logging


class RosLoggingAdapter(logging.Handler):
  """A logging handler that forwards Python log records to ROS logging."""

  def __init__(self, node_name: str = 'python_logger'):
    super().__init__()
    self.node_name = node_name

  def emit(self, record: logging.LogRecord) -> None:
    """Emit a log record to ROS logging."""
    # Check if rclpy is initialized before attempting to log
    if not rclpy.ok():
      return

    try:
      # Construct hierarchical logger name
      logger_name = f"{self.node_name}" if record.name != 'root' else self.node_name
      ros_logger = rclpy.logging.get_logger(logger_name)
      
      msg = self.format(record)
      
      # Map Python log levels to rclpy log methods
      if record.levelno >= logging.CRITICAL:
        ros_logger.fatal(msg)
      elif record.levelno >= logging.ERROR:
        ros_logger.error(msg)
      elif record.levelno >= logging.WARNING:
        ros_logger.warn(msg)
      elif record.levelno >= logging.INFO:
        ros_logger.info(msg)
      else:
        ros_logger.debug(msg)
              
    except Exception:
      self.handleError(record)


def setup_ros_logging(node_name: str = 'edu_chatbot_node', logger_name: str = 'edu_chatbot', level: int = logging.DEBUG) -> None:
  """Set up ROS logging for a Python logger."""
  logger = logging.getLogger(logger_name)
  logger.setLevel(level)

  # Prevent duplicate log messages
  logger.propagate = False
        
  # Avoid adding duplicate handlers
  if not any(isinstance(h, RosLoggingAdapter) for h in logger.handlers):
    handler = RosLoggingAdapter(node_name=node_name)
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)