import logging
import os
import shutil

import chromadb
from llama_index.core import SimpleDirectoryReader
from llama_index.core.ingestion import IngestionPipeline, IngestionCache
from llama_index.core.node_parser import SemanticSplitterNodeParser, SentenceSplitter
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

logger = logging.getLogger('edu_chatbot')

DEFAULT_DATABASE_PATH = '/home/user/database'
DEFAULT_COLLECTION_NAME = 'embeddings'
DEFAULT_EMBEDDING_MODEL = 'nomic-embed-text'
DEFAULT_OLLAMA_BASE_URL = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
DEFAULT_CHROMA_HOST = os.environ.get('CHROMA_HOST', 'localhost')
DEFAULT_CHROMA_PORT = int(os.environ.get('CHROMA_PORT', '8000'))
DEFAULT_INGESTION_CACHE_DIR = os.environ.get('INGESTION_CACHE_PATH', '/home/user/data')

DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 128
DEFAULT_SEMANTIC_BREAKPOINT_THRESHOLD = 90
DEFAULT_SEMANTIC_BUFFER_SIZE = 1

SUPPORTED_EXTENSIONS = [".txt", ".docx", ".pptx", ".md", ".pdf"]

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
      chunk_size: int = DEFAULT_CHUNK_SIZE,
      chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
      breakpoint_percentile_threshold: int = DEFAULT_SEMANTIC_BREAKPOINT_THRESHOLD,
      buffer_size: int = DEFAULT_SEMANTIC_BUFFER_SIZE
  ):
    self._database_path = database_path
    self._collection_name = collection_name
    self._cache_path = os.path.join(DEFAULT_INGESTION_CACHE_DIR, collection_name)
    
    # Initialize embedding model
    self._embed_model = OllamaEmbedding(model_name=embedding_model, base_url=ollama_base_url)
    
    # Initialize ChromaDB - connect to remote server
    self._chroma_client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
    self._chroma_collection = self._chroma_client.get_or_create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})
    self._vector_store = ChromaVectorStore(chroma_collection=self._chroma_collection)
    
    # Initialize ingestion pipeline with caching (skips unchanged chunks)
    # Note: vector_store is NOT passed here to avoid batch size issues;
    # nodes are added to the vector store in batches in update_database()
    self._pipeline = IngestionPipeline(
      transformations=[
        SemanticSplitterNodeParser(
          embed_model=self._embed_model,
          buffer_size=buffer_size,
          breakpoint_percentile_threshold=breakpoint_percentile_threshold,
        ),
        SentenceSplitter(
          chunk_size=chunk_size,
          chunk_overlap=chunk_overlap,
        ),
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

  def _wipe_database(self) -> None:
    """Delete and recreate the target Chroma collection and reset ingestion cache."""
    logger.warning(f'Wiping Chroma collection {self._collection_name} before ingestion')

    # Reset Chroma collection.
    self._chroma_client.delete_collection(name=self._collection_name)
    self._chroma_collection = self._chroma_client.get_or_create_collection(name=self._collection_name, metadata={"hnsw:space": "cosine"})
    self._vector_store = ChromaVectorStore(chroma_collection=self._chroma_collection)

    # Reset ingestion cache in memory and on disk so all documents are re-embedded.
    if os.path.isdir(self._cache_path):
      shutil.rmtree(self._cache_path)
      logger.info(f'Removed ingestion cache directory {self._cache_path}')

  def update_database(self, wipe_database: bool = False) -> tuple[int, int]:
    """
    Load documents from the database path, chunk, embed, and store them.

    Table content is moved from structured reader metadata into the
    document content so it can participate in chunking and embedding.
    Non-scalar metadata is removed before the nodes are written to Chroma.
    
    Returns:
        Tuple of (total_documents_processed, total_nodes_created)
    """
    if wipe_database:
      self._wipe_database()
    else:
      if os.path.isdir(self._cache_path):
        try:
          self._pipeline.load(self._cache_path)
          logger.info(f'Loaded ingestion cache from {self._cache_path}')
        except Exception as e:
          logger.warning(f'Failed to load ingestion cache from {self._cache_path}: {e}')
      else:
        logger.info(f'No ingestion cache found at {self._cache_path}; starting fresh')

    # Load documents with allowed extensions from the directory
    reader = SimpleDirectoryReader(
      input_dir=self._database_path,
      recursive=True,
      required_exts=SUPPORTED_EXTENSIONS,
    )
    documents = reader.load_data(show_progress=True)
    
    logger.info(f'Loaded {len(documents)} chunks from {self._database_path}')

    # Prepare documents for the vector store.
    for document in documents:
      # Preserve table content.
      tables = document.metadata.get("tables")
      if tables:
        table_text = "\n\n".join(
          table.get("detailed_content", "")
          for table in tables
          if isinstance(table, dict)
          and table.get("detailed_content")
        )

        if table_text:
          document.set_content(
            document.get_content()
            + "\n\n--- TABLE CONTENT ---\n\n"
            + table_text
            + "\n\n--- END TABLE CONTENT ---"
          )

      # Chroma only accepts scalar metadata values: str, int, float, or None.
      # Keep useful scalar metadata and remove reader-specific structured metadata.
      invalid_metadata_keys = [
        key
        for key, value in document.metadata.items()
        if value is not None
        and not isinstance(value, (str, int, float))
      ]

      for key in invalid_metadata_keys:
        logger.debug(f"Removing non-scalar metadata before vector store: key={key} type={type(document.metadata[key]).__name__}")
        del document.metadata[key]

    # Run ingestion pipeline.
    nodes = self._pipeline.run(documents=documents, show_progress=True)
    logger.info(f'Processed {len(nodes)} new/updated chunks')

    # Persist cache so unchanged chunks are skipped in future runs.
    try:
      os.makedirs(self._cache_path, exist_ok=True)
      self._pipeline.persist(self._cache_path)
      logger.info(f'Successfully wrote ingestion cache to {self._cache_path}')
    except Exception as e:
      logger.warning(f'Failed to write ingestion cache to {self._cache_path}: {e}')

    # Optional safety check before writing to Chroma.
    for node in nodes:
      invalid_metadata = {
        key: value
        for key, value in node.metadata.items()
        if value is not None
        and not isinstance(value, (str, int, float))
      }

      if invalid_metadata:
        logger.error(f'Node {node.node_id} still contains invalid Chroma metadata: {list(invalid_metadata.keys())}')
        for key in invalid_metadata:
            del node.metadata[key]

    # Add nodes to vector store in batches to avoid ChromaDB batch size limit.
    if nodes:
      total_batches = (len(nodes) + CHROMA_BATCH_SIZE - 1) // CHROMA_BATCH_SIZE
      for i in range(0, len(nodes), CHROMA_BATCH_SIZE):
        batch = nodes[i:i + CHROMA_BATCH_SIZE]
        batch_num = i // CHROMA_BATCH_SIZE + 1
        logger.info(f'Adding batch {batch_num}/{total_batches} ({len(batch)} nodes) to vector store')
        self._vector_store.add(batch)
    
    return len(documents), len(nodes)
