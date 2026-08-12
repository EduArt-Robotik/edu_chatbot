import logging
from ollama import list as ollama_list, ListResponse
from ollama import generate, GenerateResponse
from ollama import embed, EmbedResponse
from datetime import datetime

from .llm_iface import LlmIface

DEFAULT_LLM_TEMPERATURE = 0.2
DEFAULT_LLM_MODEL = 'gemma3:270m'
DEFAULT_EMBEDDING_MODEL = 'nomic-embed-text'

logger = logging.getLogger('edu_chatbot')


class OllamaLlm(LlmIface):
  """Ollama implementation of the LLM interface."""

  def __init__(self, model: str = DEFAULT_LLM_MODEL, temperature: float = DEFAULT_LLM_TEMPERATURE, embedding_model: str = DEFAULT_EMBEDDING_MODEL):
    super().__init__(model, temperature)
    self._embedding_model = embedding_model

  def ping(self) -> bool:
    """Test the connection to the Ollama server."""
    try:
        response: ListResponse = ollama_list()
        return True
    except Exception as e:
        logger.error(f'Failed to ping Ollama server: {e}')
        return False


  def generate(self, prompt: str) -> str:
    """Generate a response using Ollama."""
    query_ts = datetime.now()
    try:
        response: GenerateResponse = generate(model=self.model, prompt=prompt, options={'temperature': self.temperature})
    except Exception as e:
        logger.error(f'Failed to generate response: {e}')
        raise
    logger.debug(f'Got response in {(datetime.now() - query_ts).total_seconds()} seconds.')
    return response.response


  def embed(self, context: str) -> list[float]:
    """Generate an embedding using Ollama."""
    try:
        response: EmbedResponse = embed(model=self._embedding_model, input=context)
    except Exception as e:
        logger.error(f'Failed to generate embedding: {e}')
        raise
    return response.embeddings[0]