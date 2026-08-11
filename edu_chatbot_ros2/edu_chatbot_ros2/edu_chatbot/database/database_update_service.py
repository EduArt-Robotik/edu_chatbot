import logging
import os

import chromadb
from llama_index.core import SimpleDirectoryReader
from llama_index.core.ingestion import IngestionPipeline, IngestionCache
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

logger = logging.getLogger(__name__)

DEFAULT_DATABASE_PATH = '/home/user/database'
DEFAULT_COLLECTION_NAME = 'embeddings'
DEFAULT_EMBEDDING_MODEL = 'nomic-embed-text'
DEFAULT_OLLAMA_BASE_URL = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
DEFAULT_CHROMA_HOST = os.environ.get('CHROMA_HOST', 'localhost')
DEFAULT_CHROMA_PORT = int(os.environ.get('CHROMA_PORT', '8000'))

# ChromaDB HTTP client has payload size limits. With embeddings (~3KB each)
# plus metadata, batch size of 100 keeps payloads under typical limits.
CHROMA_BATCH_SIZE = 100


class DatabaseUpdateService:
  """Manages document ingestion and vector storage using LlamaIndex.
  
  Note: This service uses LlamaIndex's own abstractions for embedding and storage,
  which are tightly integrated in the ingestion pipeline. For the query path,
  use RagAgent with the DatabaseIface and LlmIface interfaces.
  """
  
  def __init__(
      self,
      database_path: str = DEFAULT_DATABASE_PATH,
      collection_name: str = DEFAULT_COLLECTION_NAME,
      embedding_model: str = DEFAULT_EMBEDDING_MODEL,
      ollama_base_url: str = DEFAULT_OLLAMA_BASE_URL,
      chroma_host: str = DEFAULT_CHROMA_HOST,
      chroma_port: int = DEFAULT_CHROMA_PORT,
  ):
    self._database_path = database_path
    self._collection_name = collection_name
    
    # Initialize embedding model
    self._embed_model = OllamaEmbedding(model_name=embedding_model, base_url=ollama_base_url)
    
    # Initialize ChromaDB - connect to remote server
    self._chroma_client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
    self._chroma_collection = self._chroma_client.get_or_create_collection(name=collection_name)
    self._vector_store = ChromaVectorStore(chroma_collection=self._chroma_collection)
    
    # Initialize ingestion pipeline with caching (skips unchanged chunks)
    # Note: vector_store is NOT passed here to avoid batch size issues;
    # nodes are added to the vector store in batches in update_database()
    self._pipeline = IngestionPipeline(
      transformations=[
        SentenceSplitter(chunk_size=1024, chunk_overlap=200),
        self._embed_model,
      ],
      cache=IngestionCache(),
    )

  def ping(self) -> bool:
    """Test connections to ChromaDB and Ollama embedding service.
    
    Returns:
        True if both services are accessible, False otherwise.
    """
    try:
      # Test ChromaDB connection
      self._chroma_client.heartbeat()
      
      # Test Ollama embedding by generating a small test embedding
      self._embed_model.get_text_embedding("test")
      
      return True
    except Exception as e:
      logger.error(f'Health check failed: {e}')
      return False

  def update_database(self) -> tuple[int, int]:
    """
    Load documents from the database path, chunk, embed, and store them.
    Uses IngestionCache to skip embedding unchanged chunks.
    
    Returns:
        Tuple of (total_documents_processed, total_nodes_created)
    """
    # Load all documents from the directory
    reader = SimpleDirectoryReader(
      input_dir=self._database_path,
      recursive=True,
    )
    documents = reader.load_data(show_progress=True)
    
    logger.info(f'Loaded {len(documents)} documents from {self._database_path}')
    
    # Run ingestion pipeline (automatically skips unchanged chunks via cache)
    nodes = self._pipeline.run(documents=documents, show_progress=True)
    
    logger.info(f'Processed {len(nodes)} new/updated chunks')
    
    # Add nodes to vector store in batches to avoid ChromaDB batch size limit
    if nodes:
      total_batches = (len(nodes) + CHROMA_BATCH_SIZE - 1) // CHROMA_BATCH_SIZE
      for i in range(0, len(nodes), CHROMA_BATCH_SIZE):
        batch = nodes[i:i + CHROMA_BATCH_SIZE]
        batch_num = i // CHROMA_BATCH_SIZE + 1
        logger.info(f'Adding batch {batch_num}/{total_batches} ({len(batch)} nodes) to vector store')
        self._vector_store.add(batch)
    
    return len(documents), len(nodes)
