from .llm_iface import LlmIface
from ..database.database_iface import DatabaseIface

DEFAULT_MODEL_PERSONALITY   = 'You are a helpful and concise fair exhibition chatbot.'
DEFAULT_ANSWER_INSTRUCTIONS = 'Answer the following query concisely in 1 to 3 sentences providing accurate information. Provide a plain text answer.'
DEFAULT_RAG_INSTRUCTIONS    = 'Use the following context to answer the query. Answer with "I don\'t know" if the answer is not contained in the context.'


class RagAgent:
  def __init__(
    self,
    llm: LlmIface,
    database: DatabaseIface,
    model_personality: str = DEFAULT_MODEL_PERSONALITY,
    answer_instructions: str = DEFAULT_ANSWER_INSTRUCTIONS,
    rag_instructions: str = DEFAULT_RAG_INSTRUCTIONS
  ):
    self._llm = llm
    self._database = database
    self._model_personality = model_personality
    self._answer_instructions = answer_instructions
    self._rag_instructions = rag_instructions

  @property
  def model_personality(self) -> str:
    return self._model_personality

  @model_personality.setter
  def model_personality(self, value: str):
    self._model_personality = value

  @property
  def answer_instructions(self) -> str:
    return self._answer_instructions

  @answer_instructions.setter
  def answer_instructions(self, value: str):
    self._answer_instructions = value

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

  def ping(self) -> bool:
    """Test connections to both LLM and database services."""
    return self._llm.ping() and self._database.ping()

  def generate_prompt(self, query: str, context: str = None) -> str:
    if context:
      return f'{self._model_personality}\n{self._answer_instructions}\nQuery: {query}\n{self._rag_instructions}\nContext: {context}'
    else:
      return f'{self._model_personality}\n{self._answer_instructions}\nQuery: {query}'

  def query(self, query: str, context: str = None) -> str:
    """Generate a response for the given query using the LLM.
    
    Args:
        query: The user's query.
        context: Optional context for RAG.
        
    Returns:
        The generated response text.
    """
    prompt = self.generate_prompt(query=query, context=context)
    return self._llm.generate(prompt=prompt)
