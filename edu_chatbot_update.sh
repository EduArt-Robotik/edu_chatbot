#!/bin/bash

# Define compose files based on GPU detection
if lspci | grep -i "VGA\|3D\|Display" | grep -iq "NVIDIA"; then
  echo "NVIDIA GPU detected. Using NVIDIA docker-compose configuration."
  COMPOSE_FILES="-f docker-compose.yaml -f docker-compose.nvidia.yaml"
elif lspci | grep -i "VGA\|3D\|Display" | grep -iqE "AMD|ATI"; then
  echo "AMD GPU detected. Using AMD docker-compose configuration."
  COMPOSE_FILES="-f docker-compose.yaml -f docker-compose.amd.yaml"
else
  echo "No GPU detected. Using CPU fallback."
  COMPOSE_FILES=""
fi

# Run the update services
docker compose $COMPOSE_FILES up --force-recreate edu-chatbot-llm-update
docker compose $COMPOSE_FILES up --force-recreate edu-chatbot-database-update

# Clean up containers and orphan networks
docker compose $COMPOSE_FILES down --remove-orphans edu-chatbot-llm-update
docker compose $COMPOSE_FILES down --remove-orphans edu-chatbot-database-update
docker compose $COMPOSE_FILES down --remove-orphans