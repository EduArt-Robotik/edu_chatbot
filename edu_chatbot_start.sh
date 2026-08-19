#!/bin/bash

# Detect GPU
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/docker"
source "$SCRIPT_DIR/detect_gpu.sh"
COMPOSE_FILE=$(get_compose_file)

# Start the main edu-chatbot-rag service in detached mode
docker compose $COMPOSE_FILE up --force-recreate edu-chatbot-rag -d