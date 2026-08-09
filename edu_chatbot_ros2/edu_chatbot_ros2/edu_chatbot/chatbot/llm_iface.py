from abc import ABC, abstractmethod


class LlmIface(ABC):
  """Abstract interface for LLM providers."""
  def __init__(
    self,
    model: str = None,
    temperature: float = None
  ):
    self.model = model
    self.temperature = temperature

  @abstractmethod
  def ping(self) -> bool:
    """Test the connection to the LLM service.
    
    Returns:
        True if the connection is successful, False otherwise.
    """
    pass

  @abstractmethod
  def generate(self, prompt: str) -> str:
    """Generate a response for the given prompt.
    
    Args:
        prompt: The input prompt to send to the LLM.
        
    Returns:
        The generated response text.
    """
    pass

  @abstractmethod
  def embed(self, context: str) -> str:
    """Generate an embedding for the given context.
    
    Args:
        context: The input context to generate an embedding for.
        
    Returns:
        The generated embedding as a string.
    """
    pass