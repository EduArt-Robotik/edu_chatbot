import logging

from .llm_iface import LlmIface
from ..database.database_iface import DatabaseIface, DatabaseEntry

logger = logging.getLogger('edu_chatbot')

DEFAULT_MODEL_PERSONALITY = 'Answer the query politely and directly in 1 - 3 sentences.'
DEFAULT_RAG_INSTRUCTIONS  = 'Use the context if it helps answer the query. Do not force information from the context into the answer.'
DEFAULT_TOP_K = 3
DEFAULT_RELEVANCE_THRESHOLD = 0.1

class RagAgent:
  def __init__(
    self,
    llm: LlmIface,
    embedder: LlmIface,
    database: DatabaseIface,
    top_k: int = DEFAULT_TOP_K,
    model_personality: str = DEFAULT_MODEL_PERSONALITY,
    rag_instructions: str = DEFAULT_RAG_INSTRUCTIONS,
    relevance_threshold: float = DEFAULT_RELEVANCE_THRESHOLD
  ):
    self._llm = llm
    self._embedder = embedder
    self._database = database
    self._top_k = top_k
    self._model_personality = model_personality
    self._rag_instructions = rag_instructions
    self._relevance_threshold = relevance_threshold

  @property
  def model_personality(self) -> str:
    return self._model_personality

  @model_personality.setter
  def model_personality(self, value: str):
    self._model_personality = value

  @property
  def rag_instructions(self) -> str:
    return self._rag_instructions

  @rag_instructions.setter
  def rag_instructions(self, value: str):
    self._rag_instructions = value

  @property
  def llm(self) -> LlmIface:
    return self._llm

  @property
  def database(self) -> DatabaseIface:
    return self._database

  def is_healthy(self) -> bool:
    """Test connections to both LLM and database services."""
    return self._llm.ping() and self._database.ping()

  def generate_prompt(self, query: str, context: str = None) -> str:
    """Generate a RAG prompt for the LLM based on the query and optional context."""
    if context:
      # The small local LLM has a limited attention window, so the context is placed first and the query last
      # to ensure the instructions and query are within the attention window.
      return f'{context}\n\n{self._model_personality} {self._rag_instructions}\nQuery: {query}'
    else:
      return f'{self._model_personality}\nQuery: {query}'

  def query_llm(self, query: str, context: str = None) -> tuple[str, str]:
    """Generate a response for the given query using the LLM (without RAG)."""
    prompt = self.generate_prompt(query=query, context=context)
    return self._llm.generate(prompt=prompt), prompt

  def query_rag(self, query: str) -> tuple[str, str]:
    """Generate a response for the given query using the RAG pipeline."""
    
    # Embed the query using the LLM's embedding function
    query_embedding = self._embedder.embed(query)
    
    # Retrieve relevant chunks from vector store
    results = self._database.query(query_embedding=query_embedding, top_k=self._top_k, relevance_threshold=self._relevance_threshold)

    # Extract text from retrieved entries and combine into context
    context = None
    if results:
      context_chunks = [entry.document for entry in results]
      context = '\n\n'.join(context_chunks)

    # Generate response with retrieved context
    prompt = self.generate_prompt(query=query, context=context)
    return self._llm.generate(prompt=prompt), prompt