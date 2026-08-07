import logging
from ollama import generate, list
from ollama import GenerateResponse, ListResponse
from datetime import datetime

from .llm_iface import LlmIface

LLM_TEMPERATURE = 0.2
LLM_MODEL = 'gemma3:270m'
EMBEDDING_MODEL = 'nomic-embed-text'

logger = logging.getLogger(__name__)


class OllamaLlm(LlmIface):
  """Ollama implementation of the LLM interface."""

  def __init__(self, temperature: float = LLM_TEMPERATURE):
    self.temperature = temperature

  def generate(self, prompt: str, model: str = LLM_MODEL) -> str:
    """Generate a response using Ollama."""
    query_ts = datetime.now()
    try:
        response: GenerateResponse = generate(model=model, prompt=prompt, options={'temperature': self.temperature})
    except Exception as e:
        logger.error(f'Failed to generate response: {e}')
        raise
    logger.debug(f'Got response in {(datetime.now() - query_ts).total_seconds()} seconds.')
    return response.response

  def ping(self) -> bool:
    """Test the connection to the Ollama server."""
    try:
        response: ListResponse = list()
        return True
    except Exception as e:
        logger.error(f'Failed to ping Ollama server: {e}')
        return False

