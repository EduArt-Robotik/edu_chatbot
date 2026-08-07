import logging
import chromadb

from .database_iface import DatabaseIface

logger = logging.getLogger(__name__)


class ChromaDatabase(DatabaseIface):
  """ChromaDB implementation of the database interface."""

  def __init__(self):
    self._client = None

  @property
  def client(self):
    if self._client is None:
      self._client = chromadb.Client()
    return self._client

  def ping(self) -> bool:
    """Test the connection to the ChromaDB server."""
    logger.debug('Check ChromaDB server connection...')

    try:
      logger.debug(f'ChromaDB server heartbeat: {self.client.heartbeat()}')
      logger.info('ChromaDB server connection successful.')
      return True

    except Exception as e:
      logger.error(f'Failed to connect to ChromaDB client: {e}')
      return False
