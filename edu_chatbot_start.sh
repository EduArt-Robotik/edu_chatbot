#!/bin/bash

# Detect GPU
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/detect_gpu.sh"
COMPOSE_FILE=$(get_compose_file)

# Start the main edu-chatbot-node service in detached mode
docker compose $COMPOSE_FILE up --force-recreate edu-chatbot-node -d