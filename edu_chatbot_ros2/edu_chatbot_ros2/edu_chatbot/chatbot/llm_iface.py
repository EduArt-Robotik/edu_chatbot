from abc import ABC, abstractmethod


class LlmIface(ABC):
  """Abstract interface for LLM providers."""

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
  def ping(self) -> bool:
    """Test the connection to the LLM service.
    
    Returns:
        True if the connection is successful, False otherwise.
    """
    pass