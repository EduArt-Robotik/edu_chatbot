#!/bin/bash

# Detect GPU
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/detect_gpu.sh"
COMPOSE_FILE=$(get_compose_file)

# Run the update services
docker compose $COMPOSE_FILE up --force-recreate edu-chatbot-llm-update
docker compose $COMPOSE_FILE up --force-recreate edu-chatbot-database-update

# Clean up containers and orphan networks
docker compose $COMPOSE_FILE down --remove-orphans edu-chatbot-llm-update
docker compose $COMPOSE_FILE down --remove-orphans edu-chatbot-database-update
docker compose $COMPOSE_FILE down --remove-orphans