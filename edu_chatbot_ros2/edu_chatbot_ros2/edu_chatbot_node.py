import rclpy
from rclpy.node import Node
from std_msgs.msg import String

#from ollama import chat
#from ollama import ChatResponse
from ollama import generate
from ollama import GenerateResponse

import chromadb

from datetime import datetime

LLM_MODEL = 'gemma3:270m'
EMBEDDING_MODEL = 'nomic-embed-text'


def test_chromadb_client():
  print('===========================================================')
  print('Check ChromaDB server connection...')
  print('===========================================================\n')

  try:
    chroma_client = chromadb.Client()
    print(f'ChromaDB server heartbeat: {chroma_client.heartbeat()}')
    print('ChromaDB server connection successful.')

  except Exception as e:
    print(f'Failed to connect to ChromaDB client: {e}')

  print('\n===========================================================\n\n')

def test_ollama_chat():
  print('===========================================================')
  print('Check Ollama server connection...')
  print('===========================================================\n')
  query = 'Answer the following query briefly and concisely in 1 to 3 sentences: Why is the sky blue?'
  print(f'Query: {query}\n')
  
  try:
    query_ts = datetime.now()
    response: GenerateResponse = generate(model=LLM_MODEL, prompt=query)
    print(f'Got response in {(datetime.now() - query_ts).total_seconds()} seconds.')
    print(f'Response: {response.response}')

  except Exception as e:
    print(f'Failed to connect to Ollama server: {e}')

  print('\n===========================================================\n\n')
  

def main():
  test_chromadb_client()
  test_ollama_chat()


if __name__ == '__main__':
  main()
