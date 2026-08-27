import logging
import os

import chromadb

from .database_iface import DatabaseIface
from .database_iface import DatabaseEntry

logger = logging.getLogger('edu_chatbot')

DEFAULT_COLLECTION_NAME = 'embeddings'
DEFAULT_CHROMA_HOST = os.environ.get('CHROMA_HOST', 'localhost')
DEFAULT_CHROMA_PORT = int(os.environ.get('CHROMA_PORT', '8000'))

class ChromaDatabase(DatabaseIface):
  """ChromaDB implementation of the database interface."""

  def __init__(
      self,
      collection_name: str = DEFAULT_COLLECTION_NAME,
      chroma_host: str = DEFAULT_CHROMA_HOST,
      chroma_port: int = DEFAULT_CHROMA_PORT,
  ):
    super().__init__(collection_name)
    self._chroma_host = chroma_host
    self._chroma_port = chroma_port
    self._client = None

  @property
  def client(self):
    if self._client is None:
      self._client = chromadb.HttpClient(host=self._chroma_host, port=self._chroma_port)
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
    """Get or create a collection in ChromaDB."""
    if collection_name is None:
      collection_name = self.collection_name
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

  def query(self, query_embedding: list, top_k: int, relevance_threshold: float) -> list[DatabaseEntry]:
    """Query the database for the most similar embeddings."""

    collection = self.get_collection()
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)

    entries = []
    # ChromaDB returns nested lists: {'ids': [['id1', 'id2']], ...}
    # Access the first (and only) query result with [0]
    for i in range(len(results['ids'][0])):
      distance = results['distances'][0][i]
      score = 1.0 - distance

      logger.debug(f"Retrieved chunk {results['ids'][0][i]}: "f"distance={distance:.4f}, score={score:.4f}")
      if score < relevance_threshold:
        continue

      entries.append((
        DatabaseEntry(
          id=results['ids'][0][i],
          document=results['documents'][0][i],
          embedding=results['embeddings'][0][i] if results['embeddings'] else None,
          metadata=results['metadatas'][0][i],
          score=score
        )
      ))
    return entries