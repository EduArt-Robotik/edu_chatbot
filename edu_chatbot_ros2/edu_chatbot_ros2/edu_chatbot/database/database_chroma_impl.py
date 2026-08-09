import logging
import chromadb

from .database_iface import DatabaseIface
from .database_iface import DatabaseEntry

logger = logging.getLogger(__name__)

DEFAULT_COLLECTION_NAME = 'embeddings'

class ChromaDatabase(DatabaseIface):
  """ChromaDB implementation of the database interface."""

  def __init__(self, collection_name: str = DEFAULT_COLLECTION_NAME):
    super().__init__(collection_name)
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

  def get_collection(self, collection_name: str = None):
    if collection_name is None:
      collection_name = self.collection_name
    """Get or create a collection in ChromaDB."""
    try:
      collection = self.client.get_collection(name=collection_name)
      logger.debug(f'Collection "{collection_name}" found.')
    except Exception:
      logger.debug(f'Collection "{collection_name}" not found. Creating new collection.')
      collection = self.client.create_collection(name=collection_name)
    return collection

  def store(self, entries: list[DatabaseEntry]) -> None:
    """Store embeddings in the database."""
    ids = [entry.id for entry in entries]
    documents = [entry.document for entry in entries]
    embeddings = [entry.embedding for entry in entries]
    metadatas = [entry.metadata for entry in entries]


    collection = self.get_collection()
    collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

  def query(self, query_embedding: list, top_k: int) -> list[DatabaseEntry]:
    """Query the database for the most similar embeddings."""

    collection = self.get_collection()
    results = collection.query(query_embeddings=query_embedding, n_results=top_k)

    entries = []
    for i in range(len(results['ids'])):
      entries.append(DatabaseEntry(
        id=results['ids'][i],
        document=results['documents'][i],
        embedding=results['embeddings'][i],
        metadata=results['metadatas'][i]
      ))
    return entries