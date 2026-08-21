from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class DatabaseEntry:
  """Represents a single entry in the database."""
  id: str = ''
  document: str = ''
  embedding: list = None
  metadata: dict = None


class DatabaseIface(ABC):
  """Abstract interface for database/vector store providers."""

  def __init__(self, collection_name: str):
    self.collection_name = collection_name

  @abstractmethod
  def ping(self) -> bool:
    """Test the connection to the database service.
    
    Returns:
        True if the connection is successful, False otherwise.
    """
    pass

  @abstractmethod
  def store(self, entries: list[DatabaseEntry]) -> None:
    """Store embeddings in the database.

    Args:
        entries: A list of DatabaseEntry objects to be stored.
    """
    pass

  @abstractmethod
  def query(self, query_embedding: list, top_k: int) -> list[DatabaseEntry]:
    """Query the database for the most similar embeddings.

    Args:
        query_embedding: The embedding to query against the database.
        top_k: The number of top results to return.

    Returns:
        A list of the top_k most similar DatabaseEntry objects.
    """
    pass