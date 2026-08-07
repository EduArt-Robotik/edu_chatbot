"""ROS logging handler that bridges Python's standard logging to rclpy logging."""

import logging
import rclpy.logging


class RosLoggingAdapter(logging.Handler):
    """A logging handler that forwards Python log records to ROS logging.
    
    This allows modules using standard Python logging to have their logs
    appear in ROS logging infrastructure when running in a ROS context.
    
    Usage:
        import logging
        from ros_logging_handler import RosLoggingAdapter
        
        # Configure a specific logger
        logger = logging.getLogger('edu_chatbot')
        logger.addHandler(RosLoggingAdapter())
        logger.setLevel(logging.DEBUG)
        
        # Or configure root logger to capture all logs
        logging.getLogger().addHandler(RosLoggingAdapter())
    """

    def __init__(self, node_name: str = 'python_logger'):
        """Initialize the ROS logging handler.
        
        Args:
            node_name: The ROS logger name to use. Defaults to 'python_logger'.
        """
        super().__init__()
        self.node_name = node_name

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to ROS logging.
        
        Args:
            record: The log record to emit.
        """
        try:
            # Use the logger name from the record for better traceability
            logger_name = f"{self.node_name}.{record.name}" if record.name != 'root' else self.node_name
            ros_logger = rclpy.logging.get_logger(logger_name)
            
            msg = self.format(record)
            
            if record.levelno >= logging.CRITICAL:
                ros_logger.fatal(msg)
            elif record.levelno >= logging.ERROR:
                ros_logger.error(msg)
            elif record.levelno >= logging.WARNING:
                ros_logger.warning(msg)
            elif record.levelno >= logging.INFO:
                ros_logger.info(msg)
            else:
                ros_logger.debug(msg)
                
        except Exception:
            # Fallback to default handler behavior on error
            self.handleError(record)


def setup_ros_logging(logger_name: str = 'edu_chatbot', node_name: str = 'edu_chatbot_node', level: int = logging.DEBUG) -> None:
    """Convenience function to set up ROS logging for a Python logger hierarchy.
    
    Args:
        logger_name: The Python logger name/prefix to attach the handler to.
        node_name: The ROS node name to use for logging.
        level: The logging level to set.
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # Avoid adding duplicate handlers
    if not any(isinstance(h, RosLoggingAdapter) for h in logger.handlers):
        handler = RosLoggingAdapter(node_name=node_name)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)
