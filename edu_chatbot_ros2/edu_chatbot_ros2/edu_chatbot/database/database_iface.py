from abc import ABC, abstractmethod


class DatabaseIface(ABC):
  """Abstract interface for database/vector store providers."""

  @abstractmethod
  def ping(self) -> bool:
    """Test the connection to the database service.
    
    Returns:
        True if the connection is successful, False otherwise.
    """
    pass
